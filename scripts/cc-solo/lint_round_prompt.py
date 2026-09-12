#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cc-solo 下一轮提示词校验（只读）：检查 records/ 下的 {任务}-R{NN}-prompt.md 是否符合口径。

口径（见 skills/03-score-annotate.md「下一轮提示词生成」）：
  第二轮及以后只描述现象、不写怎么改、不分条列举；开头固定「修复bug：」。

error 级：开头不对、出现分条列举（行首 1. / 1、/「第一，」）、出现改法类措辞（改成/换成/加个/补一条/
        抽成/统一成/限住/去掉/二选一/收口…）、humanizer 强制符号、A 表套话词、
        **含空行（红线：提示词不得有空行，段落之间只用单个换行）**。
warn 级：建议类措辞（应该/建议/需要把/要把）、B 表密集、跨轮次与前后对比表述。

> 空行红线（2026-09-13 起）：提示词全文不得出现空行，一段一行、段间单换行即可。空行在粘贴进容器时会被
> 当成回车提前提交，且提交表里的 User Prompt 会带上一串空行。此前已发出的提示词不追改，本脚本对它们
> 照旧记 error。

用法：
  python scripts/cc-solo/lint_round_prompt.py
  python scripts/cc-solo/lint_round_prompt.py --project cc-002 --task cc-002-codegen-10
退出码：有 error 级问题返回 1。
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
except ImportError:
    tomllib = None

FIX_ERROR = ("改成", "改为", "换成", "加个", "加一个", "补一条", "补上", "抽成", "统一成", "限住",
             "去掉", "直接引用", "二选一", "收口", "先按", "再按", "需要改", "记得加", "别忘")
FIX_WARN = ("应该", "建议", "需要把", "要把", "最好是")
# 不要求对方验证、不要求回报结果（2026-09-12 口径，见 03-score-annotate「下一轮提示词生成」）。
# 用不带「了」的祈使形态做匹配，避开「我各走了一遍」这类用户自述动作的误报。
ASK_RESULT = ("发我", "发回", "发过来", "把结果", "结果发", "报给我", "回我", "告诉我结果", "给我看")
ASK_VERIFY = ("跑一遍", "走一遍", "点一遍", "验证一下", "起服务", "起起来跑", "跑起来", "试一遍", "测一遍")
NUM_RE = re.compile(r"^\s*(\d+[\.、)）]|第[一二三四五六七八九十]+[，、)])")


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


def main():
    ber = load_ber()
    cfg = load_toml(os.path.join(PROJECT_DIR, "config.toml"))
    sec = load_toml(os.path.join(PROJECT_DIR, "secrets.toml"))
    work_root = cfg.get("paths", {}).get("work_root", "sessions/cc-solo")
    records_dir = cfg.get("paths", {}).get("records_dir", "records")
    session = sec.get("active_session") or cfg.get("sessions", {}).get("active") or "session-0909"

    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default=session)
    ap.add_argument("--project")
    ap.add_argument("--task")
    args = ap.parse_args()

    records_root = os.path.join(WORKSPACE, work_root, args.session, records_dir)
    if not os.path.isdir(records_root):
        print("[错误] 找不到记录目录：%s" % records_root)
        return 2

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
                prompts = sorted(f for f in os.listdir(tdir)
                                 if re.match(r"%s-R\d+-prompt\.md$" % re.escape(task), f))
                for f in prompts:
                    checked += 1
                    tag = f[:-3]
                    text = open(os.path.join(tdir, f), encoding="utf-8").read()
                    if not text.startswith("修复bug："):
                        errors.append("%s：开头不是「修复bug：」" % tag)
                    for line in text.splitlines():
                        if NUM_RE.match(line):
                            errors.append("%s：出现分条列举：%s" % (tag, line.strip()[:24]))
                    hit = [w for w in FIX_ERROR if w in text]
                    if hit:
                        errors.append("%s：出现改法类措辞 %s（第二轮起只描述现象）" % (tag, "、".join(hit)))
                    ar = [w for w in ASK_RESULT if w in text]
                    if ar:
                        errors.append("%s：要求对方回报结果 %s（不要求验证、不要求回报结果）" % (tag, "、".join(ar)))
                    av = [w for w in ASK_VERIFY if w in text]
                    if av:
                        errors.append("%s：要求对方跑一遍验证 %s（不要求验证、不要求回报结果）" % (tag, "、".join(av)))
                    warn_hit = [w for w in FIX_WARN if w in text]
                    if warn_hit:
                        warns.append("%s：含建议类措辞 %s，确认是在描述现象还是在给方案" % (tag, "、".join(warn_hit)))
                    sym = [s for s in ber.HUMANIZER_SYMBOLS if s in text]
                    if sym:
                        errors.append("%s：含 humanizer 强制清除符号 %s" % (tag, "、".join(sym)))
                    cl = [w for w in ber.BANNED_CLICHE if w in text]
                    if cl:
                        errors.append("%s：命中 A 表套话词 %s" % (tag, "、".join(cl)))
                    dw = [w for w in ber.DENSITY_WARN if w in text]
                    if len(dw) >= ber.DENSITY_WARN_MIN:
                        warns.append("%s：B 表密集 %s" % (tag, "、".join(dw)))
                    # 长英文串自 2026-09-13 起平台不再判红线，这里不再检查
                    cr = [w for w in ber.CROSS_ROUND if w in text]
                    pc = [w for w in ber.PAST_COMPARE if w in text]
                    if cr or pc:
                        warns.append("%s：含跨轮次/前后对比说法 %s（提示词里可保留用户口吻，但注意别让人读不懂）"
                                     % (tag, "、".join(cr + pc)))
                    # 红线：提示词不得有空行（段落之间只用单个换行）
                    blank_no = [i + 1 for i, ln in enumerate(text.splitlines()) if not ln.strip()]
                    if blank_no:
                        errors.append("%s：提示词含空行（第 %s 行）——提示词不得有空行，段落之间只用单个换行，"
                                      "粘贴进容器时空行会被当成回车提前提交"
                                      % (tag, "、".join(str(x) for x in blank_no[:6])))

    print("== cc-solo 下一轮提示词校验（会话 %s）==" % args.session)
    print("已检查 %d 份提示词：error %d，warn %d\n" % (checked, len(errors), len(warns)))
    for x in errors:
        print("  [error] " + x)
    for x in warns:
        print("  [warn ] " + x)
    if not errors and not warns:
        print("  全部通过：均为「只写现象、不分条、无改法措辞」的写法")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
