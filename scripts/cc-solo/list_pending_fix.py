#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 待返修清单（返修第一步：从提交列表发现 PENDING_FIX）
=============================================================
平台质检会给每条提交一个结论：通过（QC_PASSED）或 **待返修**（PENDING_FIX）。
本脚本负责「发现 + 归类」，不改任何数据；整改与更新见 04-export-submit.md 步骤 6。

用法：
    # 列出所有待返修（默认排除 config.toml [submission].fix_exclude_ids 里的 ID）
    python scripts/cc-solo/list_pending_fix.py

    # 看某几条的详细打回原因（逐条 GET 详情，打印失败规则 + 缺失要素）
    python scripts/cc-solo/list_pending_fix.py --detail

    # 连最新一条提交详情一起看（没给 --ids 时默认只看清单）
    python scripts/cc-solo/list_pending_fix.py --ids 5237,5238 --detail

    # 机器可读（返修流水线用）：写出 JSON 清单
    python scripts/cc-solo/list_pending_fix.py --json out/pending_fix.json

    # 覆盖排除名单（默认读 config；不给则用 4142/4143/4144）
    python scripts/cc-solo/list_pending_fix.py --exclude 4142,4143

约定（重要）：
    · **排除名单里的 ID 一律不动**（规则未定，动了会污染别人正在对齐的口径）；
      名单在 `projects/cc-solo/config.toml [submission].fix_exclude_ids`。
    · 详情 JSON 落盘到 `deliverables/cc-solo/<session>/submission-<id>-detail.json`，
      与 submit_eval_result.py --detail-id 的落盘位置一致。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

try:
    import tomllib
except ImportError:  # py<3.11
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", ".."))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")
DEFAULT_EXCLUDE = [4142, 4143, 4144]
STATUS_LABEL = {"PENDING_FIX": "待返修", "QC_PASSED": "质检通过"}


def load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def settings():
    cfg = load_toml(os.path.join(PROJECT_DIR, "config.toml"))
    sec = load_toml(os.path.join(PROJECT_DIR, "secrets.toml"))
    sub_cfg = cfg.get("submission", {})
    sub_sec = sec.get("submission", {})
    base = (sub_sec.get("submit_url") or sub_cfg.get("submit_url")
            or "https://solo2.jzxhnh.com/api/v1/submissions").rstrip("/")
    cookie = sub_sec.get("cookie", "")
    cache = os.path.join(PROJECT_DIR, ".solo_session.json")
    if os.path.exists(cache):
        try:
            c = json.load(open(cache, encoding="utf-8"))
            cookie = c.get("cookie") or cookie
        except Exception:  # noqa: BLE001
            pass
    csrf = ""
    for part in cookie.split(";"):
        if "solo_qa_csrf=" in part:
            csrf = part.split("=", 1)[1].strip()
    exclude = sub_cfg.get("fix_exclude_ids")
    exclude = [int(x) for x in exclude] if exclude else DEFAULT_EXCLUDE
    session = sec.get("active_session") or cfg.get("sessions", {}).get("active") or "session-0909"
    out_dir = os.path.join(WORKSPACE, cfg.get("paths", {}).get("deliverables_root",
                                                                "deliverables/cc-solo"), session)
    return {"base": base, "cookie": cookie, "csrf": csrf, "exclude": exclude,
            "session": session, "out_dir": out_dir}


