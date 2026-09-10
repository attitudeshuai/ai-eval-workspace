#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抽取「提交字段规范」
====================
来源二选一，**默认走实时接口（永不过期）**：

  1) 平台表单定义接口（默认）
     GET https://solo2.jzxhnh.com/api/v1/submissions/form-schema
     返回 {fingerprint, groups, fields[24], teams, attachment_max_mb}
     需要 projects/cc-solo/secrets.toml 的 [submission].cookie；
     ⚠️ 该接口对请求头敏感：只带 Cookie 会 401，必须配齐浏览器那套头
        （Referer / Accept / Sec-Ch-Ua* / Sec-Fetch-* / 浏览器 UA），已复用
        submit_eval_result.browser_headers()。

  2) 本地前端快照（离线兜底）
     projects/cc-solo/docs/submission/submitfrom.js（含 var submitFields = {...}）

输出：projects/cc-solo/docs/submission/fields.json
      （fields / field_order / required_fields；upload_api 与 submit_api 会从
        快照或既有 fields.json 继承，接口本身不返回这两项）

用法：
    python scripts/cc-solo/extract_submit_fields.py                 # 默认：拉实时接口
    python scripts/cc-solo/extract_submit_fields.py --source js     # 用本地快照
    python scripts/cc-solo/extract_submit_fields.py --print         # 只打印，不写盘
    python scripts/cc-solo/extract_submit_fields.py --out <path>

退出码：0 成功；2 来源不可用（接口取不到且未指定 --source js）；3 返回结构无法解析
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")
DEFAULT_SRC = os.path.join(PROJECT_DIR, "docs", "submission", "submitfrom.js")
DEFAULT_OUT = os.path.join(PROJECT_DIR, "docs", "submission", "fields.json")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.toml")
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.toml")
DEFAULT_FORM_SCHEMA_URL = "https://solo2.jzxhnh.com/api/v1/submissions/form-schema"
DEFAULT_SUBMIT_URL = "https://solo2.jzxhnh.com/api/v1/submissions"

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None


# ------------------------------------------------------------------ 基础
def _load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_settings():
    cfg = _load_toml(CONFIG_PATH).get("submission", {}) or {}
    sec = _load_toml(SECRETS_PATH).get("submission", {}) or {}
    url = sec.get("form_schema_url") or cfg.get("form_schema_url") or DEFAULT_FORM_SCHEMA_URL
    cookie = sec.get("cookie") or sec.get("token") or ""
    submit_url = sec.get("submit_url") or cfg.get("submit_url") or DEFAULT_SUBMIT_URL
    return url, cookie, submit_url


def slice_object(text, anchor):
    """从 anchor 之后第一个 '{' 起做括号配对，返回该 JSON 对象字符串。"""
    start = text.index("{", text.index(anchor))
    depth, i, in_str, esc = 0, start, False, False
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    raise ValueError(f"未找到与 {anchor} 配对的 JSON 对象")


def deep_find(obj, key, depth=4):
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


def normalize_fields(raw_fields):
    """字段列表 → 统一精简结构（与既有 fields.json 保持一致）。"""
    fields = []
    for fld in raw_fields or []:
        if not isinstance(fld, dict):
            continue
        fields.append({
            "field_key": fld.get("field_key"),
            "label": fld.get("label"),
            "group": fld.get("group"),
            "field_type": fld.get("field_type"),
            "is_required": bool(fld.get("is_required")),
            "is_locked_on_fix": bool(fld.get("is_locked_on_fix")),
            "is_builtin": bool(fld.get("is_builtin", True)),
            "lark_field_name": fld.get("lark_field_name"),
            "placeholder": fld.get("placeholder", ""),
            "help_text": fld.get("help_text", ""),
            "max_length": fld.get("max_length", 0),
            "options": fld.get("options", []),
            "validation": fld.get("validation", {}) or {},
            "sort_order": fld.get("sort_order", 0),
        })
    fields.sort(key=lambda x: x["sort_order"])
    return fields


# ------------------------------------------------------------------ 来源 1：实时接口
def fetch_live(url, cookie, timeout=20):
    """拉平台表单定义接口，返回原始 dict。失败抛异常（调用方给提示）。"""
    if not cookie:
        raise RuntimeError("secrets.toml [submission].cookie 为空，无法请求实时接口")
    headers = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from submit_eval_result import browser_headers
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
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


# ------------------------------------------------------------------ 来源 2：本地快照
def parse_js(path):
    """解析 submitfrom.js，返回 (raw_fields_spec, upload_api)。"""
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    raw = json.loads(slice_object(text, "submitFields"))

    upload = {}
    if "upload_config" in text:
        block = slice_object(text, "upload_config")
        url_m = re.search(r'url:\s*"([^"]+)"', block)
        method_m = re.search(r'method:\s*"([^"]+)"', block)
        ct_m = re.search(r'content_type:\s*"([^"]+)"', block)
        upload = {
            "url": url_m.group(1) if url_m else None,
            "method": (method_m.group(1) if method_m else "POST"),
            "content_type": ct_m.group(1) if ct_m else "multipart/form-data",
            "form_field": "file",
            "response_path_key": "path",
            "auth": "cookie: solo_qa_session + solo_qa_csrf（放 secrets.toml [submission].cookie）",
        }
    return raw, upload


