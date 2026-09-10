#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 表单规范预检（防止平台表单改了、本地还按旧规范生成/提交）
================================================================
流程第一步（每次生成/提交前都先跑）：GET 平台的表单定义接口

    GET https://solo2.jzxhnh.com/api/v1/submissions/form-schema

把它返回的字段规范与本地 `projects/cc-solo/docs/submission/fields.json`
比对（fingerprint + 字段集合 + 每个字段的选项/必填），一致才继续。

退出码：
    0 = 一致
    3 = 不一致（平台表单变了：需重跑 extract_submit_fields.py 并重新生成评价结果）
    4 = 取不到（凭据过期 / 网络问题），本次无法判定

用法：
    python scripts/cc-solo/check_form_schema.py
    python scripts/cc-solo/check_form_schema.py --url <覆盖接口地址>
    python scripts/cc-solo/check_form_schema.py --json     # 只输出机器可读结果
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")
FIELDS_PATH = os.path.join(PROJECT_DIR, "docs", "submission", "fields.json")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.toml")
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.toml")

DEFAULT_URL = "https://solo2.jzxhnh.com/api/v1/submissions/form-schema"

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None


# ------------------------------------------------------------------ 配置
def _load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_settings():
    cfg = _load_toml(CONFIG_PATH)
    sec = _load_toml(SECRETS_PATH)
    sub_cfg = cfg.get("submission", {}) or {}
    sub_sec = sec.get("submission", {}) or {}
    url = sub_sec.get("form_schema_url") or sub_cfg.get("form_schema_url") or DEFAULT_URL
    cookie = sub_sec.get("cookie") or sub_sec.get("token") or ""
    return url, cookie, sub_cfg, sub_sec


# ------------------------------------------------------------------ 工具
def deep_find(obj, key, depth=4):
    """在嵌套 dict 里按广度优先找 key（最多 depth 层），找不到返回 None。"""
    if depth < 0 or not isinstance(obj, dict):
        return None
    if key in obj:
        return obj[key]
    for v in obj.values():
        if isinstance(v, dict):
            r = deep_find(v, key, depth - 1)
            if r is not None:
                return r
    return None


def normalize_fields(raw):
    """把接口返回的字段列表规整成 {field_key: {...}}；兼容 list / dict 两种形态。"""
    if raw is None:
        return None
    out = {}
    seq = raw if isinstance(raw, list) else list(raw.values()) if isinstance(raw, dict) else []
    for item in seq:
        if not isinstance(item, dict):
            continue
        k = item.get("field_key") or item.get("key") or item.get("name")
        if k:
            out[k] = item
    return out or None


def local_spec():
    with open(FIELDS_PATH, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ 主逻辑
def check_schema(url=None, cookie=None, timeout=20):
    """返回 dict：{ok: True/False/None, reason, local_fp, remote_fp, diffs, raw}"""
    if url is None or cookie is None:
        u, c, _, _ = load_settings()
        url = url or u
        cookie = cookie if cookie is not None else c

    local = local_spec()
    result = {
        "url": url,
        "ok": None,
        "reason": "",
        "local_fp": local.get("fingerprint"),
        "remote_fp": None,
        "diffs": [],
        "raw": None,
    }

    if not cookie:
        result["reason"] = "secrets.toml [submission].cookie 为空，无法请求"
        return result

    # 该接口对请求头敏感：只带 Cookie 会 401，必须配齐浏览器那套头
    # （Referer / Accept / Sec-Ch-Ua / Sec-Fetch-* / 浏览器 UA），与 submit_eval_result.py 保持一致
    headers = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from submit_eval_result import browser_headers  # noqa: E402
        headers = browser_headers(url, cookie, fetch_site="same-origin")
    except Exception:  # noqa: BLE001
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://solo2.jzxhnh.com/app/submit",
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0"),
            "Cookie": cookie,
        }

    req = urllib.request.Request(url, method="GET")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        result["reason"] = (f"HTTP {e.code}：凭据可能已过期（cookie 会过期，"
                            f"从浏览器重新复制整条串填进 secrets.toml [submission].cookie）"
                            if e.code in (401, 403) else f"HTTP {e.code}")
        return result
    except Exception as e:  # noqa: BLE001
        result["reason"] = f"请求失败：{e}"
        return result

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        result["raw"] = body[:2000]
        result["reason"] = "返回不是 JSON（见 raw）"
        return result

    result["raw"] = payload
    remote_fp = deep_find(payload, "fingerprint")
    remote_fields_raw = deep_find(payload, "fields")
    result["remote_fp"] = remote_fp
    remote_fields = normalize_fields(remote_fields_raw)

    if remote_fp is None and remote_fields is None:
        result["reason"] = "返回里没找到 fingerprint 也没找到 fields，需按实际返回结构适配本脚本"
        return result

    diffs = []
    if remote_fp and result["local_fp"] and remote_fp != result["local_fp"]:
        diffs.append(f"fingerprint 不一致：本地 {result['local_fp']} / 平台 {remote_fp}")

    if remote_fields:
        lk, rk = set(local.get("fields_by_key") or {f["field_key"] for f in local["fields"]}), set(remote_fields)
        for k in sorted(rk - lk):
            diffs.append(f"平台新增字段：{k}")
        for k in sorted(lk - rk):
            diffs.append(f"平台已无此字段（本地多出）：{k}")
        lmap = {f["field_key"]: f for f in local["fields"]}
        for k in sorted(lk & rk):
            lf, rf = lmap[k], remote_fields[k]
            lo, ro = lf.get("options") or [], rf.get("options") or []
            if set(lo) != set(ro):
                diffs.append(f"字段 {k} 选项不一致：本地 {len(lo)} 项 / 平台 {len(ro)} 项")
            if bool(lf.get("is_required")) != bool(rf.get("is_required", lf.get("is_required"))):
                diffs.append(f"字段 {k} 必填性不一致：本地 {lf.get('is_required')} / 平台 {rf.get('is_required')}")

    result["diffs"] = diffs
    result["ok"] = not diffs
    if not result["reason"]:
        result["reason"] = "一致" if not diffs else f"发现 {len(diffs)} 处差异"
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="表单定义接口 URL（默认取 config/secrets，否则内置默认值）")
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--json", action="store_true", help="只输出机器可读 JSON")
    args = ap.parse_args()

    res = check_schema(url=args.url, timeout=args.timeout)

    if args.json:
        slim = {k: v for k, v in res.items() if k != "raw"}
        print(json.dumps(slim, ensure_ascii=False, indent=2))
    else:
        print("=" * 64)
        print(f"表单规范预检：{res['url']}")
        print(f"本地 fingerprint：{res['local_fp']}")
        print(f"平台 fingerprint：{res['remote_fp']}")
        if res["ok"] is True:
            print("结果：✅ 一致，平台表单没变，可以继续生成/提交")
        elif res["ok"] is False:
            print(f"结果：⚠️ 不一致（{len(res['diffs'])} 处）")
            for d in res["diffs"]:
                print(f"    - {d}")
            print("处理：重跑 python scripts/cc-solo/extract_submit_fields.py，再重新生成评价结果")
        else:
            print(f"结果：❓ 无法判定：{res['reason']}")
            if res.get("raw"):
                print(f"    返回片段：{str(res['raw'])[:400]}")
        print("=" * 64)

    if res["ok"] is True:
        return 0
    return 3 if res["ok"] is False else 4


if __name__ == "__main__":
    sys.exit(main())
