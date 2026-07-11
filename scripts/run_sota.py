#!/usr/bin/env python3
"""为指定任务创建 SOTA 运行会话与 Prompt。直接使用 task.md 作为提示词。"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from utils.helpers import (
    copy_tree,
    find_source_dir,
    find_task_dir,
    is_task_dir,
    project_dir,
    workspace_root,
)


def build_prompt(task_dir: Path) -> str:
    task_md = (task_dir / "task.md").read_text(encoding="utf-8")

    # 默认通用 Prompt
    readme_sources = [
        task_dir / "starter" / "README.md",
        task_dir / "README.md",
    ]
    readme = ""
    for src in readme_sources:
        if src.exists():
            readme = src.read_text(encoding="utf-8")
            break

    return f"""# 任务需求

{task_md}

## 起始项目

项目代码已位于 `./source`。请先阅读项目结构，按 README 启动并完成任务。

```bash
cd source
# 根据项目 README 安装依赖并启动
```

## 交付要求

1. 在 `./source` 中完成所有代码修改。
2. 按任务要求保存关键截图、测试结果等到 `./screenshots/`。
3. 不修改本任务原始目录中的任何文件。

## 项目 README

{readme}
"""


def resolve_task_dir(project_id: str, task_arg: str) -> Path:
    """解析 --task 参数为任务目录。

    支持：
    1. 完整路径
    2. task_id（自动在项目下递归查找）
    3. 相对 tasks 根的路径
    """
    path = Path(task_arg)
    if path.is_absolute() and is_task_dir(path):
        return path

    # 相对 tasks 根的路径
    project_tasks_dir = project_dir(project_id) / "tasks"
    candidate = project_tasks_dir / path
    if candidate.exists() and is_task_dir(candidate):
        return candidate

    # task_id 自动查找
    found = find_task_dir(project_id, task_arg)
    if found:
        return found

    raise FileNotFoundError(f"无法找到任务: {task_arg}")


def run_sota(
    session_name: str,
    project_id: str,
    task_dir: Path,
    agent: str,
    source_dir_override: Path | None = None,
) -> Path:
    session_dir = workspace_root() / "sessions" / session_name
    if session_dir.exists():
        raise FileExistsError(f"会话已存在: {session_dir}")

    task_id = task_dir.name
    submission_dir = (
        session_dir / "projects" / project_id / "submissions" / task_id / agent
    )
    source_dir = submission_dir / "source"
    screenshots_dir = submission_dir / "screenshots"

    submission_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # 决定源码来源：外部指定 > 项目默认 sources/<task-id>/ > task/starter
    src_candidates = []
    if source_dir_override:
        src_candidates.append(source_dir_override)
    src_candidates.append(find_source_dir(project_id, task_id))
    src_candidates.append(task_dir / "starter")

    chosen_src = None
    for candidate in src_candidates:
        if candidate and candidate.exists():
            chosen_src = candidate
            break

    if chosen_src:
        copy_tree(chosen_src, source_dir)
    else:
        source_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_prompt(task_dir)
    (submission_dir / "PROMPT.md").write_text(prompt, encoding="utf-8")

    run_script = submission_dir / "run.sh"
    run_script.write_text(
        "#!/bin/bash\nset -e\ncd source\n# 根据项目 README 安装依赖并启动\n",
        encoding="utf-8",
    )

    sota_run = task_dir / "sota-run.md"
    if sota_run.exists():
        content = sota_run.read_text(encoding="utf-8")
        if "## 运行记录" in content:
            now = datetime.now(timezone.utc).isoformat()
            record = f"\n- session: {session_name}\n- agent: {agent}\n- started_at: {now}\n- status: created\n"
            content = content.replace("## 运行记录", "## 运行记录" + record)
            sota_run.write_text(content, encoding="utf-8")

    return submission_dir


def main():
    parser = argparse.ArgumentParser(description="创建 SOTA 运行会话")
    parser.add_argument("--session", required=True, help="会话名称")
    parser.add_argument("--project", required=True, help="项目 ID")
    parser.add_argument("--task", required=True, help="任务目录、相对路径或 task_id")
    parser.add_argument("--agent", default="codex", help="Agent 名称")
    parser.add_argument("--budget", help="预算（仅记录）")
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="指定外部源码目录；否则依次尝试 projects/<project>/sources/<task-id>/ 和 task/starter",
    )
    args = parser.parse_args()

    task_path = resolve_task_dir(args.project, args.task)

    submission_dir = run_sota(
        args.session, args.project, task_path, args.agent, source_dir_override=args.source_dir
    )
    print(f"已创建 SOTA 会话: {submission_dir}")
    print(f"Prompt 文件: {submission_dir / 'PROMPT.md'}")
    print(f"运行脚本: {submission_dir / 'run.sh'}")


if __name__ == "__main__":
    main()
