#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 轨迹摘要（只读）
========================
把一段（或整份）Claude Code 轨迹压缩成「改了什么文件 / 跑了什么命令 / 最后说了什么」，
供判定任务难度、核对技术栈、以及 03-score-annotate 打分前快速摸底使用。

**只读**：不改任何数据文件。

用法：
    python scripts/cc-solo/digest_trajectory.py --task cc-001-feature-06 --round 1
    python scripts/cc-solo/digest_trajectory.py --task cc-001-feature-06            # 整份会话轨迹
    python scripts/cc-solo/digest_trajectory.py --file <某个 jsonl 路径> --tail 800
    python scripts/cc-solo/digest_trajectory.py --task cc-001-feature-06 --round 1 --full   # 打印全部 bash 命令与文件
"""
import argparse
import json
import os
import re
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
READ_TOOLS = ("Read", "Glob", "Grep", "LS")


def ws(path):
    return os.path.relpath(path, WORKSPACE) if path.startswith(WORKSPACE) else path


def load_lines(path):
    with open(path, encoding="utf-8") as f:
        return [l for l in f if l.strip()]


def digest(path, tail_chars=400, full=False):
    files, cmds, reads = [], [], []
    n_asst = n_tool_results = n_user_typed = 0
    texts = []
    for raw in load_lines(path):
        try:
            o = json.loads(raw)
        except json.JSONDecodeError:
            continue
        t = o.get("type")
        m = o.get("message") or {}
        if t == "user":
            c = m.get("content")
            if isinstance(c, str):
                n_user_typed += 1
            elif isinstance(c, list):
                n_tool_results += 1
            continue
        if t != "assistant":
            continue
        n_asst += 1
        c = m.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict):
                continue
            kind = blk.get("type")
            if kind == "tool_use":
                name, inp = blk.get("name"), (blk.get("input") or {})
                if name in WRITE_TOOLS:
                    fp = inp.get("file_path") or inp.get("notebook_path") or ""
                    if fp and fp not in files:
                        files.append(fp)
                elif name == "Bash":
                    cmds.append(re.sub(r"\s+", " ", inp.get("command") or "").strip())
                elif name in READ_TOOLS:
                    p = inp.get("file_path") or inp.get("pattern") or ""
                    if p and p not in reads:
                        reads.append(p)
            elif kind == "text":
                tx = (blk.get("text") or "").strip()
                if tx:
                    texts.append(tx)

    print("轨迹文件  : {}".format(ws(path)))
    print("用户键入  : {} 轮 | assistant 消息 {} 条 | 工具结果 {} 条".format(n_user_typed, n_asst, n_tool_results))
    print("\n改动文件（{} 个）:".format(len(files)))
    for f in (files if full else files[:20]):
        print("   {}".format(f.replace("/workspace/", "")))
    if not full and len(files) > 20:
        print("   …（还有 {} 个，加 --full 全看）".format(len(files) - 20))
    print("\nbash 命令（{} 条）:".format(len(cmds)))
    for c in (cmds if full else cmds[:20]):
        print("   {}".format(c[:160]))
    if not full and len(cmds) > 20:
        print("   …（还有 {} 条，加 --full 全看）".format(len(cmds) - 20))
    if reads:
        print("\n读过（前 10）: " + ", ".join(r.replace("/workspace/", "") for r in reads[:10]))
    print("\n末条回复（截 {} 字）:".format(tail_chars))
    print("   " + re.sub(r"\s+", " ", texts[-1] if texts else "(无)")[:tail_chars])


def main():
    ap = argparse.ArgumentParser(description="cc-solo 轨迹摘要（只读）")
    ap.add_argument("--task", help="任务名，如 cc-001-feature-06")
    ap.add_argument("--round", type=int, help="第 N 轮切片（缺省用整份会话轨迹）")
    ap.add_argument("--file", help="直接指定 jsonl 路径")
    ap.add_argument("--session", help="覆盖 session 名")
    ap.add_argument("--tail", type=int, default=400, help="末条回复截断字数（默认 400）")
    ap.add_argument("--full", action="store_true", help="打印全部文件与命令")
    args = ap.parse_args()

    if args.file:
        path = args.file
    else:
        if not args.task:
            raise SystemExit("[错误] 需要 --task 或 --file")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from capture_round import load_settings, record_dir_of
        st = load_settings(args.session)
        rdir = record_dir_of(st, args.task)
        if args.round:
            path = os.path.join(rdir, "{}-R{:02d}-trajectory.jsonl".format(args.task, args.round))
        else:
            path = os.path.join(rdir, "{}-trajectory.jsonl".format(args.task))
    if not os.path.exists(path):
        raise SystemExit("[错误] 轨迹不存在：{}\n       先跑 capture_round.py 生成切片，或确认已从容器导出".format(path))
    digest(path, args.tail, args.full)
    return 0


if __name__ == "__main__":
    sys.exit(main())
