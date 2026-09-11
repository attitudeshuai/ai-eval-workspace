#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 单轮录入辅助（02-round-capture 的机械部分）
====================================================
把「从容器轨迹里定位第 N 轮 + 切片 + 回填 SessionID/TurnID」这套机械操作固定成脚本，
避免手写 PowerShell/正则出错（例如 `"cc-solo-$task:…"` 在 PowerShell 里会被当成盘符变量，
必须写成 `"cc-solo-${task}:…"`）。

**只做机械部分**：任务类型 / 任务难度 / 语言框架属于判断项，仍由 agent（或人工）判断后
写进 `{任务}-R{NN}.md`；本脚本只负责轨迹产物与校验提示。

用法：
    # 先看本题有几轮、各轮 promptId（不落盘）
    python scripts/cc-solo/capture_round.py --task cc-001-feature-06 --list

    # 录入第 1 轮：切 R01 轨迹 + 生成完整轨迹 + 打印回填信息
    python scripts/cc-solo/capture_round.py --task cc-001-feature-06 --round 1

    # 只看解析结果不写文件
    python scripts/cc-solo/capture_round.py --task cc-001-feature-06 --round 1 --dry-run

前置：轨迹已由 agent 从容器导出到任务记录目录
    docker cp "cc-solo-${task}:/home/node/.claude/projects/-workspace/." "<RECORD_DIR>/<项目>/<项目>-<类型>/<任务>/"

产物：
    {RECORD_DIR}/<项目>/<项目>-<类型>/<任务>/<任务>-R{NN}-trajectory.jsonl   # 本轮切片（打分定位用）
    {RECORD_DIR}/<项目>/<项目>-<类型>/<任务>/<任务>-trajectory.jsonl          # 完整轨迹（提交附件，随轮次覆盖增长）

轮次口径（一轮 = 一次用户键入）：
    type == "user" 且 message.content 是**字符串** → 一次键入（promptId = 该轮 TurnID）；
    content 为数组的 user 条目是工具结果回填，复用所属轮次的 promptId，不算新轮次。
