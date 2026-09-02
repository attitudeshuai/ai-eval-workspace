#!/usr/bin/env python3
"""
为 SWE-like 项目生成任务目录骨架（swe-like 专用）。

给定一个 repo 名，为 {repo}-01/02/03 三个分支各生成一个任务目录，
并创建空的 task.md / meta.json / verify-rubric.md / session.md。
其中 session.md 默认创建为空文件，供 02 运行记录阶段粘贴 Trae 完整会话，
用于步数统计（终端命令不落盘，从 session.md 逐条数，见 skills/02-step-count.md）。

配置：
- 非敏感配置在 projects/swe-like/config.toml（[paths].work_root / [sessions].active）

用法：
    python create_task.py --repo <repo> [--session <session>] [--work-root <root>] [--dry-run]

依赖：仅标准库（Python 3.11+，需 tomllib）
"""

import argparse
import sys
import tomllib
from pathlib import Path

# 脚本位于 <workspace>/scripts/swe-like/，向上 3 级即工作台根目录
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = WORKSPACE_ROOT / "projects" / "swe-like"

# 每个任务目录默认创建的空文件骨架
SKELETON_FILES = ["task.md", "meta.json", "verify-rubric.md", "session.md"]


def load_config():
    config_path = PROJECT_DIR / "config.toml"
    if not config_path.exists():
        print(f"错误：config.toml 不存在：{config_path}")
        sys.exit(1)
    return tomllib.loads(config_path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(
        description="生成 SWE-like 任务目录骨架（含空 session.md）"
    )
    ap.add_argument("--repo", required=True, help="仓库名（如 flask），生成 {repo}-01/02/03 三个任务目录")
    ap.add_argument("--session", default=None, help="会话（批次）名，默认取 config.toml [sessions].active")
    ap.add_argument("--work-root", default=None, help="工作根目录，默认取 config.toml [paths].work_root（相对工作台根）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将创建的目录与文件，不实际创建")
    args = ap.parse_args()

    cfg = load_config()
    session = args.session or cfg.get("sessions", {}).get("active")
    work_root = args.work_root or cfg.get("paths", {}).get("work_root")
    if not session or not work_root:
        print("错误：session 或 work_root 未配置（config.toml [sessions].active / [paths].work_root）")
        sys.exit(1)

    # work_root 相对工作台根解析（config.toml 约定「所有路径以 ai-eval-workspace 为基准」）
    root = Path(work_root)
    if not root.is_absolute():
        root = WORKSPACE_ROOT / root

    base = (root / session / "tasks" / args.repo).resolve()

    for i in (1, 2, 3):
        task_dir = base / f"{args.repo}-0{i}"
        print(f"{task_dir}/")
        for fname in SKELETON_FILES:
            path = task_dir / fname
            marker = "  [dry-run] " if args.dry_run else "  创建 "
            print(f"{marker}{fname}")
            if not args.dry_run:
                task_dir.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.write_text("", encoding="utf-8")

    if args.dry_run:
        print("\n[dry-run] 未实际创建。")
    else:
        print("\n已生成 3 个任务目录，各含空 session.md。请在 task.md / meta.json / verify-rubric.md 填入内容。")


if __name__ == "__main__":
    main()
