#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 符号扫描（只读）
========================
扫描记录文件里的 AI 痕迹符号与疑似破折号变体，覆盖 `build_eval_result.py` 只查五个「-描述」的盲区
（其他问题、备注、模型回答存档、R02 提示词文件等）。

用法：
    python scripts/cc-solo/check_symbols.py --task cc-001-feature-06
    python scripts/cc-solo/check_symbols.py                 # 扫当前 session 全部任务
    python scripts/cc-solo/check_symbols.py --task cc-001-feature-06 --only 破折号,一一

说明：
    --only 用「类别名的一部分」做过滤，便于只查某一类符号。
"""
import argparse
import os
import re
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 类别名 -> 正则。前面几类是 humanizer-zh 的强制清除项，后面几类是易被误当破折号的写法。
PATTERNS = [
    ("双破折号 ——", r"\u2014\u2014"),
    ("单破折号 —", r"\u2014"),
    ("半角连字符 –", r"\u2013"),
    ("全角横线 －", r"\uff0d"),
    ("制表横线 ─", r"\u2500"),
    ("框线 ━", r"\u2501"),
    ("两个汉字一一", r"一一"),
    ("箭头 →", r"\u2192"),
    ("箭头 ⇒", r"\u21d2"),
    ("箭头 =>", r"=>"),
    ("箭头 ->", r"->"),
    ("直角引号 「」", r"[\u300c\u300d]"),
    ("反引号", r"`"),
    ("ASCII 双引号", r'"'),
    ("ASCII 单引号", r"'"),
    ("省略号 ......", r"\.{6,}"),
    ("重复顿号 、、", r"、、"),
    ("重复逗号 ，，", r"，，"),
    ("重复句号 。。", r"。。"),
]


def load_settings(session=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from capture_round import load_settings as ls
    return ls(session)


def collect_files(records_root, task=None):
    out = []
    if task:
        from capture_round import split_task_id
        project, slug, _ = split_task_id(task)
        root = os.path.join(records_root, project, "{}-{}".format(project, slug), task)
        if not os.path.isdir(root):
            raise SystemExit("[错误] 记录目录不存在：{}".format(root))
        out = [os.path.join(root, f) for f in sorted(os.listdir(root))
               if f.endswith(".md") or f.endswith(".jsonl")]
    else:
        for dirpath, _dirs, files in os.walk(records_root):
            for f in files:
                if f.endswith(".md"):
                    out.append(os.path.join(dirpath, f))
    # 轨迹文件太大且是原始数据，不扫
    return [p for p in out if not p.endswith(".jsonl")]


def main():
    ap = argparse.ArgumentParser(description="cc-solo 记录符号扫描（只读）")
    ap.add_argument("--task", help="只扫某个任务，如 cc-001-feature-06")
    ap.add_argument("--session", help="覆盖 session 名")
    ap.add_argument("--only", help="只扫类别名包含该子串的项，逗号分隔")
    ap.add_argument("--context", type=int, default=18, help="上下文宽度")
    ap.add_argument("--quiet", action="store_true", help="只输出汇总")
    args = ap.parse_args()

    st = load_settings(args.session)
    records_root = os.path.join(WORKSPACE, st["work_root"], st["session"], st["records_dir"])
    files = collect_files(records_root, args.task)
    pats = PATTERNS
    if args.only:
        keys = [k.strip() for k in args.only.split(",") if k.strip()]
        pats = [p for p in PATTERNS if any(k in p[0] for k in keys)]

    total, per_cat = 0, {}
    for p in files:
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        hits = []
        for name, pat in pats:
            for m in re.finditer(pat, txt):
                ctx = txt[max(0, m.start() - args.context):m.end() + args.context].replace("\n", " ")
                hits.append((name, ctx))
                per_cat[name] = per_cat.get(name, 0) + 1
                total += 1
        if hits and not args.quiet:
            print("=" * 70)
            print(os.path.relpath(p, records_root))
            for name, ctx in hits:
                print("   [{}] ...{}...".format(name, ctx))
    print("=" * 70)
    print("扫描文件 {} 个（session {}）｜命中 {} 处".format(len(files), st["session"], total))
    for k, v in sorted(per_cat.items(), key=lambda x: -x[1]):
        print("   {:<16} {}".format(k, v))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
