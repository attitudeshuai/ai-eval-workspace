#!/usr/bin/env python3
"""
打包 Web Dev 任务的最终交付资产。

交付包结构：
    deliverables/<task-id>/
    ├── task.md              # 任务需求
    ├── metadata.json        # 任务元数据
    ├── README.md            # 启动与测试说明
    ├── rubric.json          # 验收标准
    ├── target_states.md     # 关键状态说明
    ├── sota-run.md          # SOTA 运行记录
    ├── assets/              # 参考截图与素材
    ├── mock-data/           # mock 数据
    ├── tests/               # Playwright / 单元测试骨架
    ├── screenshots/         # 占位目录
    └── sota/                # SOTA 产物
        ├── source/          # 从远端拉下来的修改后源码
        ├── screenshots/     # agent 输出的关键状态截图
        ├── sota.log         # 运行日志
        ├── PROMPT.md        # 使用的提示词
        └── report/          # 评估报告
            ├── report.json
            └── report.md

用法：
    python scripts/package_deliverable.py \
      --task webdev-task-01.01 \
      --session session-sota-2026-07-01.01-codex \
      --agent codex
"""

import argparse
import shutil
import tarfile
from pathlib import Path

from utils.helpers import find_task_dir, project_dir, workspace_root


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

    session_dir = ws / "sessions" / session / "projects" / project_id
    submission_dir = session_dir / "submissions" / task_id / agent
    report_dir = session_dir / "reports" / task_id / agent

    if not submission_dir.exists():
        raise FileNotFoundError(f"找不到 SOTA 产物: {submission_dir}")

    project_output_dir = ws / output_dir / project_id
    project_output_dir.mkdir(parents=True, exist_ok=True)

    deliverable_dir = project_output_dir / task_id
    if deliverable_dir.exists():
        shutil.rmtree(deliverable_dir)
    deliverable_dir.mkdir(parents=True, exist_ok=False)

    # 1. 复制任务资产
    task_assets = [
        "task.md",
        "metadata.json",
        "README.md",
        "rubric.json",
        "target_states.md",
        "sota-run.md",
    ]
    for name in task_assets:
        src = task_dir / name
        if src.exists():
            shutil.copy2(src, deliverable_dir / name)

    for name in ["assets", "mock-data", "tests"]:
        src = task_dir / name
        if src.exists():
            dst = deliverable_dir / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    # 2. 复制 SOTA 产物
    sota_dir = deliverable_dir / "sota"
    sota_dir.mkdir(parents=True, exist_ok=True)

    # source/：从远端拉下来的修改后源码
    source_dir = submission_dir / "source"
    if source_dir.exists():
        shutil.copytree(source_dir, sota_dir / "source")

    # screenshots/：agent 输出的截图
    screenshots_dir = submission_dir / "source" / "screenshots"
    if screenshots_dir.exists():
        shutil.copytree(screenshots_dir, sota_dir / "screenshots")

    # sota.log
    sota_log = submission_dir / "sota.log"
    if sota_log.exists():
        shutil.copy2(sota_log, sota_dir / "sota.log")

    # PROMPT.md
    prompt_file = submission_dir / "PROMPT.md"
    if prompt_file.exists():
        shutil.copy2(prompt_file, sota_dir / "PROMPT.md")

    # report/
    if report_dir.exists():
        shutil.copytree(report_dir, sota_dir / "report")

    # 3. 打包
    tar_path = project_output_dir / f"{task_id}.tar.gz"
    if tar_path.exists():
        tar_path.unlink()

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(deliverable_dir, arcname=task_id)

    # 4. 仅保留 tar.gz，删除中间解压目录
    shutil.rmtree(deliverable_dir)

    return tar_path


def main():
    parser = argparse.ArgumentParser(description="打包 Web Dev 任务最终交付资产")
    parser.add_argument("--task", required=True, help="任务 ID，例如 webdev-task-01.01")
    parser.add_argument("--session", required=True, help="Session 名称")
    parser.add_argument("--agent", default="codex", help="Agent 名称，默认 codex")
    parser.add_argument("--project", default="webdev-long-horizon", help="项目 ID")
    parser.add_argument("--output", default="deliverables", help="输出目录，默认 deliverables/")
    args = parser.parse_args()

    tar_path = package_deliverable(
        args.task,
        args.session,
        args.agent,
        args.project,
        args.output,
    )
    print(f"交付包已生成: {tar_path}")


if __name__ == "__main__":
    main()
