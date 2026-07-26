"""
通过 GitHub API 将本地目录内容上传到指定仓库的指定分支。
支持断点续传和重试。
"""
import base64
import os
import sys
import time
import urllib.request
import urllib.error
import json


def api_request(method, url, token, data=None, timeout=60):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "gsb-upload-script",
    }
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_request_with_retry(method, url, token, data=None, max_retries=5):
    for attempt in range(max_retries):
        try:
            return api_request(method, url, token, data, timeout=120)
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def get_existing_files(owner, repo, branch, token):
    """递归获取仓库中已存在的文件路径集合。"""
    existing = set()

    def walk(path=""):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        try:
            items = api_request_with_retry("GET", url, token)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return
            raise
        for item in items:
            item_type = item.get("type")
            item_path = item.get("path", "")
            if item_type == "file":
                existing.add(item_path)
            elif item_type == "dir":
                walk(item_path)

    walk()
    return existing


def upload_file(owner, repo, branch, local_path, repo_path, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}"
    with open(local_path, "rb") as f:
        content = f.read()
    encoded = base64.b64encode(content).decode("ascii")
    data = {
        "message": f"upload {repo_path}",
        "content": encoded,
        "branch": branch,
    }
    return api_request_with_retry("PUT", url, token, data)


def main():
    if len(sys.argv) < 5:
        print("Usage: python upload_to_github.py <owner> <repo> <branch> <local_dir>")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    branch = sys.argv[3]
    local_dir = sys.argv[4]
    token = os.environ.get("GITHUB_PAT") or "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"

    files = []
    for root, dirs, filenames in os.walk(local_dir):
        dirs[:] = [d for d in dirs if d != ".git"]
        for filename in filenames:
            local_path = os.path.join(root, filename)
            repo_path = os.path.relpath(local_path, local_dir).replace("\\", "/")
            files.append((local_path, repo_path))

    files.sort(key=lambda x: x[1])
    print(f"Total files: {len(files)}")

    print("Fetching existing files...")
    existing = get_existing_files(owner, repo, branch, token)
    print(f"Existing files: {len(existing)}")

    skipped = 0
    uploaded = 0
    for i, (local_path, repo_path) in enumerate(files):
        if repo_path in existing:
            print(f"[{i+1}/{len(files)}] SKIP (exists): {repo_path}")
            skipped += 1
            continue
        print(f"[{i+1}/{len(files)}] UPLOAD: {repo_path} ...")
        upload_file(owner, repo, branch, local_path, repo_path, token)
        uploaded += 1
        time.sleep(1)

    print(f"Upload complete. Uploaded: {uploaded}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
