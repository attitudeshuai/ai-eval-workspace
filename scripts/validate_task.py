#!/usr/bin/env python3
"""校验 Web Dev 项目中的单个任务格式。仅适用于使用固定任务结构的项目。"""

import argparse
import sys
from pathlib import Path

from utils.helpers import load_json


def validate_task(task_dir: Path) -> dict:
    result = {"task": task_dir.name, "ok": True, "errors": [], "warnings": []}

    required_files = ["task.md", "metadata.json", "README.md", "rubric.json"]
    for f in required_files:
        p = task_dir / f
        if not p.exists():
            result["errors"].append(f"缺少文件: {f}")

    starter = task_dir / "starter"
    if not starter.exists():
        result["errors"].append("缺少 starter 目录")
    else:
        pkg = starter / "package.json"
        if pkg.exists():
            lockfiles = [
                starter / "package-lock.json",
                starter / "pnpm-lock.yaml",
                starter / "yarn.lock",
            ]
            if not any(l.exists() for l in lockfiles):
                result["warnings"].append("starter 未提供 lockfile（建议加上以便复现）")
        else:
            result["warnings"].append("starter 中没有 package.json（非 Node 项目可忽略）")

    metadata_path = task_dir / "metadata.json"
    if metadata_path.exists():
        try:
            data = load_json(metadata_path)
            if "id" not in data and "task_id" not in data:
                result["errors"].append("metadata.json 缺少 id 或 task_id 字段")
            if "category" not in data and "category_tags" not in data:
                result["errors"].append("metadata.json 缺少 category 或 category_tags 字段")
            if "difficulty" not in data:
                result["errors"].append("metadata.json 缺少 difficulty 字段")
        except Exception as e:
            result["errors"].append(f"metadata.json 解析失败: {e}")

    rubric_path = task_dir / "rubric.json"
    if rubric_path.exists():
        try:
            rubric = load_json(rubric_path)
            if not isinstance(rubric, dict):
                result["errors"].append("rubric.json 顶层应为 dict")
            elif "criteria" not in rubric and "dimensions" not in rubric:
                result["errors"].append("rubric.json 缺少 criteria 或 dimensions 字段")
        except Exception as e:
            result["errors"].append(f"rubric.json 解析失败: {e}")

    if result["errors"]:
        result["ok"] = False

    return result


def main():
    parser = argparse.ArgumentParser(description="校验任务结构")
    parser.add_argument("task_dir", type=Path, help="任务目录路径")
    args = parser.parse_args()

    result = validate_task(args.task_dir)
    status = "✅ 通过" if result["ok"] else "❌ 失败"
    print(f"{status} 任务: {result['task']}")
    for err in result["errors"]:
        print(f"  - {err}")
    for warning in result["warnings"]:
        print(f"  ⚠️ {warning}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
