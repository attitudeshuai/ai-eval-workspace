#!/usr/bin/env python3
"""
向 SWE 交付飞书多维表格追加一行任务记录（swe-like 项目专用）。

输入为一个 JSON 文件：{ "字段名": "值", ... }，字段名必须与多维表格表头完全一致。
- 表头中不存在的 key 直接报错（防止拼写错误静默丢数据）
- 单选/多选字段的值必须是已有选项，否则报错并列出全部合法选项
- 多选字段值用顿号（、）或逗号分隔多个选项
- 未提供的字段留空，并在输出中列出，便于人工核对
- 默认按 config.toml [feishu].dedupe_field（默认「题目名称」）查重，重复时需 --force 才允许追加

配置：
- 非敏感配置在 projects/swe-like/config.toml 的 [feishu] 段（app_token / table_id / dedupe_field）
- 敏感配置在 projects/swe-like/secrets.toml 的 [feishu] 段（app_id / app_secret）

用法：
    python3 append_delivery_feishu.py --json <记录.json> [--dry-run] [--force]

依赖：仅标准库（Python 3.11+，需 tomllib）
"""

import argparse
import datetime as _dt
import json
import sys
import tomllib
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "https://open.feishu.cn/open-apis"

# 飞书多维表格字段类型
FIELD_TYPE_TEXT = 1
FIELD_TYPE_NUMBER = 2
FIELD_TYPE_SINGLE_SELECT = 3
FIELD_TYPE_MULTI_SELECT = 4
FIELD_TYPE_DATETIME = 5
FIELD_TYPE_CHECKBOX = 7
FIELD_TYPE_URL = 15

# 只读/自动字段类型（公式、双向关联、地理位置、群聊、创建时间、
# 创建人、修改人、修改时间、自动编号）：API 写入会报错，发现时警告并跳过
READONLY_FIELD_TYPES = {19, 20, 21, 22, 23, 1001, 1002, 1003, 1004}

# 多选值分隔符
MULTI_SEPARATORS = ("、", "，", ",")

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent / "projects" / "swe-like"


def fail(msg, code=1):
    print(f"错误：{msg}")
    sys.exit(code)


def load_config():
    config_path = PROJECT_DIR / "config.toml"
    secrets_path = PROJECT_DIR / "secrets.toml"
    if not secrets_path.exists():
        fail(f"secrets.toml 不存在：{secrets_path}（请从 secrets-simple.toml 复制并填入真实值）")

    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    secrets = tomllib.loads(secrets_path.read_text(encoding="utf-8"))

    feishu_cfg = config.get("feishu", {})
    feishu_sec = secrets.get("feishu", {})
    missing = [k for k in ("app_token", "table_id") if not feishu_cfg.get(k)]
    missing += [k for k in ("app_id", "app_secret") if not feishu_sec.get(k)]
    if missing:
        fail(f"飞书配置缺失：{missing}（app_token/table_id 在 config.toml [feishu]，app_id/app_secret 在 secrets.toml [feishu]）")
    return {**feishu_cfg, **feishu_sec}


def http(method, url, token=None, body=None, raw=False):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        fail(f"HTTP {e.code} {url}\n{detail}")
    if payload.get("code") != 0:
        fail(f"飞书 API 返回错误 code={payload.get('code')} msg={payload.get('msg')}\n{url}")
    return payload if raw else payload.get("data", {})


def get_tenant_token(app_id, app_secret):
    payload = http("POST", f"{BASE_URL}/auth/v3/tenant_access_token/internal",
                   body={"app_id": app_id, "app_secret": app_secret}, raw=True)
    return payload["tenant_access_token"]


def list_fields(token, app_token, table_id):
    """返回 {字段名: field_meta}，含类型与选项。"""
    fields = {}
    page_token = None
    while True:
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields?page_size=100"
        if page_token:
            url += f"&page_token={page_token}"
        data = http("GET", url, token)
        for f in data.get("items", []):
            fields[f["field_name"]] = f
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return fields


