"""
GSB 跨文件一致性验证工具
验证评价结果文件与对话内容文件、git 仓库之间的交叉一致性。
包括：Session ID 一致性、Commit ID 远程存在性等。
"""

import os
import re
import subprocess
import sys
from config_loader import load_config, get_github_config
from path_resolver import (
    get_main_branch_dir,
    get_dialogue_file_path,
    get_review_file_path,
)
from session_id_tool import extract_session_ids_from_dialogue, extract_session_ids_from_review


def verify_commit_id_remote(commit_id: str, repo_url: str, token: str = "") -> bool:
    """通过 curl 验证 commit id 是否在远程仓库存在。"""
    if not commit_id or not repo_url:
        return False
    # 去掉 .git 后缀
    url = repo_url.rstrip("/").replace(".git", "")
    check_url = f"{url}/commit/{commit_id}"
    cmd = ["curl", "-sI"]
    if token:
        cmd.extend(["-H", f"Authorization: token {token}"])
    cmd.append(check_url)
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, encoding="utf-8"
    )
    return "200" in result.stdout or "200" in result.stderr


def extract_commit_id_from_review(text: str) -> str:
    """从评价结果文本中提取 Commit ID。"""
    m = re.search(r"##\s*Commit\s*ID\s*\n(.*?)(?=\n## |\n# |\Z)", text, re.DOTALL)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line == "【必须原文逐字复制，禁止改写】":
            continue
        # 验证是否为 40 位 hash
        if re.match(r"^[a-f0-9]{40}$", line):
            return line
    return ""


def verify_single_review(review_path: str, dialogue_path: str,
                          repo_dir: str = None, repo_url: str = None,
                          token: str = "") -> dict:
    """
    验证单个评价结果文件的三方一致性。
    返回 {"ok": bool, "errors": [str, ...]}
    """
    errors = []

    if not os.path.exists(review_path):
        return {"ok": False, "errors": [f"评价结果文件不存在: {review_path}"]}
    if not os.path.exists(dialogue_path):
        return {"ok": False, "errors": [f"对话内容文件不存在: {dialogue_path}"]}

    with open(review_path, "r", encoding="utf-8") as f:
        review_text = f.read()
    with open(dialogue_path, "r", encoding="utf-8") as f:
        dialogue_text = f.read()

    # 1. Session ID 一致性
    dialogue_sids = {r: sid for r, sid in extract_session_ids_from_dialogue(dialogue_text)}
    review_sids = {r: sid for r, sid in extract_session_ids_from_review(review_text)}

    for r in sorted(set(list(dialogue_sids.keys()) + list(review_sids.keys()))):
        dsid = dialogue_sids.get(r, "")
        rsid = review_sids.get(r, "")
        if dsid != rsid:
            errors.append(
                f"第{r}轮 Session ID 不一致: 对话内容=[{dsid}], 评价结果=[{rsid}]"
            )

    # 2. Commit ID 远程验证（如果提供了 repo_url）
    if repo_url:
        commit_id = extract_commit_id_from_review(review_text)
        if commit_id:
            if not verify_commit_id_remote(commit_id, repo_url, token):
                errors.append(
                    f"Commit ID [{commit_id}] 在远程仓库验证失败 (404)"
                )

    # 3. Commit ID 与 git 仓库一致性（如果提供了 repo_dir）
    if repo_dir and os.path.exists(repo_dir):
        commit_id = extract_commit_id_from_review(review_text)
        if commit_id:
            result = subprocess.run(
                ["git", "-C", repo_dir, "cat-file", "-t", commit_id],
                capture_output=True, text=True, encoding="utf-8"
            )
            if result.returncode != 0 or "commit" not in result.stdout:
                errors.append(
                    f"Commit ID [{commit_id}] 在本地仓库中不存在"
                )

    return {"ok": len(errors) == 0, "errors": errors}


def verify_all(project_name: str, task_type: str, config: dict = None) -> dict:
    """
    验证某项目某类型下所有模型的三方一致性。
    返回 {"ok": bool, "total_checked": int, "total_errors": int, "details": [...]}
    """
    cfg = config or load_config()
    models = cfg.get("models", [])
    gh = get_github_config(cfg)
    username = gh.get("username", "")
    token = gh.get("pat", "")
    repo_url = f"https://github.com/{username}/{project_name}"
    repo_dir = get_main_branch_dir(project_name, cfg)

    details = []
    total_checked = 0
    total_errors = 0

    for m in models:
        slug = m.get("slug", "")
        if not slug:
            continue
        dialogue_path = get_dialogue_file_path(project_name, task_type, slug, cfg)
        review_path = get_review_file_path(project_name, task_type, slug, cfg)
        if not os.path.exists(dialogue_path) or not os.path.exists(review_path):
            continue
        total_checked += 1
        result = verify_single_review(review_path, dialogue_path, repo_dir, repo_url, token)
        if result["errors"]:
            total_errors += len(result["errors"])
            details.append({
                "model": slug,
                "errors": result["errors"],
            })

    return {
        "ok": total_errors == 0,
        "total_checked": total_checked,
        "total_errors": total_errors,
        "details": details,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GSB 跨文件验证工具")
    parser.add_argument("project_name")
    parser.add_argument("task_type")
    parser.add_argument("--model", help="仅验证指定模型")
    args = parser.parse_args()

    cfg = load_config()
    if args.model:
        dpath = get_dialogue_file_path(args.project_name, args.task_type, args.model, cfg)
        rpath = get_review_file_path(args.project_name, args.task_type, args.model, cfg)
        repo_dir = get_main_branch_dir(args.project_name, cfg)
        gh = get_github_config(cfg)
        repo_url = f"https://github.com/{gh['username']}/{args.project_name}"
        result = verify_single_review(rpath, dpath, repo_dir, repo_url, gh.get("pat", ""))
        print(f"验证结果: {'通过' if result['ok'] else '失败'}")
        for e in result["errors"]:
            print(f"  - {e}")
        sys.exit(0 if result["ok"] else 1)
    else:
        result = verify_all(args.project_name, args.task_type, cfg)
        print(f"共检查 {result['total_checked']} 个模型")
        print(f"发现 {result['total_errors']} 处错误")
        for d in result["details"]:
            print(f"  模型 {d['model']}:")
            for e in d["errors"]:
                print(f"    - {e}")
        sys.exit(0 if result["ok"] else 1)
