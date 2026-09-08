#!/usr/bin/env python3
"""
向 claudccode 满意度交付飞书多维表格逐行追加数据（每轮一条数据 = 一条记录）。

输入：导出脚本生成的正式提交表 CSV（scripts/claudccode/export_submit.py 产出，
      表头见 templates/submit-headers.csv，每行 = 一轮对话 = 一条数据）。

- 把 CSV 列名映射为多维表格字段名（表头命名有差异，见 MAPPING）
- 字段名不在表中 → 报错（防止拼写错误静默丢数据）
- 单选字段值必须是已有选项；任务类型「Feature迭代」自动映射为表内选项「feature迭代」
- 默认按 (SessionID, TurnID/PromptID) 查重，已存在则跳过该行；--force 强制追加
- 只读/关联字段（父记录等）自动跳过

配置：
- 非敏感：projects/claudccode/config.toml [feishu]（app_token / table_id）
- 敏感：app_id / app_secret 优先读 projects/claudccode/secrets.toml [feishu]，
  缺省回退读 projects/code-eval-gsb/secrets.toml [feishu]（复用 GSB 应用）

用法：
    python3 scripts/claudccode/append_delivery_feishu.py \
        --csv deliverables/claudccode/session-0907/正式提交表-session-0907-2026-09-07.csv --dry-run
    python3 scripts/claudccode/append_delivery_feishu.py \
        --csv <提交表.csv> --submitter 张三          # 正式追加（默认按 SessionID+TurnID 去重）
    python3 scripts/claudccode/append_delivery_feishu.py --csv <提交表.csv> --force

依赖：仅标准库（Python 3.11+，需 tomllib）
"""

import argparse
import csv
import json
import sys
import time
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
FIELD_TYPE_URL = 15  # 超链接：写入须用 {text, link} 对象

# 只读/关联等不可写字段类型（公式、双向关联、地理位置、群聊、创建时间、创建人、
# 修改人、修改时间、自动编号）：发现时警告并跳过
READONLY_FIELD_TYPES = {18, 19, 20, 21, 22, 23, 1001, 1002, 1003, 1004}

WORKSPACE = Path(__file__).resolve().parent.parent.parent
CC_PROJECT = WORKSPACE / "projects" / "claudccode"
GSB_PROJECT = WORKSPACE / "projects" / "code-eval-gsb"

# CSV 列名 → 多维表格字段名映射（None 表示该列不投递/表中无此字段）
MAPPING = {
    # 同名直通
    "User Prompt": "User Prompt",
    "SessionID": "SessionID",
    "TurnID/PromptID": "TurnID/PromptID",
    "初始环境快照": "初始环境快照",
    "环境可复现等级": "环境可复现等级",
    "Harness": "Harness",
    "操作系统": "操作系统",
    "任务类型": "任务类型",
    "任务难度": "任务难度",
    "语言/框架": "语言/框架",
    "交付完整性": "交付完整性",
    "指令遵循": "指令遵循",
    "任务规划": "任务规划",
    "推理能力": "推理能力",
    "执行能力": "执行能力",
    "其他问题": "其他问题",
    # 重命名（表头带空格）
    "Harness版本": "Harness 版本",
    "交付完整性-描述": "交付完整性 - 描述",
    "指令遵循-描述": "指令遵循 - 描述",
    "任务规划-描述": "任务规划 - 描述",
    "推理能力-描述": "推理能力 - 描述",
    "执行能力-描述": "执行能力 - 描述",
    # 内部列（不投递）
    "Repo URL": None,
    "截图附件": None,
    "备注": None,
    "轨迹文件": None,
    # 标注人默认作为「提交人」来源（可被 --submitter 覆盖）
    "标注人": "提交人",
}

# 任务类型值映射：本工作台用「Feature迭代」，飞书表内选项是小写「feature迭代」
TASK_TYPE_VALUE_MAP = {"Feature迭代": "feature迭代"}

MULTI_SEPARATORS = ("、", "，", ",")


