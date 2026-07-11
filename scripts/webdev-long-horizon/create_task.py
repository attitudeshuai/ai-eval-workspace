#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
    load_json,
    load_toml,
    project_dir,
    render_template,
    resolve_template,
    save_json,
    sources_dir,
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


def inherit_from_parent(
    project_id: str,
    task_dir: Path,
    task_id: str,
    parent_id: str,
) -> dict[str, Path]:
    """增量任务继承父任务资产：源码、mock-data、目录结构。

    目录约定：
    - 任务：tasks/<family>/<task-id>/
    - 源码：sources/<family>/<task-id>/

    返回创建/复制的关键路径字典。
    """
    created: dict[str, Path] = {}

    # 1. 父任务目录（层级结构：tasks/<family>/<parent-id>/）
    parent_task_dir = find_task_dir(project_id, parent_id)
    if parent_task_dir is None:
        raise FileExistsError(f"父任务目录不存在: {parent_id}")

    # family 目录名与 tasks/<family>/ 一致
    family_name = parent_task_dir.parent.name
    sd = sources_dir(project_id)
    family_source_dir = sd / family_name

    # 2. 父任务源码 -> 子任务源码（sources/<family>/<task-id>/）
    parent_source_dir = family_source_dir / parent_id
    if parent_source_dir.is_dir():
        child_source_dir = family_source_dir / task_id
        copy_tree(parent_source_dir, child_source_dir)
        created["source_dir"] = child_source_dir

        # 同时生成 source 专属 README（提示这是增量任务的 baseline）
        source_readme = child_source_dir / "README.md"
        if not source_readme.exists():
            source_readme.write_text(
                f"# {task_id} 初始源码\n\n"
                f"本目录为 `{parent_id}` 的源码副本，作为 `{task_id}` 增量开发的 baseline。\n"
                "请根据任务需求在此基础上完成新增功能。\n",
                encoding="utf-8",
            )

    # 3. 父任务 mock-data -> 子任务 mock-data
    parent_mock = parent_task_dir / "mock-data"
    if parent_mock.is_dir():
        child_mock_task = task_dir / "mock-data"
        copy_tree(parent_mock, child_mock_task)
        created["mock_data_task"] = child_mock_task

        # 同步到 source 目录
        if "source_dir" in created:
            child_mock_source = created["source_dir"] / "mock-data"
            copy_tree(parent_mock, child_mock_source)
            created["mock_data_source"] = child_mock_source

    # 4. 父任务 assets -> 子任务 assets（增量任务视觉风格通常继承父任务）
    parent_assets = parent_task_dir / "assets"
    if parent_assets.is_dir():
        child_assets = task_dir / "assets"
        copy_tree(parent_assets, child_assets)
        created["assets_dir"] = child_assets

    # 5. 创建 assets/ 占位说明（若尚未创建）
    assets_dir = task_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    reference_dir = assets_dir / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    assets_readme = assets_dir / "README.md"
    if not assets_readme.exists():
        assets_readme.write_text(
            "# 任务素材说明\n\n"
            "本目录存放任务所需素材，按子目录组织：\n\n"
            "```text\n"
            "assets/\n"
            "└── reference/           # 参考截图（人工准备，供 agent 视觉还原使用）\n"
            "    ├── desktop.png      # 桌面端完整页面参考\n"
            "    ├── mobile.png       # 移动端完整页面参考\n"
            "    ├── empty_state.png  # 空状态参考\n"
            "    └── interaction_state.png  # 交互状态参考\n"
            "```\n\n"
            "> 其他任务若有图标、字体、示例图片等素材，可继续在 `assets/` 下新增子目录，\n"
            "> 例如 `assets/icons/`、`assets/fonts/`、`assets/images/`。\n\n"
            "## 截图规范\n\n"
            "- 桌面端截图宽度：1920px\n"
            "- 移动端截图宽度：390px\n"
            "- 参考图仅用于布局和视觉风格对齐，不照搬品牌资产\n",
            encoding="utf-8",
        )
    created["assets_dir"] = assets_dir

    # 5. 创建 screenshots/ 目录
    screenshots_dir = task_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    created["screenshots_dir"] = screenshots_dir

    return created


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

    # 创建通用任务目录：assets/（含 reference/）、screenshots/
    assets_dir = task_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    reference_dir = assets_dir / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    assets_readme = assets_dir / "README.md"
    if not assets_readme.exists():
        assets_readme.write_text(
            "# 任务素材说明\n\n"
            "本目录存放任务所需素材，按子目录组织：\n\n"
            "```text\n"
            "assets/\n"
            "└── reference/           # 参考截图（人工准备，供 agent 视觉还原使用）\n"
            "    ├── desktop.png      # 桌面端完整页面参考\n"
            "    ├── mobile.png       # 移动端完整页面参考\n"
            "    ├── empty_state.png  # 空状态参考\n"
            "    └── interaction_state.png  # 交互状态参考\n"
            "```\n\n"
            "> 其他任务若有图标、字体、示例图片等素材，可继续在 `assets/` 下新增子目录，\n"
            "> 例如 `assets/icons/`、`assets/fonts/`、`assets/images/`。\n\n"
            "## 截图规范\n\n"
            "- 桌面端截图宽度：1920px\n"
            "- 移动端截图宽度：390px\n"
            "- 参考图仅用于布局和视觉风格对齐，不照搬品牌资产\n",
            encoding="utf-8",
        )
    screenshots_dir = task_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # 增量任务：继承父任务资产
    inherited: dict[str, Path] = {}
    if parent and skip_starter:
        inherited = inherit_from_parent(project_id, task_dir, task_id, parent)
        # 在 metadata.json 中写入 parent_tasks
        metadata_path = task_dir / "metadata.json"
        if metadata_path.exists():
            metadata = load_json(metadata_path)
            metadata.setdefault("parent_tasks", []).append(parent)
            save_json(metadata_path, metadata)

    return task_dir, inherited


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
    task_dir, inherited = create_task(
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
        print("  - (未生成 starter)")

    if inherited:
        print("\n已继承父任务资产：")
        for name, path in inherited.items():
            print(f"  - {name}: {path}")
        if "source_dir" not in inherited:
            print("\n⚠️ 未找到父任务外部源码，请手动放到项目约定的 source 目录。")


if __name__ == "__main__":
    main()