"""
import argparse
import json
import os
import re
import shutil
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.toml")
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.toml")

# 任务名里的类型 slug（config 的 aliases 用 feat，实际目录用 feature，两个都收）
TYPE_SLUGS = {"codegen", "feature", "feat", "bugfix", "understand", "refactor", "engineering", "test"}
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_settings(session_override=None):
    cfg, sec = load_toml(CONFIG_PATH), load_toml(SECRETS_PATH)
    work_root = sec.get("work_root") or cfg.get("paths", {}).get("work_root", "sessions/cc-solo")
    records_dir = sec.get("records_dir") or cfg.get("paths", {}).get("records_dir", "records")
    session = session_override or sec.get("active_session") or cfg.get("sessions", {}).get("active")
    max_rounds = int(cfg.get("limits", {}).get("max_rounds", 10))
    return {"work_root": work_root, "records_dir": records_dir, "session": session, "max_rounds": max_rounds}


def split_task_id(task_id):
    """cc-001-feature-06 → (cc-001, feature, 06)；项目名可含连字符，从右往左切。"""
    parts = task_id.split("-")
    if len(parts) < 3 or not re.fullmatch(r"\d{2}", parts[-1]) or parts[-2] not in TYPE_SLUGS:
        raise SystemExit(f"[错误] 任务名不符合 {{项目}}-{{类型}}-{{索引}}：{task_id}（索引两位补零，类型须为 {sorted(TYPE_SLUGS)}）")
    return "-".join(parts[:-2]), parts[-2], parts[-1]


def record_dir_of(settings, task_id):
    project, slug, _ = split_task_id(task_id)
    return os.path.join(WORKSPACE, settings["work_root"], settings["session"],
                        settings["records_dir"], project, f"{project}-{slug}", task_id)


def find_session_file(rdir):
    """轨迹目录里那个 UUID.jsonl 就是会话文件；排除本脚本生成的 {任务}[-R{NN}]-trajectory.jsonl。"""
    if not os.path.isdir(rdir):
        raise SystemExit(f"[错误] 记录目录不存在：{rdir}")
    cands = [f for f in sorted(os.listdir(rdir))
             if f.endswith(".jsonl") and not f.endswith("-trajectory.jsonl")]
    if not cands:
        raise SystemExit(f"[错误] {rdir} 下没有会话轨迹（*.jsonl）。先确认已从容器导出：\n"
                         f'        docker cp "cc-solo-${{task}}:/home/node/.claude/projects/-workspace/." "{rdir}\\"')
    if len(cands) > 1:
        uuids = [f for f in cands if UUID_RE.match(os.path.splitext(f)[0])]
        if len(uuids) == 1:
            return os.path.join(rdir, uuids[0]), [f"(忽略非会话文件) {f}" for f in cands if f != uuids[0]]
        raise SystemExit(f"[错误] {rdir} 下有多个 .jsonl（{cands}）：容器可能被复用，或导出前未清理旧轨迹。请人工确认哪份是本任务会话。")
    return os.path.join(rdir, cands[0]), []


def parse_turns(path):
    """返回 (lines, turns)；turns 里每项 = {line_no, prompt_id, text, ts}，按用户键入顺序。"""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    turns = []
    for i, raw in enumerate(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "user" or obj.get("isMeta"):
            continue
        msg = obj.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, str):     # 工具结果回填：content 是数组
            continue
        turns.append({
            "line_no": i,
            "prompt_id": obj.get("promptId") or obj.get("uuid") or "",
            "text": content,
            "ts": obj.get("timestamp", ""),
        })
    return lines, turns


def read_md_field(path, field):
    """读 {任务}-R{NN}.md 里 '## {field}' 段的第一段非空文本。"""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    m = re.search(r"^##\s*" + re.escape(field) + r"\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else None


def norm(s):
    return re.sub(r"\s+", "", s or "")


def collect_turn_ids(rdir, task_id, exclude_round=None):
    """扫描同任务已有 R*.md 的 TurnID，用于查重。"""
    found = {}
    for f in sorted(os.listdir(rdir)):
        m = re.fullmatch(re.escape(task_id) + r"-R(\d{2})\.md", f)
        if not m or m.group(1) == exclude_round:
            continue
        v = read_md_field(os.path.join(rdir, f), "TurnID/PromptID")
        if v and v.strip():
            found.setdefault(v.strip(), []).append(f)
    return found


def main():
    ap = argparse.ArgumentParser(description="cc-solo 单轮录入辅助（轨迹定位 + 切片 + 回填信息）")
    ap.add_argument("--task", required=True, help="任务名，如 cc-001-feature-06")
    ap.add_argument("--round", type=int, help="要录入的轮次 N（1..10）")
    ap.add_argument("--list", action="store_true", help="只列出本题所有轮次与 promptId")
    ap.add_argument("--dry-run", action="store_true", help="只解析，不写任何文件")
    ap.add_argument("--session", help="覆盖 session 名（默认读 config/secrets 的 active）")
    args = ap.parse_args()

    st = load_settings(args.session)
    rdir = record_dir_of(st, args.task)
    sess_file, notes = find_session_file(rdir)
    lines, turns = parse_turns(sess_file)
    session_id = os.path.splitext(os.path.basename(sess_file))[0]

    print(f"任务        : {args.task}")
    print(f"记录目录    : {os.path.relpath(rdir, WORKSPACE)}")
    print(f"会话文件    : {os.path.basename(sess_file)}")
    print(f"SessionID   : {session_id}")
    print(f"用户键入轮次: {len(turns)} 轮（轨迹共 {len(lines)} 行）")
    for n in notes:
        print(f"  ! {n}")
    if session_id != os.path.splitext(os.path.basename(sess_file))[0] or not UUID_RE.match(session_id):
        print("  ! 文件名不是 UUID，SessionID 可能取错，请人工核对")

    if args.list or not args.round:
        for i, t in enumerate(turns, 1):
            prev = re.sub(r"\s+", " ", t["text"]).strip()
            print(f"  R{i:02d}  promptId={t['prompt_id']}  {t['ts'][:19]}  {prev[:60]}{'…' if len(prev) > 60 else ''}")
        if not args.list:
            print("\n提示：加 --round N 录入第 N 轮")
        return 0

    n = args.round
    if n < 1 or n > st["max_rounds"]:
        raise SystemExit(f"[错误] 轮次必须在 1..{st['max_rounds']}（会话满 {st['max_rounds']} 轮须开新任务）")
    if n > len(turns):
        raise SystemExit(f"[错误] 轨迹里只有 {len(turns)} 轮用户键入，取不到 R{n:02d}。"
                         f"（若模型还在跑，等它答完静止后再导出一次轨迹）")
    if n > 1 and n - 1 > len(turns):
        print(f"  ! 提示：要录入 R{n:02d}，轨迹里已有 {len(turns)} 轮，中间可能缺轮")

    cur = turns[n - 1]
    md = os.path.join(rdir, f"{args.task}-R{n:02d}.md")
    other = collect_turn_ids(rdir, args.task, exclude_round=f"{n:02d}")
    dup = other.get(cur["prompt_id"])

    print(f"\n== R{n:02d} ==")
    print(f"TurnID/PromptID : {cur['prompt_id']}")
    print(f"User Prompt     : {len(cur['text'])} 字符")
    print("--- User Prompt 原文 ---")
    print(cur["text"].rstrip())
    print("--- 原文结束 ---")

    md_prompt = read_md_field(md, "User Prompt")
    if md_prompt is None:
        print(f"\n  ! {os.path.basename(md)} 不存在（或没有 User Prompt 段）：需新建并填字段")
    elif norm(md_prompt) == norm(cur["text"]):
        print(f"\n  ✓ 与 {os.path.basename(md)} 的 User Prompt 一致（逐字原文，可用于锚定）")
    else:
        print(f"\n  ! 与 {os.path.basename(md)} 的 User Prompt 不一致：")
        print(f"     md  : {re.sub(chr(10), ' ', md_prompt)[:80]}…")
        print(f"     轨迹: {re.sub(chr(10), ' ', cur['text'])[:80]}…")
        print("     → 以轨迹为准（User Prompt 必须逐字原文），需修正 md")
    if dup:
        print(f"  ! TurnID 与 {dup} 重复：同一 TurnID 不能出现在两轮")
    else:
        print(f"  ✓ TurnID 在本题已录入轮次中唯一")

    if args.dry_run:
        print("\n(--dry-run：未写入任何文件)")
        return 0

    start = cur["line_no"]
    end = turns[n]["line_no"] if n < len(turns) else len(lines)
    slice_path = os.path.join(rdir, f"{args.task}-R{n:02d}-trajectory.jsonl")
    with open(slice_path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines[start:end])
    full_path = os.path.join(rdir, f"{args.task}-trajectory.jsonl")
    shutil.copyfile(sess_file, full_path)

    print(f"\n已写入：")
    print(f"  切片   {os.path.relpath(slice_path, WORKSPACE)}（{end - start} 行）")
    print(f"  完整   {os.path.relpath(full_path, WORKSPACE)}（{len(lines)} 行，随轮次覆盖增长）")
    print(f"\n回填 task-info.md：SessionID = {session_id}")
    print(f"回填 {os.path.basename(md)}：TurnID/PromptID = {cur['prompt_id']}")
    print("下一步：判定任务类型/难度/语言框架并回填 md，然后执行 score {n} 打分".format(n=n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