# ------------------------------------------------------------------ 组装
def build_spec(raw, source_label, upload_api, submit_url):
    fields = normalize_fields(raw.get("fields"))
    if not fields:
        raise ValueError("返回里没有可用的 fields")
    return {
        "schema": "cc-solo-submit-fields/v1",
        "source": source_label,
        "extracted_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "fingerprint": raw.get("fingerprint"),
        "attachment_max_mb": raw.get("attachment_max_mb"),
        "teams": raw.get("teams", []),
        "groups": raw.get("groups", []),
        "fields": fields,
        "field_order": [f["field_key"] for f in fields],
        "required_fields": [f["field_key"] for f in fields if f["is_required"]],
        "upload_api": upload_api or {},
        "submit_api": {
            "url": submit_url,
            "note": "提交接口：请求体 {\"data\": {24 字段}, \"schema_fingerprint\": …}，其中 trace_file 为附件数组；"
                    "选填字段一律置空字符串；敏感凭据放 projects/cc-solo/secrets.toml [submission].cookie（或 token）。",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["live", "js"], default="live",
                    help="live=拉平台实时接口（默认）；js=用本地 submitfrom.js 快照")
    ap.add_argument("--src", default=DEFAULT_SRC, help="--source js 时的快照路径")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--print", dest="dry", action="store_true", help="只打印，不写盘")
    args = ap.parse_args()

    form_url, cookie, submit_url = load_settings()

    # 既有 fields.json（用于继承接口不返回的 upload_api）
    existing = {}
    if os.path.exists(args.out):
        try:
            with open(args.out, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:  # noqa: BLE001
            existing = {}

    upload_api = None
    if args.source == "live":
        print(f"[来源] 平台实时接口：{form_url}")
        try:
            raw = fetch_live(form_url, cookie, timeout=args.timeout)
            source_label = form_url
        except urllib.error.HTTPError as e:
            hint = ("（凭据可能已过期：从浏览器重新复制整条 cookie 填进 secrets.toml [submission].cookie）"
                    if e.code in (401, 403) else "")
            print(f"[错误] 接口返回 HTTP {e.code}{hint}")
            print("        如需用本地快照兜底：加 --source js")
            sys.exit(2)
        except Exception as e:  # noqa: BLE001
            print(f"[错误] 接口取不到：{e}")
            print("        如需用本地快照兜底：加 --source js")
            sys.exit(2)
        # 接口不返回 upload_config，从快照或既有 fields.json 继承
        if os.path.exists(args.src):
            try:
                _, upload_api = parse_js(args.src)
            except Exception:  # noqa: BLE001
                upload_api = None
        upload_api = upload_api or existing.get("upload_api") or {}
    else:
        print(f"[来源] 本地快照：{os.path.relpath(args.src, WORKSPACE)}")
        if not os.path.exists(args.src):
            print(f"[错误] 找不到快照文件：{args.src}")
            sys.exit(2)
        raw, upload_api = parse_js(args.src)
        source_label = os.path.relpath(args.src, WORKSPACE).replace("\\", "/")

    try:
        spec = build_spec(raw, source_label, upload_api, submit_url)
    except ValueError as e:
        print(f"[错误] 返回结构无法解析：{e}")
        sys.exit(3)

    if not args.dry:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
            f.write("\n")

    old_fp = existing.get("fingerprint")
    print("=" * 60)
    if args.dry:
        print("（--print：未写盘）")
    else:
        print(f"字段规范已生成：{args.out}")
    print(f"来源：{spec['source']}")
    print(f"fingerprint：{spec['fingerprint']}"
          + (f"（改前 {old_fp}）" if old_fp and old_fp != spec["fingerprint"] else "（与改前一致）"))
    print(f"字段数：{len(spec['fields'])}（必填 {len(spec['required_fields'])}）"
          f"  附件上限 {spec['attachment_max_mb']} MB")
    for fld in spec["fields"]:
        opt = f"  options={fld['options']}" if fld["options"] else ""
        val = f"  validation={fld['validation']}" if fld["validation"] else ""
        print(f"  [{fld['sort_order']:>3}] {fld['field_key']:<18} {fld['label']:<14} "
              f"{fld['field_type']:<10}{' 必填' if fld['is_required'] else ''}{opt}{val}")
    print(f"轨迹上传接口：{(spec['upload_api'] or {}).get('url')}")
    print(f"提交接口：{spec['submit_api']['url']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
