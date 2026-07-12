#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
将交付文件夹发布为 GitHub 仓库。

读取 projects/webdev-long-horizon/config.toml 和 secrets.toml 中的 [github] 配置，
在指定用户下创建公开仓库，初始化 git 并推送交付文件夹。

用法：
    python scripts/webdev-long-horizon/publish_to_github.py \
      --task webdev-task-sxw-03 \
      --deliverable deliverables/webdev-long-horizon/webdev-task-sxw-03
"""

import argparse
import os
import subprocess
from pathlib import Path


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_toml(path: Path) -> dict:
    import tomllib
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_github_config(project_id: str) -> dict:
    config_path = workspace_root() / "projects" / project_id / "config.toml"
    defaults = {"username": "", "token": ""}

    if config_path.exists():
        data = load_toml(config_path)
        github = data.get("github", {})
        secrets_file = github.get("secrets_file", "secrets.toml")
        secrets_path = workspace_root() / "projects" / project_id / secrets_file
        if secrets_path.exists():
            secrets = load_toml(secrets_path)
            gh_secrets = secrets.get("github", {})
            for key in ["username", "token"]:
                if key in gh_secrets:
                    defaults[key] = gh_secrets[key]

    return defaults


def publish(task_id: str, deliverable_dir: str, project_id: str = "webdev-long-horizon") -> str:
    config = load_github_config(project_id)
    username = config["username"]
    token = config["token"]

    if not username or not token:
        raise ValueError("GitHub 配置缺失：请在 projects/<project>/secrets.toml 中配置 [github] 段")

    deliverable_path = Path(deliverable_dir).resolve()
    if not deliverable_path.exists():
        raise FileNotFoundError(f"交付目录不存在: {deliverable_path}")

    # 1. 检查是否已有 git 仓库，没有则初始化
    git_dir = deliverable_path / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=deliverable_path, capture_output=True, check=True)

    # 2. 确保有 .gitignore
    gitignore = deliverable_path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("node_modules/\ndist/\nbuild/\n.cache/\n*.log\n.env\n.DS_Store\nThumbs.db\n", encoding="utf-8")

    # 3. 提交所有文件
    subprocess.run(["git", "add", "."], cwd=deliverable_path, capture_output=True, check=True)
    result = subprocess.run(
        ["git", "commit", "--allow-empty", "-m", f"Deliverable: {task_id}"],
        cwd=deliverable_path, capture_output=True, text=True
    )

    # 4. 通过 API 创建 GitHub 仓库
    import urllib.request, json
    repo_name = task_id
    api_url = "https://api.github.com/user/repos"
    data = json.dumps({"name": repo_name, "private": False, "auto_init": False}).encode()
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ai-eval-workspace")

    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read())
            html_url = resp_data.get("html_url", "")
            print(f"仓库已创建: {html_url}")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        if "already exists" in body or e.code == 422:
            print(f"仓库已存在: https://github.com/{username}/{repo_name}")
        else:
            raise RuntimeError(f"创建仓库失败: {e.code} {body}")

    # 5. 添加 remote 并推送
    remote_url = f"git@github.com:{username}/{repo_name}.git"
    subprocess.run(
        ["git", "remote", "remove", "origin"],
        cwd=deliverable_path, capture_output=True
    )
    subprocess.run(
        ["git", "remote", "add", "origin", remote_url],
        cwd=deliverable_path, capture_output=True, check=True
    )

    # 获取当前分支名
    branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=deliverable_path, capture_output=True, text=True, check=True
    )
    branch = branch_result.stdout.strip()

    subprocess.run(
        ["git", "push", "-u", "origin", branch, "--force"],
        cwd=deliverable_path, capture_output=True, check=True
    )

    repo_url = f"https://github.com/{username}/{repo_name}"
    print(f"推送完成: {repo_url}")
    return repo_url


def main():
    parser = argparse.ArgumentParser(description="将交付文件夹发布为 GitHub 仓库")
    parser.add_argument("--task", required=True, help="任务 ID，例如 webdev-task-sxw-03")
    parser.add_argument("--deliverable", required=True, help="交付文件夹路径")
    parser.add_argument("--project", default="webdev-long-horizon", help="项目 ID")
    args = parser.parse_args()

    repo_url = publish(args.task, args.deliverable, args.project)
    print(f"\n✓ 发布完成: {repo_url}")


if __name__ == "__main__":
    main()
