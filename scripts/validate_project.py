#!/usr/bin/env python3
"""校验项目是否存在且配置合规。默认不强制任务结构。"""

import argparse
import sys
from pathlib import Path

from utils.helpers import list_projects, list_tasks, load_toml, project_dir
from validate_task import validate_task


def check_project_config(project_id: str) -> list[str]:
    errors = []
    pd = project_dir(project_id)
    if not pd.exists():
        return [f"项目不存在: {project_id}"]

    config_path = pd / "config.toml"
    if not config_path.exists():
        errors.append("项目缺少 config.toml")
        return errors

    try:
        data = load_toml(config_path)
    except Exception as e:
        errors.append(f"config.toml 解析失败: {e}")
        return errors

    project = data.get("project", {})
    for key in ["id", "name"]:
        if key not in project:
            errors.append(f"config.toml [project] 缺少字段: {key}")

    return errors


def validate_project(
    project_id: str, validate_tasks: bool = False, allow_no_starter: bool = False
) -> dict:
    result = {
        "project": project_id,
        "ok": True,
        "errors": [],
        "tasks": [],
    }
    result["errors"].extend(check_project_config(project_id))

    if validate_tasks and not result["errors"]:
        for task_dir in list_tasks(project_id):
            task_result = validate_task(task_dir, allow_no_starter=allow_no_starter)
            result["tasks"].append(task_result)
            if not task_result["ok"]:
                result["ok"] = False

    if result["errors"]:
        result["ok"] = False

    return result


def main():
    parser = argparse.ArgumentParser(description="校验项目")
    parser.add_argument("--project", help="指定项目 ID")
    parser.add_argument("--all", action="store_true", help="校验所有项目")
    parser.add_argument("--tasks", action="store_true", help="同时校验项目下的任务结构（仅适用于使用 Web Dev 任务格式的项目）")
    parser.add_argument(
        "--allow-no-starter",
        action="store_true",
        help="允许任务目录中不存在 starter（源码由外部提供）",
    )
    args = parser.parse_args()

    if args.all:
        projects = [p.name for p in list_projects()]
    elif args.project:
        projects = [args.project]
    else:
        print("请指定 --project 或 --all")
        sys.exit(1)

    all_ok = True
    for project_id in projects:
        result = validate_project(
            project_id, validate_tasks=args.tasks, allow_no_starter=args.allow_no_starter
        )
        status = "✅ 通过" if result["ok"] else "❌ 失败"
        print(f"\n{status} 项目: {result['project']}")
        for err in result["errors"]:
            print(f"  - {err}")
        if args.tasks:
            for task_result in result["tasks"]:
                task_status = "✅ 通过" if task_result["ok"] else "❌ 失败"
                print(f"  {task_status} 任务: {task_result['task']}")
                for err in task_result["errors"]:
                    print(f"    - {err}")
        if not result["ok"]:
            all_ok = False

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
