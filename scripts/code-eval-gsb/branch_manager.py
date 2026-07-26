"""
GSB 分支管理工具
负责根据配置在 GitHub 上创建对比分支、本地 clone 等操作。
"""

import os
import subprocess
import sys
from config_loader import load_config, get_github_config
from path_resolver import (
    get_main_branch_dir,
    get_model_branch_dir,
    get_github_repo_url,
)


def run_cmd(cmd: list, cwd: str = None, check: bool = False) -> tuple:
    """运行 shell 命令，返回 (returncode, stdout, stderr)。"""
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.returncode, result.stdout, result.stderr


def create_github_branches(project_name: str, config: dict = None) -> dict:
    """
    在 GitHub 上从 main 创建所有模型的对比分支。
    返回 {"ok": bool, "created": [slug, ...], "failed": [(slug, error), ...]}
    """
    cfg = config or load_config()
    models = cfg.get("models", [])
    origin_dir = get_main_branch_dir(project_name, cfg)
    gh = get_github_config(cfg)
    username = gh.get("username", "")
    pat = gh.get("pat", "")

    created = []
    failed = []

    for m in models:
        slug = m.get("slug", "")
        if not slug:
            continue
        # 使用 git push origin main:<slug>
        # 优先 SSH，回退 HTTPS + PAT
        ssh_url = f"git@github.com:{username}/{project_name}.git"
        https_url = f"https://{pat}@github.com/{username}/{project_name}.git"

        rc, out, err = run_cmd(["git", "push", "origin", f"main:{slug}"], cwd=origin_dir)
        if rc != 0:
            # 尝试用 HTTPS
            rc2, out2, err2 = run_cmd(
                ["git", "push", https_url, f"main:{slug}"], cwd=origin_dir
            )
            if rc2 != 0:
                failed.append((slug, err or err2))
                continue
        created.append(slug)

    return {"ok": len(failed) == 0, "created": created, "failed": failed}


def clone_model_branches(project_name: str, config: dict = None) -> dict:
    """
    将所有模型的对比分支 clone 到本地独立目录。
    返回 {"ok": bool, "cloned": [slug, ...], "failed": [(slug, error), ...]}
    """
    cfg = config or load_config()
    models = cfg.get("models", [])
    gh = get_github_config(cfg)
    username = gh.get("username", "")
    pat = gh.get("pat", "")

    cloned = []
    failed = []

    for m in models:
        slug = m.get("slug", "")
        if not slug:
            continue
        target_dir = get_model_branch_dir(project_name, slug, cfg)
        if os.path.exists(target_dir):
            cloned.append(slug)
            continue

        ssh_url = f"git@github.com:{username}/{project_name}.git"
        https_url = f"https://{pat}@github.com/{username}/{project_name}.git"

        rc, out, err = run_cmd(
            ["git", "clone", "-b", slug, ssh_url, target_dir]
        )
        if rc != 0:
            rc2, out2, err2 = run_cmd(
                ["git", "clone", "-b", slug, https_url, target_dir]
            )
            if rc2 != 0:
                failed.append((slug, err or err2))
                continue
        cloned.append(slug)

    return {"ok": len(failed) == 0, "cloned": cloned, "failed": failed}


def verify_local_dirs(project_name: str, config: dict = None) -> dict:
    """
    验证所有本地目录是否存在。
    返回 {"ok": bool, "missing": [path, ...], "existing": [path, ...]}
    """
    cfg = config or load_config()
    models = cfg.get("models", [])
    missing = []
    existing = []

    origin_dir = get_main_branch_dir(project_name, cfg)
    if os.path.exists(origin_dir):
        existing.append(origin_dir)
    else:
        missing.append(origin_dir)

    for m in models:
        slug = m.get("slug", "")
        if not slug:
            continue
        d = get_model_branch_dir(project_name, slug, cfg)
        if os.path.exists(d):
            existing.append(d)
        else:
            missing.append(d)

    return {"ok": len(missing) == 0, "missing": missing, "existing": existing}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GSB 分支管理工具")
    parser.add_argument("command", choices=["create", "clone", "verify"])
    parser.add_argument("project_name")
    args = parser.parse_args()

    if args.command == "create":
        result = create_github_branches(args.project_name)
    elif args.command == "clone":
        result = clone_model_branches(args.project_name)
    else:
        result = verify_local_dirs(args.project_name)

    print(result)
    sys.exit(0 if result["ok"] else 1)
