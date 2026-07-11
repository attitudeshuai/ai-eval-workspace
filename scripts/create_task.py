#!/usr/bin/env python3
"""在指定项目下创建新任务。使用项目级模板（项目自治）。

支持层级任务 ID 与层级目录结构：
- 顶层任务：tasks/webdev-task-01/webdev-task-01/
- 子任务：tasks/webdev-task-01/webdev-task-01.01/
- 孙任务：tasks/webdev-task-01/webdev-task-01.01/webdev-task-01.01.01/
"""

import argparse
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from utils.helpers import (
    copy_tree,
    find_task_dir,
    load_toml,
    project_dir,
    render_template,
    resolve_template,
    task_prefix,
)


def parse_task_id(task_id: str, prefix: str) -> tuple[str, list[int]]:
    """解析任务 ID，返回 (prefix, [层级序号])。

    例如：
    - webdev-task-01        -> ("webdev-task", [1])
    - webdev-task-01.02     -> ("webdev-task", [1, 2])
    - webdev-task-01.02.03  -> ("webdev-task", [1, 2, 3])
    """
    pattern = rf"^{re.escape(prefix)}-(\d+(?:\.\d+)*)$"
    match = re.match(pattern, task_id)
    if not match:
        raise ValueError(f"非法任务 ID 格式: {task_id}，应为 {prefix}-NN 或 {prefix}-NN.NN")
    indices = [int(x) for x in match.group(1).split(".")]
    return prefix, indices


def format_task_id(prefix: str, indices: list[int]) -> str:
    """将层级序号格式化为任务 ID。"""
    return f"{prefix}-{'.'.join(f'{i:02d}' for i in indices)}"


def find_next_task_id(tasks_dir: Path, prefix: str, parent_id: str | None = None) -> str:
    """根据现有任务确定下一个任务 ID。"""
    existing_ids = []

    def collect(path: Path):
        for item in path.iterdir():
            if not item.is_dir():
                continue
            matched = False
            try:
                _, indices = parse_task_id(item.name, prefix)
                existing_ids.append(indices)
                matched = True
            except ValueError:
                pass
            # 即使目录名本身是任务 ID，也继续递归，
            # 因为层级结构下任务目录内可能还包含子任务目录。
            collect(item)

    collect(tasks_dir)

    if parent_id is None:
        # 顶层任务：找 [N] 中的最大值
        top_indices = [idx for idx in existing_ids if len(idx) == 1]
        next_top = max([i[0] for i in top_indices], default=0) + 1
        return format_task_id(prefix, [next_top])

    # 子任务：基于 parent_id 的层级
    _, parent_indices = parse_task_id(parent_id, prefix)
    child_depth = len(parent_indices) + 1
    max_child = 0
    for indices in existing_ids:
        if len(indices) == child_depth and indices[:-1] == parent_indices:
            max_child = max(max_child, indices[-1])
    next_child = max_child + 1
    return format_task_id(prefix, parent_indices + [next_child])


def determine_task_dir(tasks_dir: Path, task_id: str, parent_id: str | None = None) -> Path:
    """确定任务目录位置（层级结构）。"""
    if parent_id is None:
        # 顶层任务：tasks/<task-id>/<task-id>/
        return tasks_dir / task_id / task_id

    # 子任务：在父任务目录的父目录下创建
    parent_dir = find_task_dir(project_id_from_path(tasks_dir), parent_id)
    if parent_dir is None:
        raise FileExistsError(f"父任务不存在: {parent_id}")
    return parent_dir.parent / task_id


def project_id_from_path(tasks_dir: Path) -> str:
    """从 tasks/ 目录路径推断项目 ID。"""
    # tasks_dir = workspace_root/projects/<project-id>/tasks
    return tasks_dir.parent.name


def create_task(
    project_id: str,
    title: str,
    category: str,
    difficulty: str,
    arena_tags: list[str],
    prompt_type: str = "前端",
    skip_starter: bool = False,
    parent: str | None = None,
) -> Path:
    pd = project_dir(project_id)
    if not pd.exists():
        raise FileExistsError(f"项目不存在: {pd}")

    config = load_toml(pd / "config.toml")
    prefix = config.get("project", {}).get("task_prefix", f"{project_id}-task")

    tasks_dir_path = pd / "tasks"

    task_id = find_next_task_id(tasks_dir_path, prefix, parent)
    task_dir = determine_task_dir(tasks_dir_path, task_id, parent)
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

    if not skip_starter:
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
    parser.add_argument(
        "--skip-starter",
        action="store_true",
        help="不复制 starter 模板；源码可由用户后续放到 projects/<project>/sources/<task-id>/",
    )
    parser.add_argument(
        "--parent",
        help="父任务 ID（如 webdev-task-01），创建子任务时会生成 webdev-task-01.01",
    )
    args = parser.parse_args()

    arena_tags = [t.strip() for t in args.arena_tags.split(",") if t.strip()]
    task_dir = create_task(
        args.project,
        args.title,
        args.category,
        args.difficulty,
        arena_tags,
        args.prompt_type,
        skip_starter=args.skip_starter,
        parent=args.parent,
    )
    print(f"已创建任务: {task_dir}")
    print(f"  - {task_dir / 'task.md'}")
    print(f"  - {task_dir / 'metadata.json'}")
    if not args.skip_starter:
        print(f"  - {task_dir / 'starter'}")
        print("提示：如果 starter 使用 npm，请手动进入目录执行 npm install 生成 lockfile。")
    else:
        print("  - (未生成 starter，请自行提供源码并放到项目约定的 source 目录)")


if __name__ == "__main__":
    main()