def fail(msg, code=1):
    print(f"错误：{msg}")
    sys.exit(code)


def load_config():
    cfg_path = CC_PROJECT / "config.toml"
    cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8")).get("feishu", {})
    missing = [k for k in ("app_token", "table_id") if not cfg.get(k)]
    if missing:
        fail(f"claudccode config.toml [feishu] 缺少：{missing}")
    return cfg


def load_secrets():
    """app_id/app_secret：优先 claudccode/secrets.toml，缺省回退 code-eval-gsb/secrets.toml。"""
    for proj in (CC_PROJECT, GSB_PROJECT):
        sp = proj / "secrets.toml"
        if sp.exists():
            sec = tomllib.loads(sp.read_text(encoding="utf-8")).get("feishu", {})
            if sec.get("app_id") and sec.get("app_secret"):
                return sec
    fail("未找到飞书 app_id/app_secret：请在 projects/claudccode/secrets.toml [feishu] "
         "或 projects/code-eval-gsb/secrets.toml [feishu] 配置（secrets-simple.toml 有模板）")


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


def row_exists(token, app_token, table_id, session_id, turn_id):
    """按 (SessionID, TurnID/PromptID) 查重。"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
    body = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {"field_name": "SessionID", "operator": "is", "value": [session_id]},
                {"field_name": "TurnID/PromptID", "operator": "is", "value": [turn_id]},
            ],
        },
        "field_names": ["SessionID", "TurnID/PromptID"],
        "page_size": 5,
    }
    data = http("POST", url, token, body)
    return data.get("total", 0) > 0


def convert_record(record, fields):
    """按字段类型把值转为飞书 API 格式，返回 (payload, empty_names, skipped_names)。"""
    unknown = [k for k in record if k not in fields]
    payload, skipped = {}, []
    for name, value in record.items():
        if name not in fields:
            continue
        meta = fields[name]
        ftype = meta["type"]
        options = {o["name"] for o in (meta.get("property") or {}).get("options") or []}

        if value is None or (isinstance(value, str) and not value.strip()):
            continue

        if ftype in READONLY_FIELD_TYPES:
            skipped.append(name)
            continue

        if ftype == FIELD_TYPE_MULTI_SELECT:
            # 顿号/逗号拆分
            parts = [str(value)]
            for sep in MULTI_SEPARATORS:
                parts = [p2 for p in parts for p2 in p.split(sep)]
            vals = [p.strip() for p in parts if p.strip()]
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
        elif ftype == FIELD_TYPE_DATETIME:
            try:
                payload[name] = int(float(value))
            except (TypeError, ValueError):
                fail(f"日期字段「{name}」的值 {value!r} 不是毫秒时间戳")
        elif ftype == FIELD_TYPE_URL:
            v = str(value).strip()
            payload[name] = {"text": v, "link": v}  # 超链接字段须对象格式，纯字符串会报 URLFieldConvFail
        elif ftype == FIELD_TYPE_CHECKBOX:
            payload[name] = str(value).strip() in ("是", "true", "True", "1")
        else:
            payload[name] = str(value)

    empty = [name for name in fields if name not in payload]
    if skipped:
        print(f"提示：以下 {len(skipped)} 个字段为只读/关联字段，跳过不写入：{skipped}")
    return payload, unknown, empty


def build_record(row, fields, submitter, ts_ms):
    """CSV 一行 → {飞书字段名: 值}。"""
    record = {}
    for csv_col, feishu_name in MAPPING.items():
        if feishu_name is None or csv_col not in row:
            continue
        val = (row.get(csv_col) or "").strip()
        if not val:
            continue
        # 提交人：优先命令行 --submitter
        if feishu_name == "提交人":
            if submitter:
                continue  # 下面统一写
            record[feishu_name] = val
            continue
        # 任务类型值映射（Feature迭代 → feature迭代）
        if csv_col == "任务类型" and val in TASK_TYPE_VALUE_MAP:
            val = TASK_TYPE_VALUE_MAP[val]
        record[feishu_name] = val

    if submitter:
        record["提交人"] = submitter
    record["提交时间"] = ts_ms
    # 字段名必须都在表里
    unknown = [k for k in record if k not in fields]
    if unknown:
        fail(f"以下字段名不在多维表格中（疑似命名差异/拼写错误）：{unknown}\n现有字段：{sorted(fields)}")
    return record


def main():
    ap = argparse.ArgumentParser(description="向 claudccode 交付飞书多维表格逐行追加数据（每行=一条数据）")
    ap.add_argument("--csv", help="正式提交表 CSV 路径（默认取 deliverables/claudccode/{SESSION}/ 下最新一份）")
    ap.add_argument("--session", help="SESSION_NAME（配合 --csv 缺省时用）")
    ap.add_argument("--submitter", help="提交人姓名（覆盖 CSV 标注人列，写入表中「提交人」文本字段）")
    ap.add_argument("--dry-run", action="store_true", help="只校验（拉表头/选项/查重），不写入")
    ap.add_argument("--force", action="store_true", help="(SessionID, TurnID) 已存在时仍强制追加")
    args = ap.parse_args()

    # ---- 定位 CSV ----
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            fail(f"CSV 不存在：{csv_path}")
    else:
        from export_submit import _load_config  # 复用导出脚本的配置读取
        session = args.session or _load_config().get("active") or "session-0907"
        dl_root = WORKSPACE / _load_config()["deliverables_root"] / session
        cands = sorted(dl_root.glob("正式提交表-*.csv")) if dl_root.exists() else []
        if not cands:
            fail(f"deliverables 下没有正式提交表：{dl_root}")
        csv_path = cands[-1]
    print(f"提交表：{csv_path}")

    cfg = load_config()
    sec = load_secrets()
    token = get_tenant_token(sec["app_id"], sec["app_secret"])
    app_token, table_id = cfg["app_token"], cfg["table_id"]
    fields = list_fields(token, app_token, table_id)
    print(f"已读取多维表格 {len(fields)} 个字段：{sorted(fields)}")

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    ts_ms = int(time.time() * 1000)
    total = len(rows)
    created, skipped_exist, errors = [], [], []
    print(f"共 {total} 条数据（每行=一轮=一条）待投递。")

    for i, row in enumerate(rows, 1):
        session_id = (row.get("SessionID") or "").strip()
        turn_id = (row.get("TurnID/PromptID") or "").strip()
        tag = f"[{i}/{total}] Session={session_id} Turn={turn_id}"
        if not (session_id and turn_id):
            errors.append(f"{tag} 缺少 SessionID 或 TurnID/PromptID，跳过")
            continue
        if not args.force and row_exists(token, app_token, table_id, session_id, turn_id):
            skipped_exist.append(tag)
            continue
        record = build_record(row, fields, args.submitter, ts_ms)
        payload, unknown, empty = convert_record(record, fields)
        if unknown:
            fail(f"字段名不在表中：{unknown}")
        if args.dry_run:
            print(f"  {tag} → 将写入 {len(payload)} 个字段；留空：{empty or '无'}")
            continue
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        data = http("POST", url, token, {"fields": payload})
        rid = data.get("record", {}).get("record_id", "?")
        created.append((tag, rid))
        print(f"  已追加 {tag} record_id={rid}")

    print("=" * 60)
    print(f"数据总数：{total} | 追加成功：{len(created)} | 已存在跳过：{len(skipped_exist)} | 错误：{len(errors)}")
    if args.dry_run:
        print("[dry-run] 仅校验，未写入任何记录。")
    if skipped_exist:
        print("已存在（如需强制追加加 --force）：")
        for t in skipped_exist:
            print("  " + t)
    if errors:
        print("错误项：")
        for t in errors:
            print("  " + t)
    if created:
        print("新增记录：")
        for tag, rid in created:
            print(f"  {rid}  {tag}")


if __name__ == "__main__":
    main()
