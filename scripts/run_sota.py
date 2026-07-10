#!/usr/bin/env python3
"""为指定任务创建 SOTA 运行会话与 Prompt。支持项目级 Prompt 模板覆盖。"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from utils.helpers import copy_tree, project_dir, tasks_dir, workspace_root


def find_prompt_template(project_id: str, task_dir: Path) -> Path | None:
    """查找项目级或任务级 Prompt 模板。"""
    candidates = [
        task_dir / "PROMPT.md",
        project_dir(project_id) / "templates" / "PROMPT.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_prompt(project_id: str, task_dir: Path) -> str:
    task_md = (task_dir / "task.md").read_text(encoding="utf-8")

    template = find_prompt_template(project_id, task_dir)
    if template:
        return template.read_text(encoding="utf-8").replace("{{task_md}}", task_md)

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


def run_sota(session_name: str, project_id: str, task_dir: Path, agent: str) -> Path:
    session_dir = workspace_root() / "sessions" / session_name
    if session_dir.exists():
        raise FileExistsError(f"会话已存在: {session_dir}")

    submission_dir = (
        session_dir / "projects" / project_id / "submissions" / task_dir.name / agent
    )
    source_dir = submission_dir / "source"
    screenshots_dir = submission_dir / "screenshots"

    submission_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    starter_dir = task_dir / "starter"
    if starter_dir.exists():
        copy_tree(starter_dir, source_dir)

    prompt = build_prompt(project_id, task_dir)
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
    parser.add_argument("--task", required=True, help="任务目录或 ID")
    parser.add_argument("--agent", default="codex", help="Agent 名称")
    parser.add_argument("--budget", help="预算（仅记录）")
    args = parser.parse_args()

    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = tasks_dir(args.project) / task_path.name

    submission_dir = run_sota(args.session, args.project, task_path, args.agent)
    print(f"已创建 SOTA 会话: {submission_dir}")
    print(f"Prompt 文件: {submission_dir / 'PROMPT.md'}")
    print(f"运行脚本: {submission_dir / 'run.sh'}")


if __name__ == "__main__":
    main()
