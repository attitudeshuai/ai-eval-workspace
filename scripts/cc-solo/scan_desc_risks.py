# -*- coding: utf-8 -*-
"""描述风险自查（第二轮质检新规则，2026-09-13 实测打回后提炼）。

配合 check_round_files.py 使用：门禁查的是「格式 / 词表 / 符号 / 跨轮次」这类硬红线，
本脚本查的是**平台 LLM 质检会打回、但机械上合法的写法**，属于提示级自查，需人工判断。

用法：
    python scripts/cc-solo/scan_desc_risks.py --project cc-002
    python scripts/cc-solo/scan_desc_risks.py --session session-0909 --project cc-002 --task cc-002-feature-23
    python scripts/cc-solo/scan_desc_risks.py --project cc-002 --json out.json

四条规则（都来自平台真实打回）：
    R1 次数统计无对象 —— 只写「N 次调用里只有一次被拒」这类没有对象的次数，读者无法定位；
                        正确写法要落到「第几次工具调用 + 文件名/函数名 + 命令或报错原文 + 后果」。
    R2 空指代        —— 「这一条 / 那一条 / 同一条现象 / 这一步 / 那处 / 查不清的那条」没有具体指向。
    R3 环境原因挂扣分 —— 「执行能力」描述里把环境缺依赖/镜像缺工具链当作扣分依据（平台判非模型过错）。
    R4 主观形容词     —— 「不可追踪 / 轻微 / 偏弱 / 略显 / 明显的猜测」这类评价词，要求换客观事实。

误报说明：`七次调用里没有出现任何待办项` 这类**陈述事实且不带失误**的句子可能被 R1 命中，
脚本已尽量排除「没有 / 无一 / 都正常」这类否定或全通过表述，剩下的仍需人工过一眼。
"""
import argparse
import io
import json
import os
import re
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIMS = ["交付完整性", "指令遵循", "任务规划", "推理能力", "执行能力"]

# R1：次数 + 负面结果，且句中不出现「第 N 次 / 没有 / 都 / 全部」这类已定位或全通过表述
R1 = re.compile(
    r"[一二三四五六七八九十百零两\d]+\s*次[^。；，]{0,18}?"
    r"(没成功|被拒|略|多余|白跑|浪费|出错|有问题)"
)
R1_EXCLUDE = re.compile(r"(第|没有|无一|都正常|都成功|全部|全程|次数)")
# R2：无具体指向的指代（只收平台真实点过名的几类；普通的「这一步／这一处」在指代明确时不算问题）
R2 = re.compile(r"(查不清的那条|同一条现象|这条现象|那条现象|某个现象|这一条现象|那一条现象|没有具体指向)")
# R3：环境原因写进执行能力
R3 = re.compile(r"(环境里没装|环境缺|没装[^。；]{0,10}依赖|基础镜像|精简镜像|沙箱|依赖没装|工具链)")
# R4：主观形容词
R4 = re.compile(r"(不可追踪|轻微|偏弱|略显|较为冗余|明显的?猜测|较强的?猜测|不太到位)")

RULES = {
    "R1": ("次数统计无对象", R1),
    "R2": ("空指代", R2),
    "R3": ("环境原因挂扣分（执行能力）", R3),
    "R4": ("主观形容词", R4),
}


def record_files(root, task_filter):
    """root = records/{project}；下面一层是 {project}-{type}，再下一层是任务目录。"""
    for type_dir in sorted(os.listdir(root)):
        tdir = os.path.join(root, type_dir)
        if not os.path.isdir(tdir):
            continue
        for task in sorted(os.listdir(tdir)):
            d = os.path.join(tdir, task)
            if not os.path.isdir(d):
                continue
            if task_filter and not any(task == f or task.startswith(f + "-") for f in task_filter):
                continue
            for fn in sorted(os.listdir(d)):
                if re.match(r"^%s-R\d+\.md$" % re.escape(task), fn):
                    yield task, os.path.join(d, fn), fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="session-0909")
    ap.add_argument("--project", default="cc-002")
    ap.add_argument("--task", action="append", default=[], help="只看指定任务，可重复")
    ap.add_argument("--json", help="把结果写成 JSON")
    args = ap.parse_args()

    root = os.path.join(WS, "sessions", "cc-solo", args.session, "records", args.project)
    if not os.path.isdir(root):
        print("找不到记录目录：%s" % root)
        return 1

    findings = []
    n_files = 0
    for task, path, fn in record_files(root, set(args.task)):
        n_files += 1
        text = io.open(path, encoding="utf-8").read()
        for dim in DIMS:
            m = re.search(r"^##\s*" + dim + r"-描述\s*$\s*(.*?)(?=^##\s|\Z)", text, re.M | re.S)
            if not m:
                continue
            body = m.group(1).strip()
            key = "%s %s" % (fn[:-3], dim)
            for code, (label, pat) in RULES.items():
                if code == "R3" and dim != "执行能力":
                    continue
                for hit in pat.finditer(body):
                    frag = hit.group(0)
                    if code == "R1" and R1_EXCLUDE.search(frag):
                        continue
                    findings.append({"record": key, "dim": dim, "rule": code, "label": label, "snippet": frag})

    print("== cc-solo 描述风险自查（%s / %s）==" % (args.session, args.project))
    print("已扫描 %d 个轮次文件，命中 %d 处（提示级，需人工判断）" % (n_files, len(findings)))
    for code in ("R1", "R2", "R3", "R4"):
        items = [f for f in findings if f["rule"] == code]
        print()
        print("-- %s %s（%d 处）--" % (code, RULES[code][0], len(items)))
        for f in items:
            print("  %s | %s" % (f["record"], f["snippet"]))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"session": args.session, "project": args.project, "count": len(findings), "findings": findings},
                      fh, ensure_ascii=False, indent=2)
        print()
        print("已写出：%s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
