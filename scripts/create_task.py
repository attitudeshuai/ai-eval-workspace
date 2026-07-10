#!/usr/bin/env python3
"""在指定项目下创建新任务。使用项目级模板（项目自治）。"""

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

from utils.helpers import (
    copy_tree,
    load_toml,
    project_dir,
    render_template,
    resolve_template,
)


def create_task(
    project_id: str,
    title: str,
    category: str,
    difficulty: str,
    arena_tags: list[str],
    prompt_type: str = "前端",
) -> Path:
    pd = project_dir(project_id)
    if not pd.exists():
        raise FileExistsError(f"项目不存在: {pd}")

    config = load_toml(pd / "config.toml")
    prefix = config.get("project", {}).get("task_prefix", f"{project_id}-task")

    tasks_dir = pd / "tasks"
    existing = sorted(tasks_dir.glob(f"{prefix}-*"))
    next_index = len(existing) + 1
    task_id = f"{prefix}-{next_index:04d}"
    task_dir = tasks_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=False)

    now = datetime.now(timezone.utc).isoformat()
    variables = {
        "project_id": project_id,
        "task_id": task_id,
        "title": title,
        "category": category,
        "difficulty": difficulty,
        "arena_tags": arena_tags,
        "prompt_type": prompt_type,
        "created_at": now,
    }

    task_template = resolve_template(project_id, "task")
    if not task_template.exists():
        raise FileNotFoundError(
            f"项目 {project_id} 缺少任务模板，请在 {pd / 'templates' / 'task'} 或 global templates/task 创建。"
        )

    for template_file in task_template.iterdir():
        if template_file.is_file():
            dest = task_dir / template_file.name
            dest.write_text(render_template(template_file, variables), encoding="utf-8")

    starter_template = resolve_template(project_id, "starter")
    if starter_template.exists():
        copy_tree(starter_template, task_dir / "starter")

    return task_dir


def main():
    parser = argparse.ArgumentParser(description="创建新任务")
    parser.add_argument("--project", required=True, help="项目 ID")
    parser.add_argument("--title", required=True, help="任务标题")
    parser.add_argument("--category", required=True, help="任务类别")
    parser.add_argument("--difficulty", default="高", help="难度")
    parser.add_argument("--arena-tags", default="", help="Arena 标签，逗号分隔")
    parser.add_argument("--prompt-type", default="前端", help="提示类型")
    args = parser.parse_args()

    arena_tags = [t.strip() for t in args.arena_tags.split(",") if t.strip()]
    task_dir = create_task(
        args.project,
        args.title,
        args.category,
        args.difficulty,
        arena_tags,
        args.prompt_type,
    )
    print(f"已创建任务: {task_dir}")
    print(f"  - {task_dir / 'task.md'}")
    print(f"  - {task_dir / 'metadata.json'}")
    print(f"  - {task_dir / 'starter'}")
    print("提示：如果 starter 使用 npm，请手动进入目录执行 npm install 生成 lockfile。")


if __name__ == "__main__":
    main()
