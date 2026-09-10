#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从浏览器表单定义里抽取「提交字段规范」
=====================================
输入：projects/cc-solo/docs/submission/submitfrom.js（前端页面里拷出来的字段定义，含 var submitFields = {...}）
输出：projects/cc-solo/docs/submission/fields.json（机器可读的字段规范，供 build_eval_result.py / submit_eval_result.py 校验与排序）

用法：
    python scripts/cc-solo/extract_submit_fields.py
    python scripts/cc-solo/extract_submit_fields.py --src <submitfrom.js> --out <fields.json>

说明：
- submitfrom.js 里 `var submitFields = { ... }` 的内容本身就是合法 JSON，直接按大括号配对截取后 json.loads。
- 轨迹上传接口（upload URL / method / 表单字段名）也从同一文件里抽出来写进 spec；
  **cookie 属于会话凭据，不写进 json**，请放在 projects/cc-solo/secrets.toml 的 [submission].cookie。
- 表单改了字段后重跑本脚本即可，不改代码。
"""
import argparse
import datetime
import json
import os
import re
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SRC = os.path.join(WORKSPACE, "projects", "cc-solo", "docs", "submission", "submitfrom.js")
DEFAULT_OUT = os.path.join(WORKSPACE, "projects", "cc-solo", "docs", "submission", "fields.json")


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


def parse_source(path):
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()

    raw = json.loads(slice_object(text, "submitFields"))

    fields = []
    for fld in raw.get("fields", []):
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

    # 轨迹上传接口（cookie 不入库）
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
            "form_field": "file",           # 抓包里 Content-Disposition: name="file"
            "response_path_key": "path",    # 返回 {"name","path","size"}，取 path 作为附件标识
            "auth": "cookie: solo_qa_session + solo_qa_csrf（放 secrets.toml [submission].cookie）",
        }

    return {
        "schema": "cc-solo-submit-fields/v1",
        "source": os.path.relpath(path, WORKSPACE).replace("\\", "/"),
        "extracted_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "fingerprint": raw.get("fingerprint"),
        "attachment_max_mb": raw.get("attachment_max_mb"),
        "teams": raw.get("teams", []),
        "groups": raw.get("groups", []),
        "fields": fields,
        "field_order": [f["field_key"] for f in fields],
        "required_fields": [f["field_key"] for f in fields if f["is_required"]],
        "upload_api": upload,
        "submit_api": {
            "url": "https://solo2.jzxhnh.com/api/v1/submissions",
            "note": "提交接口：请求体 {\"data\": {24 字段}, \"schema_fingerprint\": …}，其中 trace_file 为附件数组；"
                    "敏感凭据放 projects/cc-solo/secrets.toml [submission].cookie（或 token）。",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    if not os.path.exists(args.src):
        print(f"[错误] 找不到字段定义文件：{args.src}")
        sys.exit(2)

    spec = parse_source(args.src)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("=" * 60)
    print(f"字段规范已生成：{args.out}")
    print(f"来源：{spec['source']}  fingerprint={spec['fingerprint']}")
    print(f"字段数：{len(spec['fields'])}（必填 {len(spec['required_fields'])}）"
          f"  附件上限 {spec['attachment_max_mb']} MB")
    for fld in spec["fields"]:
        opt = f"  options={fld['options']}" if fld["options"] else ""
        val = f"  validation={fld['validation']}" if fld["validation"] else ""
        print(f"  [{fld['sort_order']:>3}] {fld['field_key']:<18} {fld['label']:<14} "
              f"{fld['field_type']:<10}{' 必填' if fld['is_required'] else ''}{opt}{val}")
    print(f"轨迹上传接口：{spec['upload_api'].get('url')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
