#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
打包 Web Dev 任务的最终交付资产。

交付包结构：
    deliverables/<project-id>/<task-id>/
    ├── task.md              # 任务需求
    ├── metadata.json        # 任务元数据
    ├── README.md            # 启动与测试说明（含已知限制章节）
    ├── .ignore              # 忽略规则
    ├── starter/             # 初始项目代码（Greenfield 含 .gitkeep）
    ├── assets/              # 参考截图与素材
    ├── mock-data/           # mock 数据
    ├── tests/               # Playwright / 单元测试骨架
    ├── rubric.json          # 验收标准
    ├── target_states.md     # 关键状态说明
    ├── trajectory.jsonl     # codex rollout 轨迹（最新的单次运行）
    └── screenshots/         # 关键状态截图

输出为文件夹，不再打包 tar.gz。

用法：
    python scripts/webdev-long-horizon/package_deliverable.py \
      --task webdev-task-sxw-01.01 \
      --session session-sota-2026-07-01.01-codex \
      --agent codex
"""

import argparse
import os
import shutil
from pathlib import Path

from utils.helpers import find_task_dir, project_dir, workspace_root

IGNORE_CONTENT = """# Dependencies
node_modules/
.pnp
.pnp.js

# Build
dist/
build/
target/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Env
.env
.env.local
.env.*.local

# Logs
*.log
"""


def package_deliverable(
    task_id: str,
    session: str,
    agent: str,
    project_id: str = "webdev-long-horizon",
    output_dir: str = "deliverables",
) -> Path:
    ws = workspace_root()
    task_dir = find_task_dir(project_id, task_id)
    if task_dir is None:
        raise FileNotFoundError(f"找不到任务: {task_id}")

    session_dir = ws / "sessions" / project_id / session
    submission_dir = session_dir / "submissions" / task_id

    if not submission_dir.exists():
        raise FileNotFoundError(f"找不到 SOTA 产物: {submission_dir}")

    project_output_dir = ws / output_dir / project_id
    project_output_dir.mkdir(parents=True, exist_ok=True)

    deliverable_dir = project_output_dir / task_id
    if deliverable_dir.exists():
        shutil.rmtree(deliverable_dir)
    deliverable_dir.mkdir(parents=True, exist_ok=False)

    # 1. 复制任务资产（不含 sota-run.md）
    task_assets = [
        "task.md",
        "metadata.json",
        "README.md",
        "rubric.json",
        "target_states.md",
    ]
    for name in task_assets:
        src = task_dir / name
        if src.exists():
            shutil.copy2(src, deliverable_dir / name)

    for name in ["assets", "mock-data", "tests"]:
        src = task_dir / name
        if src.exists() and any(src.iterdir()):
            dst = deliverable_dir / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    # 2. 复制 SOTA 截图
    sota_screenshots = submission_dir / "screenshots"
    dst_screenshots = deliverable_dir / "screenshots"
    if sota_screenshots.exists() and any(sota_screenshots.iterdir()):
        if dst_screenshots.exists():
            shutil.rmtree(dst_screenshots)
        shutil.copytree(sota_screenshots, dst_screenshots)
    else:
        dst_screenshots.mkdir(parents=True, exist_ok=True)

    # 3. 复制最新的 trajectory rollout 文件
    trajectory_dir = session_dir / "trajectory"
    if trajectory_dir.exists():
        rollout_files = sorted(trajectory_dir.glob("rollout*.jsonl"))
        if rollout_files:
            shutil.copy2(rollout_files[-1], deliverable_dir / "trajectory.jsonl")
        else:
            print(f"  注意：未找到 rollout 文件 ({trajectory_dir})")
    else:
        print(f"  注意：未找到 trajectory 目录 ({trajectory_dir})")

    # 4. 初始源码 baseline 到 starter/
    family = task_dir.parent.name
    baseline_dir = project_dir(project_id) / "sources" / family / task_id
    starter_dir = deliverable_dir / "starter"
    if baseline_dir.exists() and any(baseline_dir.iterdir()):
        shutil.copytree(baseline_dir, starter_dir)
    else:
        starter_dir.mkdir(parents=True, exist_ok=True)
        (starter_dir / ".gitkeep").write_text("", encoding="utf-8")

    # 5. 生成 .ignore 文件
    (deliverable_dir / ".ignore").write_text(IGNORE_CONTENT, encoding="utf-8")

    return deliverable_dir


def main():
    parser = argparse.ArgumentParser(description="打包 Web Dev 任务最终交付资产")
    parser.add_argument("--task", required=True, help="任务 ID，例如 webdev-task-sxw-01.01")
    parser.add_argument("--session", required=True, help="Session 名称")
    parser.add_argument("--agent", default="codex", help="Agent 名称，默认 codex")
    parser.add_argument("--project", default="webdev-long-horizon", help="项目 ID")
    parser.add_argument("--output", default="deliverables", help="输出目录，默认 deliverables/")
    args = parser.parse_args()

    deliverable_dir = package_deliverable(
        args.task,
        args.session,
        args.agent,
        args.project,
        args.output,
    )
    print(f"交付文件夹已生成: {deliverable_dir}")


if __name__ == "__main__":
    main()
