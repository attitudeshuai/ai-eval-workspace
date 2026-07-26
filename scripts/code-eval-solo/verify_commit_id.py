import sys, os, re, subprocess


def extract_commit_ids(file_path: str):
    """从评价结果文件中提取所有非空 Commit ID，返回 [(round_num, commit_id), ...]"""
    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    rounds = list(re.finditer(r'^# .+ 第\s*(\d+)\s*次对话评价结果', content, re.MULTILINE))
    results = []

    for i, m in enumerate(rounds):
        round_num = int(m.group(1))
        start = m.start()
        end = rounds[i + 1].start() if i + 1 < len(rounds) else len(content)
        block = content[start:end]

        cid_match = re.search(
            r'## Commit ID\s*\n'
            r'(?:【必须原文逐字复制，禁止改写】)?\s*'
            r'(.*?)\s*(?=\n## |\Z)',
            block, re.DOTALL
        )
        commit_id = cid_match.group(1).strip() if cid_match else ''
        commit_id = re.sub(r'<!--.*?-->', '', commit_id).strip()
        if commit_id:
            results.append((round_num, commit_id))

    return results


def get_repo_page_url(repo_path: str) -> str:
    """从 git remote URL 解析出仓库页面地址（去掉 .git，去掉 token）。"""
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, check=True
        )
        url = result.stdout.strip()
        if url.startswith('git@'):
            url = url.replace(':', '/').replace('git@', 'https://')
        if url.endswith('.git'):
            url = url[:-4]
        url = re.sub(r'^https://[^@]+@', 'https://', url)
        return url
    except subprocess.CalledProcessError:
        return ''


def verify_remote_commit(repo_page_url: str, commit_id: str) -> tuple[bool, str]:
    """请求远程 commit 页面，检查状态码。返回 (是否通过, 诊断信息)"""
    commit_url = f"{repo_page_url}/commit/{commit_id}"
    try:
        import urllib.request
        req = urllib.request.Request(commit_url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = resp.status
            if code == 200:
                return True, f"HTTP 200"
            if code == 404:
                return False, f"HTTP 404，commit 不存在或尚未推送到远程"
            return False, f"HTTP {code}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, f"HTTP 404，commit 不存在或尚未推送到远程"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, f"请求异常: {e}"


def verify_commit_ids(review_path: str, repo_path: str) -> bool:
    """验证评价结果文件中所有 Commit ID 在远程 commit 页面可访问（HTTP 200）。"""
    print(f'评价文件: {review_path}')
    print(f'仓库目录: {repo_path}')
    print()

    commit_records = extract_commit_ids(review_path)
    if not commit_records:
        print('未找到任何非空 Commit ID，无需验证。')
        return True

    repo_url = get_repo_page_url(repo_path)
    if not repo_url:
        print("❌ 验证失败：无法从 git remote 解析仓库页面地址")
        return False

    issues = []
    for round_num, commit_id in commit_records:
        if len(commit_id) != 40:
            issues.append(
                f"轮次 {round_num}: Commit ID 长度不为 40 位 (当前 {len(commit_id)} 位): {commit_id}"
            )
            continue

        ok, info = verify_remote_commit(repo_url, commit_id)
        url = f"{repo_url}/commit/{commit_id}"
        if not ok:
            issues.append(f"轮次 {round_num}: {info} ({url})")

    if issues:
        print(f"❌ 验证失败，发现 {len(issues)} 个问题：\n")
        for issue in issues:
            print(f"  - {issue}")
        print()
        return False
    else:
        print(f"✅ 验证通过！共 {len(commit_records)} 个 Commit ID，全部在远程仓库中存在。")
        return True


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(
            "Usage: python verify_commit_id.py <评价结果文件路径> <git仓库路径>",
            file=sys.stderr
        )
        sys.exit(1)

    review_path = sys.argv[1]
    repo_path = sys.argv[2]

    if not os.path.exists(review_path):
        print(f"错误: 评价结果文件不存在: {review_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(repo_path):
        print(f"错误: 仓库目录不存在: {repo_path}", file=sys.stderr)
        sys.exit(1)

    ok = verify_commit_ids(review_path, repo_path)
    sys.exit(0 if ok else 1)