def get_json(url, st):
    req = urllib.request.Request(url, headers={
        "Cookie": st["cookie"], "X-CSRF-Token": st["csrf"], "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_list(st, status, page_size=100):
    items, page = [], 1
    while True:
        url = "%s?page=%d&page_size=%d&stage=&keyword=&date_from=&date_to=&user_id=0" % (
            st["base"], page, page_size)
        d = get_json(url, st)
        items.extend(d.get("items") or [])
        meta = d.get("meta") or {}
        if page >= int(meta.get("total_pages") or 1):
            break
        page += 1
    return items


def fetch_detail(st, sid):
    d = get_json("%s/%d" % (st["base"], sid), st)
    os.makedirs(st["out_dir"], exist_ok=True)
    path = os.path.join(st["out_dir"], "submission-%d-detail.json" % sid)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d, path


def failed_checks(detail):
    out = []
    for c in ((detail.get("verdict") or {}).get("failed_checks") or []):
        name = c.get("check_name", "")
        dim = name.split(" · ")[0].strip()
        rule = name.split(" · ")[-1].strip()
        detail_txt = c.get("detail", "")
        miss = (detail_txt.split("缺失的要素：")[-1].strip()
                if "缺失的要素" in detail_txt else detail_txt.strip())
        out.append({"dim": dim, "rule": rule, "summary": c.get("summary", ""), "missing": miss})
    return out


def main():
    ap = argparse.ArgumentParser(description="cc-solo 待返修清单（PENDING_FIX 发现与归类）")
    ap.add_argument("--status", default="PENDING_FIX", help="只看该状态（默认 PENDING_FIX）")
    ap.add_argument("--ids", help="只看这些提交 ID（逗号分隔）；给了就跳过列表筛选")
    ap.add_argument("--exclude", help="覆盖排除名单（逗号分隔 ID）")
    ap.add_argument("--detail", action="store_true", help="逐条拉详情，打印失败规则与缺失要素")
    ap.add_argument("--json", help="把清单写成 JSON（返修流水线用）")
    ap.add_argument("--all-status", action="store_true", help="打印全部状态分布（排查用）")
    args = ap.parse_args()

    st = settings()
    if args.exclude:
        st["exclude"] = [int(x) for x in args.exclude.replace(" ", "").split(",") if x]
    if not st["cookie"]:
        print("[错误] 没拿到 cookie：检查 projects/cc-solo/secrets.toml [submission].cookie "
              "或先跑 submit_eval_result.py --login-only --commit")
        return 2

    if args.ids:
        ids = [int(x) for x in args.ids.replace(" ", "").split(",") if x]
        items = [{"id": i} for i in ids]
        dist = {}
    else:
        items = fetch_list(st, args.status)
        dist = {}
        for it in items:
            dist[it.get("status_label")] = dist.get(it.get("status_label"), 0) + 1
        items = [it for it in items if it.get("status") == args.status]

    if args.all_status:
        print("[状态分布] %s" % "，".join("%s %d" % (k, v) for k, v in dist.items()))

    excluded = [it for it in items if int(it.get("id", 0)) in st["exclude"]]
    todo = [it for it in items if int(it.get("id", 0)) not in st["exclude"]]

    print("接口    ：%s" % st["base"])
    print("会话    ：%s｜交付目录：%s" % (st["session"], os.path.relpath(st["out_dir"], WORKSPACE)))
    print("排除名单：%s（配置项 submission.fix_exclude_ids，规则未定，勿动）"
          % ", ".join(str(x) for x in st["exclude"]))
    print("待处理  ：%d 条%s" % (len(todo), ("（另排除 %d 条）" % len(excluded)) if excluded else ""))

    plan = []
    for it in sorted(todo, key=lambda x: int(x["id"])):
        sid = int(it["id"])
        row = {"id": sid, "status": it.get("status"), "round_no": it.get("round_no"),
               "question_type": it.get("question_type"), "session_id": it.get("session_id"),
               "turn_id": it.get("turn_id"), "scores": it.get("scores"),
               "qc_summary": it.get("qc_summary")}
        print("-" * 78)
        print("#%d  %s %s 轮次=%s  版本 v%s" % (sid, it.get("question_type"), it.get("difficulty"),
                                              it.get("round_no"), it.get("current_version")))
        print("   session_id=%s  turn_id=%s" % (it.get("session_id"), it.get("turn_id")))
        print("   分数：%s" % json.dumps(it.get("scores"), ensure_ascii=False))
        if args.detail:
            detail, path = fetch_detail(st, sid)
            row["editable"] = detail.get("editable")
            row["locked_fields"] = detail.get("locked_fields")
            checks = failed_checks(detail)
            row["failed_checks"] = checks
            print("   可修改：%s｜锁定字段：%s" % (detail.get("editable"),
                                              "、".join(detail.get("locked_fields") or []) or "无"))
            dims = {}
            for c in checks:
                dims.setdefault(c["dim"], []).append(c)
                print("   · [%s] %s" % (c["dim"], c["rule"]))
                print("     %s" % c["missing"].replace("\n", " ")[:300])
            row["dims_to_fix"] = {k: [c["rule"] for c in v] for k, v in dims.items()}
            print("   详情落盘：%s" % os.path.relpath(path, WORKSPACE))
        plan.append(row)

    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"base": st["base"], "excluded": [int(x["id"]) for x in excluded],
                       "items": plan}, f, ensure_ascii=False, indent=2)
        print("\n已写出清单：%s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
