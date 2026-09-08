#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claudccode 正式提交表导出 + 质检
=================================
读取 {work_root}/{SESSION}/records/ 下所有任务，把每个任务的共享字段（task-info.md）
与每轮数据文件（{TASK_ID}-R{NN}.md）合并为「一轮 = 一行」的正式提交表 CSV，并输出质检报告。

用法：
    python scripts/claudccode/export_submit.py                     # 默认会话（secrets/config）
    python scripts/claudccode/export_submit.py --session session-0907   # 指定会话
    python scripts/claudccode/export_submit.py --task cc-1         # 只导出指定任务
    python scripts/claudccode/export_submit.py --out /tmp/x.csv    # 指定输出

说明：
- 只读数据文件 + 写 CSV；不改动任何记录。
- 机械/格式级质检：字段完整、分数范围、轮次≤上限、SessionID 一致、TurnID 唯一、
  快照格式、首轮难度、类型分布、打分与描述方向一致性提示。
- 评分依据是否到位属主观质检，需人工复核（本脚本不代写原因）。
"""
import argparse
import csv
import datetime
import os
import re
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "claudccode")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.toml")
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.toml")
HEADERS_CSV = os.path.join(PROJECT_DIR, "templates", "submit-headers.csv")

# ---------------------------------------------------------------- 配置读取
def _load_toml_simple(path, keys):
    """无 tomllib 依赖的极简 TOML 标量读取；命中 [section] 表与 key = value。"""
    out = {}
    section = ""
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line.strip("[]").strip()
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    full = (section + "." + k) if section else k
                    if full in keys:
                        out[full] = v
    except FileNotFoundError:
        pass
    return out


def _load_config():
    keys = {
        "paths.work_root", "paths.records_dir", "paths.deliverables_root",
        "sessions.active", "naming.task_prefix", "limits.max_rounds",
        "delivery.filename_prefix", "task_types.types",
        "difficulty.levels", "difficulty.first_round_forbidden",
        "scoring.dimensions", "scoring.score_min", "scoring.score_max",
        "harness.claude_code_version",
    }
    cfg = {}
    try:
        import tomllib  # Python 3.11+
        for p in (CONFIG_PATH, SECRETS_PATH):
            if os.path.exists(p):
                with open(p, "rb") as f:
                    data = tomllib.load(f)
                    cfg["work_root"] = data.get("paths", {}).get("work_root", cfg.get("work_root"))
                    cfg["records_dir"] = data.get("paths", {}).get("records_dir", cfg.get("records_dir"))
                    cfg["deliverables_root"] = data.get("paths", {}).get("deliverables_root", cfg.get("deliverables_root"))
                    cfg["active"] = data.get("sessions", {}).get("active", cfg.get("active"))
                    cfg["task_prefix"] = data.get("naming", {}).get("task_prefix", cfg.get("task_prefix"))
                    cfg["max_rounds"] = data.get("limits", {}).get("max_rounds", cfg.get("max_rounds"))
                    cfg["filename_prefix"] = data.get("delivery", {}).get("filename_prefix", cfg.get("filename_prefix"))
                    cfg["types"] = data.get("task_types", {}).get("types", cfg.get("types"))
                    cfg["dims"] = data.get("scoring", {}).get("dimensions", cfg.get("dims"))
                    cfg["first_forbidden"] = data.get("difficulty", {}).get("first_round_forbidden", cfg.get("first_forbidden"))
                    cfg["claude_code_version"] = data.get("harness", {}).get("claude_code_version", cfg.get("claude_code_version"))
                    # secrets.toml 覆盖
                    if p == SECRETS_PATH:
                        cfg["active"] = data.get("active_session", cfg.get("active"))
    except ImportError:
        simple = _load_toml_simple(CONFIG_PATH, keys)
        cfg = {
            "work_root": simple.get("paths.work_root", "sessions/claudccode"),
            "records_dir": simple.get("paths.records_dir", "records"),
            "deliverables_root": simple.get("paths.deliverables_root", "deliverables/claudccode"),
            "active": simple.get("sessions.active", "session-0907"),
            "task_prefix": simple.get("naming.task_prefix", "cc"),
            "max_rounds": int(simple.get("limits.max_rounds", "10")),
            "filename_prefix": simple.get("delivery.filename_prefix", "正式提交表"),
            "types": None, "dims": None, "first_forbidden": ["简单"],
            "claude_code_version": simple.get("harness.claude_code_version", ""),
        }
    cfg.setdefault("max_rounds", 10)
    cfg.setdefault("task_prefix", "cc")
    cfg.setdefault("filename_prefix", "正式提交表")
    cfg.setdefault("deliverables_root", "deliverables/claudccode")
    cfg.setdefault("records_dir", "records")
    cfg.setdefault("work_root", "sessions/claudccode")
    cfg.setdefault("types", ["0-1代码生成", "Feature迭代", "Bug修复", "代码理解", "代码重构", "工程化", "代码测试"])
    cfg.setdefault("dims", ["交付完整性", "指令遵循", "任务规划", "推理能力", "执行能力"])
    cfg.setdefault("first_forbidden", ["简单"])
    cfg.setdefault("claude_code_version", "")
    return cfg


# ---------------------------------------------------------------- 解析记录
def read_utf8(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def parse_blocks(text):
    """按行首 '## ' 切块：{标题: 内容}（值保留多行，末尾去空行）。"""
    blocks, cur = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            blocks[cur] = []
        elif cur is not None:
            blocks[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in blocks.items()}


def parse_task_info(path):
    return parse_blocks(read_utf8(path))


def parse_round_file(path):
    return parse_blocks(read_utf8(path))


# ---------------------------------------------------------------- 列定义
def load_headers():
    """列顺序与 templates/submit-headers.csv 保持一致；文件不存在时用内置默认。"""
    default = ("任务类型,任务难度,语言/框架,Harness,Harness版本,操作系统,环境可复现等级,"
               "初始环境快照,User Prompt,SessionID,TurnID/PromptID,轨迹文件,"
               "交付完整性,交付完整性-描述,指令遵循,指令遵循-描述,任务规划,任务规划-描述,"
               "推理能力,推理能力-描述,执行能力,执行能力-描述,其他问题,"
               "Repo URL,截图附件,标注人,备注")
    if os.path.exists(HEADERS_CSV):
        line = read_utf8(HEADERS_CSV).strip().splitlines()
        if line:
            return [c for c in next(csv.reader([line[0]]))]
    return [c for c in next(csv.reader([default]))]


DIM_FIELDS = [  # (维度, 分数小标题, 描述小标题)
    ("交付完整性", "交付完整性", "交付完整性-描述"),
    ("指令遵循", "指令遵循", "指令遵循-描述"),
    ("任务规划", "任务规划", "任务规划-描述"),
    ("推理能力", "推理能力", "推理能力-描述"),
    ("执行能力", "执行能力", "执行能力-描述"),
]

RE_SNAPSHOT = re.compile(r"^https://github\.com/[^/]+/[^/]+/commit/[0-9a-fA-F]{40}$")
# 强失败词：高分(≥4)描述中出现则提示复核（如「满分却写没完成」这类矛盾）
STRONG_NEG = ("未完成", "没完成", "没改", "未实现", "未提供", "未处理", "失败", "无法运行",
              "不可用", "虚假", "答非所问", "一行代码", "严重幻觉", "死循环", "编译不过",
              "跑不通", "无法编译", "没跑通", "压根没")
# 弱负面证据词：低分(≤2)描述中完全无任何负面词时提示复核
NEG_ANY = STRONG_NEG + ("报错", "错误", "幻觉", "编造", "臆造", "瞎猜", "无视", "无头苍蝇",
                        "冗余", "缺失", "遗漏", "漏掉", "滥用", "低效", "反复", "重复",
                        "卡住", "绕圈", "无效", "不符合", "多余", "越界", "擅自")

# Harness → 轨迹根前缀：Codex CLI 的轨迹在 ~/.codex/sessions/；Claude Code 在容器里做，轨迹导出到本机 records/<REPO>/<REPO>-trajectory.jsonl
HARNESS_TRAJ_PREFIX = {
    "Codex CLI": "~/.codex/sessions",
    "Claude Code": "records/",
}


def build_row(task_id, info, rfile, headers, cfg, problems):
    """把 task-info + round-file 拼成一行；按 headers 顺序对齐。"""
    num_m = re.search(r"R(\d{2,3})$", os.path.splitext(os.path.basename(rfile))[0])
    round_no = int(num_m.group(1)) if num_m else 0
    b = parse_round_file(rfile)

    row = {h: "" for h in headers}
    # 每轮字段
    row["任务类型"] = b.get("任务类型", "")
    row["任务难度"] = b.get("任务难度", "")
    row["语言/框架"] = b.get("语言/框架", "")
    row["User Prompt"] = b.get("User Prompt", "")
    row["TurnID/PromptID"] = b.get("TurnID/PromptID", "")
    row["其他问题"] = b.get("其他问题", "")
    # 内部字段
    row["截图附件"] = b.get("截图附件（内部）", "")
    row["备注"] = b.get("备注（内部）", "")
    for dim, s_title, d_title in DIM_FIELDS:
        row[s_title] = b.get(s_title, "")
        row[d_title] = b.get(d_title, "")
    # 共享字段（task-info）
    row["初始环境快照"] = info.get("初始环境快照", "")
    row["Harness"] = info.get("Harness", "")
    row["Harness版本"] = info.get("Harness版本", "")
    # 导出自动带入配置里的 Claude Code 默认版本（避免每任务手填/填错；仅对 Claude Code）
    if row["Harness"] == "Claude Code" and cfg.get("claude_code_version"):
        row["Harness版本"] = cfg["claude_code_version"]
    row["操作系统"] = info.get("操作系统", "")
    row["环境可复现等级"] = info.get("环境可复现等级", "")
    row["SessionID"] = info.get("SessionID", "")
    row["轨迹文件"] = info.get("轨迹根目录（轨迹文件）", "")
    row["Repo URL"] = info.get("Repo URL", "")
    row["标注人"] = info.get("标注人", "")

    # ---------------- 质检 ----------------
    tag = f"{task_id} {os.path.basename(rfile)}"
    for s_title, d_title in [(x[1], x[2]) for x in DIM_FIELDS]:
        sv = row[s_title].strip()
        dv = row[d_title].strip()
        if sv:
            try:
                sc = int(sv)
                if not (1 <= sc <= 5):
                    problems.append(f"[分数越界] {tag} {s_title}={sv}（须 1-5 整数）")
            except ValueError:
                problems.append(f"[分数非整数] {tag} {s_title}={sv!r}")
        else:
            problems.append(f"[字段缺失] {tag} 缺少 {s_title}")
        if not dv:
            problems.append(f"[描述缺失] {tag} 缺少 {d_title}（必填）")
        elif len(dv) < 8:
            problems.append(f"[描述过短] {tag} {d_title} 过短，疑似笼统，请人工补充")
        # 方向一致性（仅提示，不自动改）
        try:
            sc = int(row[s_title].strip()) if row[s_title].strip() else None
        except ValueError:
            sc = None
        if sc is not None:
            has_strong = any(t in dv for t in STRONG_NEG)
            has_neg = any(t in dv for t in NEG_ANY)
            if sc >= 4 and has_strong:
                problems.append(f"[一致性提示] {tag} {s_title}={sc} 但描述含强失败词，请人工复核")
            if sc <= 2 and not has_neg:
                problems.append(f"[一致性提示] {tag} {s_title}={sc} 但描述未见负面证据，请人工复核")

    if round_no == 1 and row["任务难度"] in cfg.get("first_forbidden", ["简单"]):
        problems.append(f"[首轮难度] {tag} 首轮严禁「{row['任务难度']}」")
    if not row["User Prompt"]:
        problems.append(f"[Prompt缺失] {tag} 缺少 User Prompt")
    if not row["TurnID/PromptID"]:
        problems.append(f"[TurnID缺失] {tag} 缺少 TurnID/PromptID")
    if row["任务类型"] not in cfg.get("types", []):
        problems.append(f"[类型非法] {tag} 任务类型={row['任务类型']!r}")
    snap = row["初始环境快照"]
    if snap and not RE_SNAPSHOT.match(snap):
        problems.append(f"[快照格式] {tag} 快照非完整 40 位 permalink：{snap[:60]}")
    elif not snap:
        problems.append(f"[快照缺失] {tag} 缺少初始环境快照")
    # 轨迹文件须与 Harness 对应（哪个 CLI 做的就放哪个 CLI 的目录下）
    traj = row["轨迹文件"]
    prefix = HARNESS_TRAJ_PREFIX.get(row["Harness"]) if row["Harness"] else None
    if row["Harness"] and not prefix:
        problems.append(f"[轨迹Harness] {tag} 未知 Harness={row['Harness']!r}，无法校验轨迹目录")
    elif prefix and traj and not traj.startswith(prefix):
        problems.append(f"[轨迹路径] {tag} Harness={row['Harness']} 但轨迹文件不在 {prefix} 下：{traj[:80]}")
    elif not traj and row["SessionID"]:
        problems.append(f"[轨迹缺失] {tag} 缺少轨迹文件（按 Harness 填 ~/.codex/sessions 或 records/<REPO>/<REPO>-trajectory.jsonl 下文件）")
    return row, round_no


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", help="SESSION_NAME；默认取 secrets/config 的 active")
    ap.add_argument("--task", help="只导出指定任务 ID")
    ap.add_argument("--out", help="CSV 输出路径（默认 deliverables/claudccode/{SESSION}/正式提交表-...csv）")
    args = ap.parse_args()

    cfg = _load_config()
    session = args.session or cfg.get("active") or "session-0907"
    records_root = os.path.join(WORKSPACE, cfg["work_root"], session, cfg["records_dir"])
    if not os.path.isdir(records_root):
        print(f"[错误] records 目录不存在：{records_root}")
        sys.exit(2)

    # 收集任务
    tasks = sorted(d for d in os.listdir(records_root)
                   if os.path.isdir(os.path.join(records_root, d)) and not d.startswith("."))
    if args.task:
        tasks = [t for t in tasks if t == args.task]
        if not tasks:
            print(f"[错误] 未找到任务 {args.task}")
            sys.exit(2)

    headers = load_headers()
    rows, problems = [], []
    info_cache = {}
    per_task_rounds = {}

    for task_id in tasks:
        tdir = os.path.join(records_root, task_id)
        info_path = os.path.join(tdir, "task-info.md")
        info = parse_task_info(info_path) if os.path.exists(info_path) else {}
        info_cache[task_id] = info
        if not info:
            problems.append(f"[task-info缺失] {task_id} 缺少 task-info.md")
        rfiles = sorted(f for f in os.listdir(tdir)
                        if re.match(rf"^{re.escape(task_id)}-R\d+\.md$", f))
        rounds = []
        for rf in rfiles:
            row, rn = build_row(task_id, info, os.path.join(tdir, rf), headers, cfg, problems)
            rows.append((task_id, rn, row))
            rounds.append((rn, row))
        per_task_rounds[task_id] = rounds

        # 会话一致性
        sids = {r["SessionID"] for _, r in rounds}
        if len(sids) > 1:
            problems.append(f"[SessionID不一致] {task_id} 各轮取值不同：{sids}")
        turns = [r["TurnID/PromptID"] for _, r in rounds]
        dup = [t for t in set(turns) if turns.count(t) > 1 and t]
        if dup:
            problems.append(f"[TurnID重复] {task_id} 重复 TurnID：{dup}")
        if len(rounds) > int(cfg.get("max_rounds", 10)):
            problems.append(f"[轮次超限] {task_id} 共 {len(rounds)} 轮 > {cfg.get('max_rounds')}")

    # 排序：task_id 自然序 + 轮次序
    def nat_key(t):
        m = re.search(r"(\d+)$", t[0])
        return (int(m.group(1)) if m else 0, t[1])
    rows.sort(key=nat_key)

    # 输出 CSV（UTF-8 BOM）
    date = datetime.date.today().strftime("%Y-%m-%d")
    out = args.out or os.path.join(WORKSPACE, cfg["deliverables_root"], session,
                                   f"{cfg['filename_prefix']}-{session}-{date}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for _, _, row in rows:
            w.writerow(row)

    # 类型分布（按天口径近似：本批）
    from collections import Counter
    type_counter = Counter(r["任务类型"] for _, _, r in rows)
    total = len(rows)

    print("=" * 60)
    print(f"导出完成：{out}")
    print(f"会话：{session} | 任务数：{len(tasks)} | 数据条数（行数）：{total}")
    print("-" * 60)
    if type_counter:
        print("任务类型分布：")
        for k, v in type_counter.most_common():
            print(f"  {k}: {v} ({v / total * 100:.1f}%)")
        print("  参照偏序：0-1代码生成/Feature迭代/Bug修复 > 代码理解≈代码重构 > 其他")
    print("-" * 60)
    if problems:
        print(f"质检发现 {len(problems)} 项（部分为提示项，需人工复核）：")
        for p in problems:
            print("  " + p)
    else:
        print("质检通过：无机械性问题。")
    print("=" * 60)
    print("注：主观质检（原因是否到位/是否真看过轨迹/是否雷同题）须人工复核，脚本不代写原因。")


if __name__ == "__main__":
    main()
