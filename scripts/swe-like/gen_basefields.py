#!/usr/bin/env python3
"""为 swe-like 交付包生成 docs/底稿必填字段.md（人工回填，不打包 zip）。

格式要求（质检）：Verify Rubric 与产物结果都用 1. / 2. / 3. 编号清单，逐条对应。

用法：python3 gen_basefields.py <题目目录1> [<题目目录2> ...]
"""
import re
import sys
import tomllib
from pathlib import Path

import yaml


def rubric_numbered(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))["rubrics"]
    items = sorted(doc, key=lambda r: (int(r["id"]) if str(r["id"]).isdigit() else 1e9))
    return "<br>".join("%s. [%s] %s" % (r["id"], r["type"], r["text"].strip()) for r in items)


def run_result_numbered(raw):
    out = []
    for line in str(raw).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        num = parts[0].rstrip("：:.、")
        rest = parts[1] if len(parts) > 1 else ""
        out.append("%s. %s" % (num, rest))
    return "<br>".join(out)


def cell(v):
    return str(v).replace("\n", "<br>")


def table(rows):
    return "\n".join(["| 字段 | 值 |", "|---|---|"] + ["| %s | %s |" % (k, cell(v)) for k, v in rows])


def generate(pkg: Path):
    data = tomllib.loads((pkg / "task.toml").read_text(encoding="utf-8"))
    ins = (pkg / "instruction.md").read_text(encoding="utf-8").strip()
    rubric = rubric_numbered(pkg / "tests" / "nl_rubric.yaml")
    run = run_result_numbered(data.get("run_result", ""))
    notes = data.get("notes", "")
    m = re.search(r"https://github\.com/[^/\s]+/[^/\s]+/commit/[0-9a-f]{40}", notes)
    fork_commit = m.group(0) if m else "（需提交人补填）"
    precheck = re.search(r"查重记录[^。]*。", notes)
    precheck = precheck.group(0) if precheck else ""

    g_base = [
        ("题目名称", data.get("title", "")),
        ("提交人", "（提交人，请自行在底稿圈人）"),
        ("提交日期", data.get("submit_date", "")),
        ("主要语言", data.get("language", "")),
        ("任务类型", data.get("task_type", "")),
        ("Repo URL", data.get("repo_url", "")),
        ("Commit/版本", data.get("base_commit", "")),
        ("Fork Repo Commit URL", fork_commit),
        ("需求预检记录", precheck),
    ]
    g_content = [
        ("需求 Prompt（原文）", ins),
        ("Verify Rubric", rubric),
        ("真实性与难度说明", data.get("realism_and_difficulty", "")),
        ("可能涉及模块", data.get("modules", "")),
        ("备注", notes),
        ("交付包（zip）", "（本流程不自动打包，由提交人按底稿要求自行上传）"),
    ]
    g_run = [
        ("Trae Session ID", data.get("trae_session_id", "")),
        ("有效轮数", str(data.get("effective_turns", ""))),
        ("Harness", data.get("harness", "")),
        ("Seed 模型/版本", data.get("seed_model", "")),
        ("是否完成需求", data.get("requirement_met", "")),
        ("产物结果", run),
        ("产物截图", "（提交人自行在底稿附 evidence/screenshots/validation.png）"),
        ("运行轨迹", "（提交人自行在底稿附 evidence/trajectory.md）"),
    ]

    doc = f"""# 底稿必填字段（{pkg.name}）

> 说明：本机无 lark-cli / 无 auth login，toml2base.py 无法回填，采用人工回填。
> 请按下列字段逐项复制到底稿「底稿-Harbor 交付（试行）」表。多行内容用 <br> 展开。
> Verify Rubric 与产物结果均按 1. / 2. / 3. 编号逐条对应。

## 基础与仓库信息

{table(g_base)}

## 出题内容与产物

{table(g_content)}

## 运行记录

{table(g_run)}

## 其它

- 质检列（Reviewer / 静态内容是否通过质检 / 题目是否可运行 / 质检备注）由质检填写，提交人不用管。
"""
    (pkg / "docs").mkdir(exist_ok=True)
    (pkg / "docs" / "底稿必填字段.md").write_text(doc, encoding="utf-8")
    return pkg.name


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: gen_basefields.py <题目目录1> [<题目目录2> ...]", file=sys.stderr)
        sys.exit(2)
    for d in sys.argv[1:]:
        print("[%s] 已生成 docs/底稿必填字段.md（1. 编号格式）" % generate(Path(d)))