def check_duplicate(token, app_token, table_id, field_name, value):
    """按指定字段查重。"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
    body = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {"field_name": field_name, "operator": "is", "value": [value]}
            ],
        },
        "field_names": [field_name],
        "page_size": 5,
    }
    data = http("POST", url, token, body)
    return data.get("total", 0) > 0


def split_multi(value):
    """按顿号/逗号拆分多选值，去掉空项。"""
    parts = [value]
    for sep in MULTI_SEPARATORS:
        parts = [p2 for p in parts for p2 in p.split(sep)]
    return [p.strip() for p in parts if p.strip()]


def to_timestamp_ms(value):
    """把日期字符串（YYYY-MM-DD 或 ISO8601）或时间戳转为毫秒时间戳。"""
    v = str(value).strip()
    if v.isdigit():
        n = int(v)
        return n if len(str(n)) >= 12 else n * 1000  # 秒 → 毫秒
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
        try:
            dt = _dt.datetime.strptime(v, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期：{value!r}（支持 YYYY-MM-DD / ISO8601 / 毫秒或秒时间戳）")


def convert_record(record, fields):
    """按字段类型把 JSON 值转换为飞书 API 需要的格式，返回 (fields_payload, unknown_keys, empty_names)。"""
    unknown = [k for k in record if k not in fields]
    payload = {}
    skipped = []
    for name, value in record.items():
        if name not in fields:
            continue
        meta = fields[name]
        ftype = meta["type"]
        options = {o["name"] for o in (meta.get("property") or {}).get("options") or []}

        if value is None or (isinstance(value, str) and not value.strip()):
            continue  # 留空

        if ftype in READONLY_FIELD_TYPES:
            skipped.append(name)
            continue

        if ftype == FIELD_TYPE_MULTI_SELECT:
            vals = split_multi(str(value))
            bad = [v for v in vals if v not in options]
            if bad:
                fail(f"多选字段「{name}」的值 {bad} 不在已有选项中。\n  合法选项：{sorted(options)}")
            payload[name] = vals
        elif ftype == FIELD_TYPE_SINGLE_SELECT:
            v = str(value).strip()
            if v not in options:
                fail(f"单选字段「{name}」的值 {v!r} 不在已有选项中。\n  合法选项：{sorted(options)}")
            payload[name] = v
        elif ftype == FIELD_TYPE_NUMBER:
            try:
                n = float(value)
                payload[name] = int(n) if n == int(n) else n
            except (TypeError, ValueError):
                fail(f"数字字段「{name}」的值 {value!r} 不是数字")
        elif ftype == FIELD_TYPE_CHECKBOX:
            payload[name] = str(value).strip() in ("是", "true", "True", "1")
        elif ftype == FIELD_TYPE_DATETIME:
            try:
                payload[name] = to_timestamp_ms(value)
            except ValueError as e:
                fail(str(e))
        elif ftype == FIELD_TYPE_URL:
            v = str(value).strip()
            payload[name] = {"text": v, "link": v}
        else:
            payload[name] = str(value)

    empty = [name for name in fields if name not in payload]
    if skipped:
        print(f"提示：以下 {len(skipped)} 个字段为飞书自动字段（创建人/创建时间等），已跳过不写入：")
        for name in skipped:
            print(f"  - {name}")
    return payload, unknown, empty


def main():
    ap = argparse.ArgumentParser(description="向 SWE 交付飞书多维表格追加一行任务记录")
    ap.add_argument("--json", required=True, help="记录 JSON 文件路径（{字段名: 值}）")
    ap.add_argument("--dry-run", action="store_true", help="只校验不写入")
    ap.add_argument("--force", action="store_true", help="查重字段重复时仍强制追加")
    args = ap.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        fail(f"JSON 文件不存在：{json_path}")
    record = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        fail("JSON 顶层必须是对象 {字段名: 值}")

    cfg = load_config()
    token = get_tenant_token(cfg["app_id"], cfg["app_secret"])
    app_token, table_id = cfg["app_token"], cfg["table_id"]
    dedupe_field = cfg.get("dedupe_field") or "题目名称"

    # 1) 拉取表头
    fields = list_fields(token, app_token, table_id)
    print(f"已读取多维表格 {len(fields)} 个字段。")

    # 2) 未知字段校验
    unknown = [k for k in record if k not in fields]
    if unknown:
        print("错误：以下字段名在多维表格中不存在（疑似拼写错误）：")
        for k in unknown:
            print(f"  - {k}")
        sys.exit(1)

    # 3) 查重（默认「题目名称」）
    dup_val = str(record.get(dedupe_field, "")).strip()
    if dup_val and check_duplicate(token, app_token, table_id, dedupe_field, dup_val):
        if not args.force:
            fail(f"「{dedupe_field}」已存在：{dup_val}\n如确认要重复追加，请加 --force。")
        print(f"警告：「{dedupe_field}」已存在，--force 强制追加：{dup_val}")

    # 4) 类型转换（含单选/多选选项校验、日期/超链接处理）
    payload, _, empty = convert_record(record, fields)
    print(f"将写入 {len(payload)}/{len(fields)} 个字段，以下 {len(empty)} 个字段留空：")
    for name in empty:
        print(f"  - {name}")

    if args.dry_run:
        print("\n[dry-run] 校验通过，未写入多维表格。")
        return

    # 5) 创建记录
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    data = http("POST", url, token, {"fields": payload})
    record_id = data.get("record", {}).get("record_id", "?")
    print(f"\n已追加记录 record_id={record_id}。")


if __name__ == "__main__":
    main()
