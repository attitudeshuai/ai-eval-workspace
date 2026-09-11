#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 评价结果提交（轨迹上传 + 提交接口；cookie 过期自动重新登录）
====================================================================
读取 build_eval_result.py 产出的评价结果 JSON，按「一轮 = 一条记录」提交：

 1. 轨迹文件是**附件**：先上传拿远端 path（multipart/form-data，表单字段 file）
 2. 再提交到 https://solo2.jzxhnh.com/api/v1/submissions，请求体：

    {
      "data": { 全部字段都在（保持 24 字段结构）；但**选填字段一律置空字符串**
                （fields.json 里 is_required=false 的，本期为 other_issues 其他问题）；
                "trace_file": [{"name": "…-trajectory.jsonl", "path": "uploads/<id>.jsonl", "size": 321940}] },
      "schema_fingerprint": "cc4da53236368ac2"
    }

    响应：{"id":1196,"status":"SUBMITTED","status_label":"已提交","round_no":1,
           "schema_stale":false,"message":"提交成功，正在自动质检，稍后可在列表查看结论"}

登录与 cookie（会过期，脚本自动续）
----------------------------------
服务端下发的 `solo_qa_session` / `solo_qa_csrf` 有效期约 2 天。脚本：
  · 启动时若 secrets.toml [submission] 没 cookie（或加了 --refresh-cookie）→ 先登录；
  · 请求过程中遇到 401/403（cookie 过期 / 失效）→ 自动登录一次并重试原请求；
  · 登录接口：POST {login_url}（默认 https://solo2.jzxhnh.com/api/v1/auth/login），
    请求体 {"username": <secrets.toml [submission].username>, "password": <…>.password}；
  · 从响应的 Set-Cookie（或响应体里的 csrf/session 字段）取新 cookie，**连同到期时间**存进
    `projects/cc-solo/.solo_session.json`（gitignore），同时回写 `secrets.toml`；
  · 之后每次运行**优先复用缓存里的 cookie —— 没过期就不会再登录**；只有「缓存缺失 / 已过期 /
    请求返回 401、403」时才重新登录一次。`--status` 看当前来源与剩余有效期，`--refresh-cookie`
    强制续期，`--no-cache` 只用 secrets.toml。

用法：
    # 看一眼会提交什么（默认 dry-run，不联网）
    python scripts/cc-solo/submit_eval_result.py --result <评价结果.json>
    python scripts/cc-solo/submit_eval_result.py --result <json> --show-payload    # 打印完整请求体

    # 刷新 cookie（登录一次并写回 secrets.toml），不处理任何记录
    python scripts/cc-solo/submit_eval_result.py --login-only --commit

    # 只上传轨迹并回填远端 path（不提交）
    python scripts/cc-solo/submit_eval_result.py --result <json> --upload-only --commit --write-back

    # 正式提交
    python scripts/cc-solo/submit_eval_result.py --result <json> --commit
    python scripts/cc-solo/submit_eval_result.py --result <json> --record app-001-codegen-01#R01 --commit

配置（projects/cc-solo/secrets.toml，gitignore）：
    [submission]
    submit_url = "https://solo2.jzxhnh.com/api/v1/submissions"   # 缺省取 config.toml [submission]
    cookie = "solo_qa_session=...; solo_qa_csrf=..."             # 也可写 token = "..."（二者等价）；会被脚本自动刷新
    username = "…"                                               # 平台账号（cookie 过期时自动登录用）
    password = "…"                                               # 平台密码（敏感，勿外传）
    csrf_header = ""                                             # 留空则自动取 cookie 里的 solo_qa_csrf
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.toml")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.toml")

DEFAULT_LOGIN_URL = "https://solo2.jzxhnh.com/api/v1/auth/login"

# 会话缓存：登录一次就把 cookie + 到期时间存这里；**未过期就直接复用，不再登录**
SESSION_CACHE_PATH = os.path.join(PROJECT_DIR, ".solo_session.json")
EXPIRY_MARGIN_SEC = 60          # 剩余不足 60 秒按过期处理，提前续期


