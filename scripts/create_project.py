#!/usr/bin/env python3
"""onboard 一个新的评估项目。"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from utils.helpers import project_dir, render_template, workspace_root


def create_project(project_id: str, name: str, description: str) -> Path:
    pd = project_dir(project_id)
    if pd.exists():
        raise FileExistsError(f"项目已存在: {pd}")

    template_dir = workspace_root() / "templates" / "project"

    now = datetime.now(timezone.utc).isoformat()
    variables = {
        "project_id": project_id,
        "project_name": name,
        "description": description,
        "created_at": now,
    }

    pd.mkdir(parents=True, exist_ok=True)

    # 渲染最小化模板
    for template_file in ["config.toml", "README.md"]:
        src = template_dir / template_file
        if src.exists():
            (pd / template_file).write_text(
                render_template(src, variables), encoding="utf-8"
            )

    return pd


def main():
    parser = argparse.ArgumentParser(description="创建新评估项目")
    parser.add_argument("--id", required=True, help="项目 ID（英文、短横线连接）")
    parser.add_argument("--name", required=True, help="项目显示名称")
    parser.add_argument("--description", default="", help="项目描述")
    args = parser.parse_args()

    pd = create_project(args.id, args.name, args.description)
    print(f"已创建项目: {pd}")
    print(f"配置文件: {pd / 'config.toml'}")
    print(f"说明文档: {pd / 'README.md'}")
    print("提示：项目内部结构完全自由，可根据需求自行组织。")


if __name__ == "__main__":
    main()
