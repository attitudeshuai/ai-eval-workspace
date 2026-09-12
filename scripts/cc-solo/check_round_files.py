#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cc-solo 轮次文件机械校验（只读，不改数据、不生成产物）。

对 records/ 下每个任务的 {任务}-R{NN}.md 逐条检查：
  分数 1-5 整数、五条描述非空、humanizer 强制符号、项目补充符号、A 表套话词、B 表密度、
  跨轮次与前后对比表述、分数与描述方向一致、任务类型/难度合法（难度不写「简单」）、
  TurnID 任务内唯一、SessionID 已回填、完整轨迹与本轮切片文件存在。

用法：
  python scripts/cc-solo/check_round_files.py                    # 当前会话全部任务
  python scripts/cc-solo/check_round_files.py --project cc-002   # 只查某项目
  python scripts/cc-solo/check_round_files.py --task cc-002-codegen-10
退出码：有 error 级问题返回 1（可直接接在导出前做门禁）。
"""
import argparse
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", ".."))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")

try:
    import tomllib
except ImportError:  # py<3.11
    tomllib = None


def load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_ber():
    spec = importlib.util.spec_from_file_location("ber", os.path.join(HERE, "build_eval_result.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def blocks(text):
    out, cur = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def main():
    ber = load_ber()
    cfg = load_toml(os.path.join(PROJECT_DIR, "config.toml"))
    sec = load_toml(os.path.join(PROJECT_DIR, "secrets.toml"))
    work_root = cfg.get("paths", {}).get("work_root", "sessions/cc-solo")
    records_dir = cfg.get("paths", {}).get("records_dir", "records")
    session = sec.get("active_session") or cfg.get("sessions", {}).get("active") or "session-0909"

    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default=session)
    ap.add_argument("--project", help="只查某个项目（如 cc-002）")
    ap.add_argument("--task", help="只查某个任务（如 cc-002-codegen-10）")
    args = ap.parse_args()

    records_root = os.path.join(WORKSPACE, work_root, args.session, records_dir)
    if not os.path.isdir(records_root):
        print("[错误] 找不到记录目录：%s" % records_root)
        return 2

    dims = [d[0] for d in ber.DIMENSIONS]
    allowed_types = tuple(cfg.get("task_types", {}).get("types", []) or
                          ["0-1代码生成", "Feature迭代", "Bug修复", "代码理解", "代码重构", "工程化", "代码测试"])
    allowed_levels = tuple(cfg.get("difficulty", {}).get("levels", []) or ["简单", "中等", "困难", "地狱"])

    checked, errors, warns = 0, [], []
    for proj in sorted(os.listdir(records_root)):
        if args.project and proj != args.project:
            continue
        pdir = os.path.join(records_root, proj)
        if not os.path.isdir(pdir):
            continue
        for group in sorted(os.listdir(pdir)):
            gdir = os.path.join(pdir, group)
            if not os.path.isdir(gdir):
                continue
            for task in sorted(os.listdir(gdir)):
                if args.task and task != args.task:
                    continue
                tdir = os.path.join(gdir, task)
                if not os.path.isdir(tdir):
                    continue
                rounds = sorted(f for f in os.listdir(tdir) if re.match(r"%s-R\d+\.md$" % re.escape(task), f))
                if not rounds:
                    continue
                info_path = os.path.join(tdir, "task-info.md")
                info = open(info_path, encoding="utf-8").read() if os.path.exists(info_path) else ""
                if "<首轮" in info or not info:
                    warns.append("%s：task-info.md 的 SessionID 尚未回填" % task)
                if not os.path.exists(os.path.join(tdir, "%s-trajectory.jsonl" % task)):
                    errors.append("%s：缺完整轨迹 %s-trajectory.jsonl" % (task, task))
                seen_turns = {}
                for f in rounds:
                    checked += 1
                    tag = f[:-3]
                    b = blocks(open(os.path.join(tdir, f), encoding="utf-8").read())
                    turn = b.get("TurnID/PromptID", "")
                    if not turn:
                        errors.append("%s：TurnID 为空" % tag)
                    elif turn in seen_turns:
                        errors.append("%s：TurnID 与 %s 重复" % (tag, seen_turns[turn]))
                    else:
                        seen_turns[turn] = tag
                    if not os.path.exists(os.path.join(tdir, f.replace(".md", "-trajectory.jsonl"))):
                        errors.append("%s：缺本轮轨迹切片" % tag)
                    if b.get("任务类型") not in allowed_types:
                        errors.append("%s：任务类型不合法 %r" % (tag, b.get("任务类型")))
                    level = b.get("任务难度", "")
                    if level not in allowed_levels:
                        errors.append("%s：任务难度不合法 %r" % (tag, level))
                    elif level == "简单":
                        errors.append("%s：任务难度写了「简单」（本期口径：任何轮次都不写简单）" % tag)
                    for dim in dims:
                        sc, desc = b.get(dim, ""), b.get(dim + "-描述", "")
                        if not re.fullmatch(r"[1-5]", sc or ""):
                            errors.append("%s %s：分数非 1-5 整数 %r" % (tag, dim, sc))
                        if len(desc) < 40:
                            errors.append("%s %s：描述过短或为空" % (tag, dim))
                            continue
                        sym = [s for s in ber.HUMANIZER_SYMBOLS if s in desc]
                        if sym:
                            errors.append("%s %s：含 humanizer 强制清除符号 %s" % (tag, dim, "、".join(sym)))
                        psym = [s for s in ber.PROJECT_SYMBOLS if s in desc]
                        if psym:
                            errors.append("%s %s：含项目补充红线写法 %s" % (tag, dim, "、".join(psym)))
                        cl = [w for w in ber.BANNED_CLICHE if w in desc]
                        if cl:
                            errors.append("%s %s：命中 A 表 %s" % (tag, dim, "、".join(cl)))
                        dw = [w for w in ber.DENSITY_WARN if w in desc]
                        if len(dw) >= ber.DENSITY_WARN_MIN:
                            warns.append("%s %s：B 表密集 %s" % (tag, dim, "、".join(dw)))
                        cr = [w for w in ber.CROSS_ROUND if w in desc]
                        if cr:
                            errors.append("%s %s：跨轮次表述 %s" % (tag, dim, "、".join(cr)))
                        pc = [w for w in ber.PAST_COMPARE if w in desc]
                        if pc:
                            errors.append("%s %s：与改动前对比的表述 %s" % (tag, dim, "、".join(pc)))
                        # 长英文串自 2026-09-13 起平台不再判红线，这里不再检查
                        if re.fullmatch(r"[4-5]", sc or "") and any(t in desc for t in ber.STRONG_NEG):
                            warns.append("%s %s=%s 但含强失败词，复核方向一致性" % (tag, dim, sc))
                        if re.fullmatch(r"[12]", sc or "") and not any(t in desc for t in ber.NEG_ANY):
                            warns.append("%s %s=%s 但描述未见负面证据" % (tag, dim, sc))

    print("== cc-solo 轮次文件校验（会话 %s）==" % args.session)
    print("已检查 %d 条数据：error %d，warn %d\n" % (checked, len(errors), len(warns)))
    for x in errors:
        print("  [error] " + x)
    for x in warns:
        print("  [warn ] " + x)
    if not errors and not warns:
        print("  全部通过：分数/描述/词表/符号/跨轮次/一致性/轨迹文件均无问题")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
