#!/usr/bin/env python3
"""
为 SWE-like 项目生成任务目录骨架（swe-like 专用，伪 Harbor 格式）。

给定 repo 名，按 config.toml [task].max_tasks_per_repo 的上限补齐
{repo}-01 … {repo}-{NN} 任务目录（已存在的目录跳过，不覆盖）。
每个目录含：task.toml（预填 title/submit_date/repo_url）、instruction.md（空）、
environment/Dockerfile、tests/nl_rubric.yaml、solution/、evidence/screenshots/。

配置：
- 非敏感配置在 projects/swe-like/config.toml（[paths].work_root / [sessions].active / [task].max_tasks_per_repo）

用法：
    python create_task.py --repo <repo> [--repo-url <url>] [--session <session>] [--work-root <root>] [--dry-run]

依赖：仅标准库（Python 3.11+，需 tomllib）
"""

import argparse
import datetime
import sys
import tomllib
from pathlib import Path

# 脚本位于 <workspace>/scripts/swe-like/，向上 3 级即工作台根目录
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = WORKSPACE_ROOT / "projects" / "swe-like"
TEMPLATE_DIR = PROJECT_DIR / "templates" / "harbor"

TASK_TOML_TEMPLATE = '''# harbor 交付包 · task.toml（16 键，与底稿列一一对应；不要自行增删或改名）
# 状态：题目创建中。标记 [待运行] / [待验收] 的键在第 2 / 3 步回填。

title       = "{title}"     # 题目名称（与交付包目录名一致）
submitter   = ""            # 提交人（脚本不回填，底稿里圈自己）
submit_date = "{today}"     # YYYY-MM-DD
language    = "Go"          # 本批次只可填 Python / Go
task_type   = "功能新增"     # 功能新增 / Bug 修复 / 测试增强 / 重构/性能 / 配置/工具链 / 其他
repo_url    = "{repo_url}"
base_commit = ""            # 40 位完整 SHA，须与 Dockerfile 的 ARG BASE_SHA 一致

realism_and_difficulty = """
真实性与难度说明写在这里。
"""

modules = ""                # 可能涉及模块

trae_session_id = ""         # [待运行] 原文复制，miniswe 可留空
effective_turns = 0          # [待运行] 有效轮数（agent step 口径，环境重试不计入）
harness         = "TraeX"    # Trae / TraeX / miniswe
seed_model      = "Seed Evolving"
requirement_met = "无法判断" # [待验收] 完成 / 部分完成 / 未完成 / 无法判断

run_result = ""              # [待验收] 逐条对应 rubric：id + 通过/未通过 + 未通过原因

notes = ""
'''

NL_RUBRIC_TEMPLATE = '''# nl_rubric.yaml（自然语言判分标准）
# 至少 5 条；type 只能 f2p / p2p；至少各含 1 条 f2p 和 1 条 p2p。
# 每条一句自然语言，不写死文件名/类名/实现方案。
# 验收前固定，评判口径一致，不得根据模型结果事后调整。

rubrics:
  - id: 1
    type: f2p
    text: ""

  - id: 2
    type: f2p
    text: ""

  - id: 3
    type: f2p
    text: ""

  - id: 4
    type: f2p
    text: ""

  - id: 5
    type: p2p
    text: ""
'''

DOCKERFILE_TEMPLATE = '''FROM public.ecr.aws/x8v8d7g8/mars-base:latest
WORKDIR /app

# BASE_SHA 必须与 task.toml 的 base_commit 完全一致（40 位完整 SHA）
ARG REPO_URL={repo_url}
ARG BASE_SHA=
RUN git clone "$REPO_URL" . \\
 && DEFAULT="$(git remote show origin | sed -n 's/.*HEAD branch: //p')" \\
 && git checkout -B "$DEFAULT" "$BASE_SHA" \\
 && git remote remove origin \\
 && for b in $(git for-each-ref --format='%(refname:short)' refs/heads | grep -vx "$DEFAULT"); do git branch -D "$b" || true; done \\
 && for t in $(git tag); do git merge-base --is-ancestor "$t" HEAD 2>/dev/null || git tag -d "$t"; done \\
 && git reflog expire --expire=now --all \\
 && git gc --prune=now

# 装本仓库依赖，含本题需求新增的依赖；能钉版本就钉。
# Python:  RUN pip install --no-cache-dir -e ".[all]"
# Go:      RUN go mod download

CMD ["bash"]
'''


def load_config():
    config_path = PROJECT_DIR / "config.toml"
    if not config_path.exists():
        print(f"错误：config.toml 不存在：{config_path}")
        sys.exit(1)
    return tomllib.loads(config_path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description="生成 SWE-like harbor 任务目录骨架（补齐到 max_tasks_per_repo）")
    ap.add_argument("--repo", required=True, help="仓库名（如 caddy）")
    ap.add_argument("--repo-url", default="", help="原始仓库 URL，预填 task.toml 与 Dockerfile")
    ap.add_argument("--session", default=None, help="会话（批次）名，默认取 config.toml [sessions].active")
    ap.add_argument("--work-root", default=None, help="工作根目录，默认取 config.toml [paths].work_root（相对工作台根）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将创建的目录与文件，不实际创建")
    args = ap.parse_args()

    cfg = load_config()
    session = args.session or cfg.get("sessions", {}).get("active")
    work_root = args.work_root or cfg.get("paths", {}).get("work_root")
    max_tasks = int(cfg.get("task", {}).get("max_tasks_per_repo", 3))
    if not session or not work_root:
        print("错误：session 或 work_root 未配置（config.toml [sessions].active / [paths].work_root）")
        sys.exit(1)

    root = Path(work_root)
    if not root.is_absolute():
        root = WORKSPACE_ROOT / root
    base = (root / session / "tasks" / args.repo).resolve()
    today = datetime.date.today().isoformat()

    created = 0
    for i in range(1, max_tasks + 1):
        task_dir = base / f"{args.repo}-{i:02d}"
        if task_dir.exists():
            print(f"  跳过（已存在） {task_dir}")
            continue
        created += 1
        files = {
            "task.toml": TASK_TOML_TEMPLATE.format(title=task_dir.name, today=today, repo_url=args.repo_url),
            "instruction.md": "",
            "environment/Dockerfile": DOCKERFILE_TEMPLATE.format(repo_url=args.repo_url),
            "tests/nl_rubric.yaml": NL_RUBRIC_TEMPLATE,
        }
        print(f"{task_dir}/")
        for rel, content in files.items():
            print(f"  {'[dry-run]' if args.dry_run else '创建'} {rel}")
            if not args.dry_run:
                p = task_dir / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
        for d in ("solution", "evidence/screenshots"):
            print(f"  {'[dry-run]' if args.dry_run else '创建'} {d}/")
            if not args.dry_run:
                (task_dir / d).mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print(f"\n[dry-run] 未实际创建。将新建 {created} 个任务目录（上限 {max_tasks}）。")
    else:
        print(f"\n已新建 {created} 个任务目录（上限 {max_tasks}，已存在的不动）。请填写 task.toml / instruction.md / nl_rubric.yaml。")


if __name__ == "__main__":
    main()
