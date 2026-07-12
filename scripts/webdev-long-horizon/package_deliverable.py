#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
打包 Web Dev 任务的最终交付资产。

交付包结构（严格遵循高难度 Web Dev 长程任务数据采购需求 Draft 的附录建议）：
    deliverables/<task-id>/
    ├── task.md              # 任务需求
    ├── metadata.json        # 任务元数据
    ├── README.md            # 启动与测试说明
    ├── rubric.json          # 验收标准
    ├── target_states.md     # 关键状态说明
    ├── sota-run.md          # SOTA 运行记录
    ├── starter/             # 初始项目代码
    ├── assets/              # 参考截图与素材
    ├── mock-data/           # mock 数据
    ├── tests/               # Playwright / 单元测试骨架
    └── screenshots/         # 人工验证后放置的关键状态截图（可选）

用法：
    python scripts/webdev-long-horizon/package_deliverable.py \
      --task webdev-task-sxw-01.01 \
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

    session_dir = ws / "sessions" / project_id / session
    submission_dir = session_dir / "submissions" / task_id / task_id

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

    for name in ["assets", "mock-data", "tests", "screenshots"]:
        src = task_dir / name
        if src.exists() and any(src.iterdir()):
            dst = deliverable_dir / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    # 2. 复制初始源码 baseline 到 starter/
    #    对于增量任务，这是从父任务继承的 source；对于 Greenfield，这是空目录。
    family = task_dir.parent.name
    baseline_dir = project_dir(project_id) / "sources" / family / task_id
    starter_dir = deliverable_dir / "starter"
    if baseline_dir.exists() and any(baseline_dir.iterdir()):
        shutil.copytree(baseline_dir, starter_dir)
    else:
        starter_dir.mkdir(parents=True, exist_ok=True)
        # 保留空目录占位，方便 tar 打包
        (starter_dir / ".gitkeep").write_text("", encoding="utf-8")

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
    parser.add_argument("--task", required=True, help="任务 ID，例如 webdev-task-sxw-01.01")
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