def _now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def read_session_cache():
    try:
        with open(SESSION_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_session_cache(cookie, csrf, expires_at=None, source="login"):
    """把当前 cookie（含到期时间）落盘，供下次直接复用。"""
    if not cookie:
        return
    obj = {
        "cookie": cookie,
        "csrf": csrf or "",
        "obtained_at": _now_iso(),
        "expires_at": expires_at or "",
        "source": source,
    }
    try:
        with open(SESSION_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError:
        pass


def expiry_state(expires_at):
    """→ (是否仍有效, 人类可读剩余时间)；expires_at 为空时返回 (None, "无到期信息")。"""
    if not expires_at:
        return None, "无到期信息"
    try:
        exp = datetime.datetime.fromisoformat(expires_at)
    except ValueError:
        return None, "无法解析"
    if exp.tzinfo is None:
        exp = exp.astimezone()
    left = (exp - datetime.datetime.now().astimezone()).total_seconds()
    if left <= 0:
        return False, "已过期"
    if left <= EXPIRY_MARGIN_SEC:
        return False, f"仅剩 {int(left)}s"
    h, m = divmod(int(left // 60), 60)
    return True, f"剩余 {h}h{m:02d}m"

# 登录响应体里可能出现的 csrf / session 字段名（大小写不敏感）
CSRF_KEYS = ("csrf_token", "csrftoken", "csrf", "solo_qa_csrf")
SESSION_KEYS = ("session", "session_id", "sessionid", "solo_qa_session", "token")

try:
    import tomllib
except ImportError:
    tomllib = None


def load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_settings():
    cfg = load_toml(CONFIG_PATH).get("submission", {})
    sec = load_toml(SECRETS_PATH).get("submission", {})
    return cfg, sec


def mask(v, keep=6):
    v = str(v or "")
    return (v[:keep] + "…" + v[-2:]) if len(v) > keep + 3 else "…"


# ---------------------------------------------------------------- 网络
# 该平台对请求头敏感：只带 Cookie 会被 401，必须配齐浏览器那套头（Referer/Accept/Sec-* 等）
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0")


def origin_of(url):
    from urllib.parse import urlparse
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else "https://solo2.jzxhnh.com"


def browser_headers(url, cookie=None, csrf=None, accept="application/json, text/plain, */*",
                     fetch_site="same-origin", referer_path="/app/submit"):
    """浏览器同类请求的请求头集合（照浏览器抓包配上，避免 401）。"""
    h = {
        "Accept": accept,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": BROWSER_UA,
        "Referer": origin_of(url) + referer_path,
        "Sec-Ch-Ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": fetch_site,
    }
    if cookie:
        h["Cookie"] = cookie
    if csrf:
        # 两个头名都发，覆盖 Django 默认（X-CSRFToken）与带连字符写法（X-CSRF-Token）
        h["X-CSRF-Token"] = csrf
        h["X-CSRFToken"] = csrf
    return h


def post_multipart(url, cookie, file_path, form_field="file", timeout=180, csrf=None):
    """上传文件：multipart/form-data，返回解析后的 JSON（形如 {"name":…,"path":…,"size":…}）。"""
    boundary = "----ccsolo" + uuid.uuid4().hex
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        content = f.read()
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="{form_field}"; filename="{filename}"\r\n'.encode(),
        b"Content-Type: application/octet-stream\r\n\r\n",
        content,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in browser_headers(url, cookie, csrf=csrf).items():
        req.add_header(k, v)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Origin", origin_of(url))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
    return json.loads(raw), resp


def post_json(url, cookie, payload, csrf_header=None, timeout=120, referer_path="/app/submit"):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in browser_headers(url, cookie, csrf=csrf_header, referer_path=referer_path).items():
        req.add_header(k, v)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Origin", origin_of(url))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
    try:
        return json.loads(raw), resp
    except json.JSONDecodeError:
        return {"_raw": raw}, resp


def _set_cookies_from(resp):
    """从响应里吸收 Set-Cookie（返回 {name: value}）。"""
    out = {}
    try:
        vals = resp.headers.get_all("Set-Cookie") or []
    except AttributeError:
        one = resp.headers.get("Set-Cookie")
        vals = [one] if one else []
    for sc in vals:
        nv = sc.split(";", 1)[0].strip()
        if "=" in nv:
            k, v = nv.split("=", 1)
            if k.strip() and v.strip():
                out[k.strip()] = v.strip()
    return out


def _expiry_from(resp):
    """从响应的 Set-Cookie 里解析最早到期时间（Expires / Max-Age），返回 ISO 串或 None。"""
    from email.utils import parsedate_to_datetime
    try:
        vals = resp.headers.get_all("Set-Cookie") or []
    except AttributeError:
        one = resp.headers.get("Set-Cookie")
        vals = [one] if one else []
    earliest = None
    for sc in vals:
        for part in sc.split(";")[1:]:
            p = part.strip()
            low = p.lower()
            try:
                if low.startswith("max-age="):
                    t = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                        seconds=int(p.split("=", 1)[1]))
                elif low.startswith("expires="):
                    t = parsedate_to_datetime(p.split("=", 1)[1]).astimezone(datetime.timezone.utc)
                else:
                    continue
            except (ValueError, TypeError, IndexError):
                continue
            earliest = t if earliest is None or t < earliest else earliest
    return earliest.astimezone().isoformat(timespec="seconds") if earliest else None


def _deep_find_tokens(obj, depth=0):
    """登录响应体里可能带 csrf / session 字段。"""
    found = {}
    if depth > 3 or not isinstance(obj, dict):
        return found
    for k, v in obj.items():
        kl = str(k).lower()
        if isinstance(v, str) and v:
            if kl in [x.lower() for x in CSRF_KEYS]:
                found.setdefault("solo_qa_csrf", v)
            elif kl in [x.lower() for x in SESSION_KEYS]:
                found.setdefault("solo_qa_session", v)
        elif isinstance(v, dict):
            for kk, vv in _deep_find_tokens(v, depth + 1).items():
                found.setdefault(kk, vv)
    return found


# ---------------------------------------------------------------- 会话（cookie + 自动登录）
class Session:
    """持有 cookie/csrf；401/403 时自动登录刷新，并把新 cookie 写回 secrets.toml。"""

    def __init__(self, cfg, sec, auto_login=True, persist=True, verbose=True, no_cache=False):
        self.cfg, self.sec = cfg, dict(sec)
        self.login_url = sec.get("login_url") or cfg.get("login_url") or DEFAULT_LOGIN_URL
        self.username = sec.get("username") or ""
        self.password = sec.get("password") or ""
        self.auto_login = auto_login
        self.persist = persist
        self.verbose = verbose
        self.no_cache = no_cache
        self.logins = 0
        self.needs_login = False

        # 取用顺序：会话缓存（未过期）→ secrets.toml（若比缓存新，视为人工改过）→ 都没有才登录
        cache = {} if no_cache else read_session_cache()
        self.cache = cache
        self.expires_at = cache.get("expires_at") or ""
        sec_cookie = sec.get("cookie") or sec.get("token") or ""
        cache_cookie = cache.get("cookie") or ""
        fresh, left = expiry_state(self.expires_at)
        secrets_newer = False
        if sec_cookie and cache_cookie and sec_cookie != cache_cookie:
            try:
                secrets_newer = os.path.getmtime(SECRETS_PATH) > os.path.getmtime(SESSION_CACHE_PATH)
            except OSError:
                secrets_newer = False

        if cache_cookie and fresh is True and not secrets_newer:
            self.cookie, self.source = cache_cookie, f"会话缓存（{left}）"
        elif sec_cookie:
            self.cookie = sec_cookie
            self.source = "secrets.toml" + ("（比缓存新）" if secrets_newer else "")
        elif cache_cookie:
            self.cookie, self.source = cache_cookie, f"会话缓存（{left}）"
            self.needs_login = True              # 缓存已过期 → 需要重新登录
        else:
            self.cookie, self.source = "", "无"
            self.needs_login = True

        self.csrf = self._csrf_of(sec) or cache.get("csrf") or ""
        self.cookie_names = self._names(self.cookie)

    # ---- 小工具 ----
    @staticmethod
    def _names(cookie):
        return {p.split("=", 1)[0].strip() for p in str(cookie).split(";") if "=" in p}

    def _csrf_of(self, sec=None):
        explicit = (sec or self.sec).get("csrf_header") or ""
        if explicit:
            return explicit
        m = re.search(r"solo_qa_csrf=([^;]+)", self.cookie or "")
        return m.group(1).strip() if m else ""

    def summary(self):
        names = self._names(self.cookie)
        if not self.cookie:
            return "【无 cookie】"
        parts = []
        for p in str(self.cookie).split(";"):
            if "=" in p:
                k, v = p.split("=", 1)
                parts.append(f"{k.strip()}={mask(v.strip())}")
        return "；".join(parts) + (f"（csrf={'已带' if self.csrf else '缺失'}）")

    # ---- 登录 ----
    def login(self, why=""):
        if not self.username or not self.password:
            raise RuntimeError("cookie 已失效，但 secrets.toml [submission] 没有 username / password，无法自动登录")
        if self.verbose:
            print(f"    → 自动登录（{why or '手动'}）：POST {self.login_url}  user={self.username}")
        body = json.dumps({"username": self.username, "password": self.password},
                          ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.login_url, data=body, method="POST")
        for k, v in browser_headers(self.login_url, self.cookie or None, csrf=self.csrf or None,
                                    referer_path="/login").items():
            req.add_header(k, v)
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.add_header("Origin", origin_of(self.login_url))
        exp = None
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", "replace")
                new = _set_cookies_from(resp)
                exp = _expiry_from(resp)
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            raise RuntimeError(f"登录失败 HTTP {e.code}：{detail}")

        obj = None
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            pass
        if isinstance(obj, dict):
            for k, v in _deep_find_tokens(obj).items():
                new.setdefault(k, v)

        if not new:
            raise RuntimeError(f"登录成功但响应里没拿到 cookie/字段：{raw[:200]}")

        # 合并进现有 cookie 串（保留登录没返回的其它 cookie）
        merged = {}
        for p in str(self.cookie or "").split(";"):
            if "=" in p:
                k, v = p.split("=", 1)
                merged[k.strip()] = v.strip()
        merged.update(new)
        self.cookie = "; ".join(f"{k}={v}" for k, v in merged.items())
        self.csrf = re.search(r"solo_qa_csrf=([^;]+)", self.cookie).group(1).strip() \
            if "solo_qa_csrf" in merged else self._csrf_of()
        self.cookie_names = self._names(self.cookie)
        self.logins += 1
        if self.verbose:
            print(f"    ← 登录成功，新 cookie：{self.summary()}")
            if isinstance(obj, dict):
                # 只打字段名，避免把 token/session 值打进日志
                print(f"      响应字段：{', '.join(list(obj.keys())[:8])}")
        self.expires_at = exp or self.expires_at
        write_session_cache(self.cookie, self.csrf, self.expires_at, source="login")
        self.persist_cookies()
        return self.cookie

    def persist_cookies(self):
        """把当前 cookie 写回 secrets.toml [submission] 的 cookie 行（就地替换，不动其它内容）。"""
        if not self.persist or not self.cookie:
            return False
        try:
            with open(SECRETS_PATH, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            if self.verbose:
                print(f"    [提示] 找不到 {SECRETS_PATH}，跳过 cookie 回写")
            return False
        in_sec, done = False, False
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("["):
                in_sec = (s == "[submission]")
                continue
            if in_sec and (s.startswith("cookie") or s.startswith("token")):
                lines[i] = f'cookie = "{self.cookie}"'
                done = True
                break
        if not done:
            for i, line in enumerate(lines):
                if line.strip() == "[submission]":
                    lines.insert(i + 1, f'cookie = "{self.cookie}"')
                    done = True
                    break
        if not done:
            lines += ["", "[submission]", f'cookie = "{self.cookie}"']
        with open(SECRETS_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        if self.verbose:
            print(f"      已把新 cookie 写回 {os.path.relpath(SECRETS_PATH, WORKSPACE)}")
        return True

    # ---- 带自动续期的请求 ----
    def _with_relogin(self, fn, what):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            if e.code not in (401, 403) or not self.auto_login:
                raise
            if self.verbose:
                print(f"    HTTP {e.code}（{what}：cookie 可能已过期），登录后重试一次…")
            self.login(why=f"HTTP {e.code}")
            return fn()
        except RuntimeError:
            raise

    def upload(self, url, file_path, form_field="file"):
        def call():
            obj, resp = post_multipart(url, self.cookie, file_path, form_field=form_field, csrf=self.csrf or None)
            new = _set_cookies_from(resp)
            if new:
                merged = dict(p.split("=", 1) for p in self.cookie.split(";") if "=" in p)
                merged.update(new)
                self.cookie = "; ".join(f"{k.strip()}={v.strip()}" for k, v in merged.items())
                self.csrf = self._csrf_of()
                self.expires_at = _expiry_from(resp) or self.expires_at
                write_session_cache(self.cookie, self.csrf, self.expires_at, source="request")
                self.persist_cookies()
            return obj
        return self._with_relogin(call, "上传轨迹")

    def submit(self, url, payload):
        def call():
            obj, resp = post_json(url, self.cookie, payload, csrf_header=self.csrf or None)
            new = _set_cookies_from(resp)
            if new:
                merged = dict(p.split("=", 1) for p in self.cookie.split(";") if "=" in p)
                merged.update(new)
                self.cookie = "; ".join(f"{k.strip()}={v.strip()}" for k, v in merged.items())
                self.csrf = self._csrf_of()
                self.expires_at = _expiry_from(resp) or self.expires_at
                write_session_cache(self.cookie, self.csrf, self.expires_at, source="request")
                self.persist_cookies()
            return obj
        return self._with_relogin(call, "提交")


def build_payload(record, field_order, fingerprint, blank_keys=None):
    """一条记录 → 提交请求体：{"data": {24 字段}, "schema_fingerprint": …}。

    选填字段（fields.json 里 is_required=false，本期为 other_issues）**字段保留、值置空字符串**：
    不把内容提交出去，同时保持 body 的字段结构完整。

    trace_file 为附件数组 [{name,path,size}]，由上传步骤回填；未上传时为空数组。
    """
    blank = set(blank_keys or ())
    data = {k: ("" if k in blank else record["fields"].get(k, "")) for k in field_order}
    tf = record["fields"].get("trace_file")
    data["trace_file"] = tf if isinstance(tf, list) else []
    return {"data": data, "schema_fingerprint": fingerprint}


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", help="评价结果 JSON（build_eval_result.py 产物）；--login-only 时可不给")
    ap.add_argument("--url", help="提交接口 URL（覆盖 config/secrets 的 submit_url）")
    ap.add_argument("--cookie", help="整条凭据串（覆盖 secrets.toml [submission].cookie）")
    ap.add_argument("--record", action="append", help="只处理指定 record_key（可多次），如 app-001-codegen-01#R01")
    ap.add_argument("--only-ready", action="store_true", help="只提交 ready=true 的记录（跳过有 error 的）")
    ap.add_argument("--upload-only", action="store_true", help="只上传轨迹、回填附件信息，不提交")
    ap.add_argument("--login-only", action="store_true", help="只登录刷新 cookie，不处理记录")
    ap.add_argument("--refresh-cookie", action="store_true", help="处理前先强制登录一次")
    ap.add_argument("--no-auto-login", action="store_true", help="禁止自动登录（401/403 直接报错）")
    ap.add_argument("--no-cache", action="store_true", help="不用/不写会话缓存（只读 secrets.toml）")
    ap.add_argument("--status", action="store_true", help="只看 cookie 来源与剩余有效期，不发请求")
    ap.add_argument("--commit", action="store_true", help="真的发请求；不加则只打印计划（dry-run）")
    ap.add_argument("--interval", type=float, default=5.0,
                    help="逐条提交时每条之间的等待秒数（接口不支持批量，默认 5）")
    ap.add_argument("--show-payload", action="store_true", help="打印完整请求体（含 desc 全文）")
    ap.add_argument("--write-back", action="store_true", help="把上传结果/接口返回回写到结果 JSON")
    args = ap.parse_args()

    if not args.result and not args.login_only and not args.status:
        ap.error("必须提供 --result（或用 --login-only / --status）")

    data = None
    if args.result:
        with open(args.result, encoding="utf-8") as f:
            data = json.load(f)
    data = data or {}

    cfg_sec, sec = load_settings()
    if args.cookie:
        sec = dict(sec)
        sec["cookie"] = args.cookie

    upload_api = data.get("upload_api", {}) or {}
    upload_url = sec.get("upload_url") or cfg_sec.get("upload_url") or upload_api.get("url")
    form_field = cfg_sec.get("upload_form_field") or upload_api.get("form_field", "file")
    path_key = cfg_sec.get("upload_response_path_key") or upload_api.get("response_path_key", "path")
    submit_url = args.url or sec.get("submit_url") or cfg_sec.get("submit_url") or (data.get("submit_api") or {}).get("url")
    fingerprint = data.get("field_spec_fingerprint") or (data.get("submit_api") or {}).get("schema_fingerprint")
    max_mb = float(cfg_sec.get("attachment_max_mb") or 20)

    session = Session(cfg_sec, sec, auto_login=not args.no_auto_login, persist=True, verbose=True,
                      no_cache=args.no_cache)

    records = data.get("records", []) or []
    if args.record:
        want = set(args.record)
        records = [r for r in records if r["record_key"] in want]
    if args.only_ready:
        records = [r for r in records if r.get("ready")]

    print("=" * 64)
    if args.result:
        print(f"评价结果：{args.result}")
        print(f"会话：{data.get('session')}｜待处理记录：{len(records)}")
    print(f"轨迹上传接口：{upload_url or '【未配置】'}（表单字段 {form_field}，取返回 {path_key}）")
    print(f"提交接口：{submit_url or '【未配置】'}")
    print(f"登录接口：{session.login_url}（账号 {session.username or '【未配置 username】'}）")
    print(f"schema_fingerprint：{fingerprint or '（本次无需）'}")
    print(f"cookie：{session.summary()}")
    _fresh, _left = expiry_state(session.expires_at)
    print(f"cookie 来源：{session.source}"
          + (f"｜到期 {session.expires_at}（{_left}）" if session.expires_at else "｜无到期信息"))
    print(f"自动登录：{'关闭' if args.no_auto_login else '开启（仅在没有可用 cookie 或 401/403 时登录一次）'}"
          + f"｜本次启动{'需要' if session.needs_login else '不需要'}登录")
    print(f"模式：{'正式执行（--commit）' if args.commit else 'DRY-RUN（只打印计划，不发请求）'}")
    if records:
        print(f"提交方式：逐条提交（接口不支持批量），每条间隔 {args.interval:.0f}s")
    print("-" * 64)

    if args.status:
        print("-" * 64)
        print(f"会话缓存：{os.path.relpath(SESSION_CACHE_PATH, WORKSPACE)}"
              f"{'（--no-cache，本次不读）' if args.no_cache else ''}")
        print(f"  obtained_at={session.cache.get('obtained_at') or '—'}"
              f"｜expires_at={session.expires_at or '—'}｜{_left}")
        print(f"  secrets.toml 里的 cookie：{'有' if (sec.get('cookie') or sec.get('token')) else '无'}")
        print(f"  结论：{'可直接复用，无需登录' if not session.needs_login else '需要登录刷新'}")
        return

    # ---------------- dry-run ----------------
    if not args.commit:
        if args.login_only or args.refresh_cookie or session.needs_login:
            print("[dry-run] 会先登录刷新 cookie（加 --commit 才真的发请求，并写回缓存 + secrets.toml）")
        else:
            print("[dry-run] 复用已保存的 cookie，本次不会登录")
        if args.login_only:
            return
        for r in records:
            tag = r["record_key"]
            local = r.get("trace_file_local")
            abs_local = os.path.join(WORKSPACE, local) if local else None
            size = os.path.getsize(abs_local) if abs_local and os.path.exists(abs_local) else 0
            size_mb = size / 1024 / 1024
            blockers = [i for i in r.get("issues", []) if i["level"] == "error"]
            print(f"· {tag}  轨迹={local} ({size_mb:.2f} MB{'  ⚠️超上限' if size_mb > max_mb else ''})")
            if blockers:
                print(f"    阻塞项：{'；'.join(i['message'] for i in blockers)}")
            if args.show_payload:
                print("    请求体：")
                print(json.dumps(build_payload(r, data.get("field_order") or [], fingerprint,
                                               data.get("blank_optional_fields")), ensure_ascii=False, indent=2))
            else:
                preview = json.dumps(build_payload(r, data.get("field_order") or [], fingerprint,
                                                   data.get("blank_optional_fields")), ensure_ascii=False)
                print(f"    请求体（截断）：{preview[:300]}…")
        print("=" * 64)
        print("这是 dry-run：没有发任何请求。确认无误后加 --commit。")
        return

    # ---------------- 真执行 ----------------
    try:
        if args.login_only or args.refresh_cookie or session.needs_login:
            session.login(why="强制刷新" if (args.login_only or args.refresh_cookie)
                          else "没有可用的 cookie / 缓存")
        if args.login_only:
            print("=" * 64)
            print("已刷新 cookie 并写回 secrets.toml。")
            return
    except RuntimeError as e:
        print(f"[错误] {e}")
        sys.exit(3)

    # 正式提交前：先请求平台表单定义接口，确认字段规范没过期（变了就不提交）
    if args.commit:
        sc = None
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from check_form_schema import check_schema
            sc = check_schema(cookie=session.cookie)
        except Exception as e:  # noqa: BLE001
            print(f"[提示] 表单规范预检跳过：{e}")
        if sc:
            if sc["ok"] is True:
                print(f"[表单规范] fingerprint={sc['local_fp']}，与平台一致 ✅")
            elif sc["ok"] is False:
                print(f"[中止] 平台表单已变：本地 {sc['local_fp']} / 平台 {sc['remote_fp']}")
                for d in sc["diffs"]:
                    print(f"        - {d}")
                print("        未发送任何提交请求。请重跑 extract_submit_fields.py 后重新生成评价结果。")
                sys.exit(3)
            else:
                print(f"[提示] 表单规范预检未完成（{sc['reason']}），继续按本地规范提交，请自行留意 schema_stale")
        print("-" * 64)

    field_order = data.get("field_order") or (list(records[0]["fields"].keys()) if records else [])
    # 选填字段一律置空字符串：字段保留在 body 里，但不提交内容
    blank_keys = set(data.get("blank_optional_fields") or (data.get("excluded_optional_fields") or []))
    if blank_keys:
        print(f"选填字段置空（字段保留、内容不提交）：{'、'.join(sorted(blank_keys))}")
    else:
        print("[提示] 结果文件里没有 blank_optional_fields，选填字段将按原值提交")
    changed = False
    submitted = 0

    for r in records:
        # 接口不支持批量：逐条提交，每条之间留间隔（第一条不等待）
        if submitted > 0:
            print(f"· 等待 {args.interval:.0f}s 后提交下一条（接口不支持批量）…")
            time.sleep(args.interval)
        tag = r["record_key"]
        local = r.get("trace_file_local")
        abs_local = os.path.join(WORKSPACE, local) if local else None
        size = os.path.getsize(abs_local) if abs_local and os.path.exists(abs_local) else 0
        size_mb = size / 1024 / 1024
        blockers = [i for i in r.get("issues", []) if i["level"] == "error"]
        print(f"· {tag}  轨迹={local} ({size_mb:.2f} MB{'  ⚠️超上限' if size_mb > max_mb else ''})")
        if blockers:
            print(f"    阻塞项：{'；'.join(i['message'] for i in blockers)}")

        if not abs_local or not os.path.exists(abs_local):
            print("    [跳过] 轨迹文件不存在")
            continue
        if not upload_url:
            print("    [跳过] 上传接口 URL 未配置")
            continue
        # 已上传过（fields.trace_file 已是附件数组且带远端 path）就不重复传；
        # 注意：结果文件里未提交时 trace_file 可能是本机路径字符串，那种情况仍要上传
        tf = r["fields"].get("trace_file")
        already = isinstance(tf, list) and bool(tf) and bool(tf[0].get("path"))
        if not already:
            try:
                up = session.upload(upload_url, abs_local, form_field=form_field)
                remote = up.get(path_key) or (up.get("data") or {}).get(path_key)
                if not remote:
                    print(f"    [失败] 上传返回里没找到 {path_key}：{up}")
                    continue
                att = {"name": up.get("name") or os.path.basename(abs_local),
                       "path": remote, "size": int(up.get("size") or size)}
                r["trace_file_uploaded"] = remote
                r["fields"]["trace_file"] = [att]
                changed = True
                print(f"    上传成功 → {remote}（{att['size']} bytes）")
            except urllib.error.HTTPError as e:
                print(f"    [失败] 上传 HTTP {e.code}：{e.read()[:200]!r}")
                continue
            except Exception as e:  # noqa: BLE001
                print(f"    [失败] 上传异常：{e}")
                continue
        else:
            print(f"    轨迹已上传：{r['trace_file_uploaded']}")

        if args.upload_only:
            continue
        if not submit_url:
            print("    [跳过提交] 提交接口 URL 未配置（轨迹已上传）")
            continue
        payload = build_payload(r, field_order, fingerprint, blank_keys)
        submitted += 1
        try:
            resp = session.submit(submit_url, payload)
        except urllib.error.HTTPError as e:
            print(f"    [失败] 提交 HTTP {e.code}：{e.read()[:300]!r}")
            continue
        except Exception as e:  # noqa: BLE001
            print(f"    [失败] 提交异常：{e}")
            continue

        status = str(resp.get("status", "")).upper()
        ok = status == "SUBMITTED" or bool(resp.get("id"))
        r["submit_response"] = resp
        changed = True
        print(f"    {'提交成功' if ok else '提交返回异常'} → id={resp.get('id')} status={resp.get('status')}"
              f" round_no={resp.get('round_no')}")
        if resp.get("message"):
            print(f"    平台消息：{resp['message']}")
        if resp.get("schema_stale"):
            print("    ⚠️ schema_stale=true：表单字段规范已变，请重跑 extract_submit_fields.py 后重新生成并提交")

    if args.write_back and changed and args.result:
        with open(args.result, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"- 已回写上传结果/接口返回到：{args.result}")

    print("=" * 64)
    if session.logins:
        print(f"本次自动登录 {session.logins} 次；新 cookie 已写入会话缓存与 secrets.toml"
              f"（下次直接复用，过期才再登录）")


if __name__ == "__main__":
    main()
