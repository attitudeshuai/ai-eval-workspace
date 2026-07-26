import sys, subprocess


def get_commit_id(repo_path: str) -> str:
    """从 git 仓库获取当前 HEAD 的完整 40 位 commit hash，原样输出，无任何额外格式。"""
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'log', '-1', '--format=%H'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"错误: 无法获取 commit hash: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python get_commit_id.py <git仓库路径>", file=sys.stderr)
        sys.exit(1)

    repo_path = sys.argv[1]
    commit_id = get_commit_id(repo_path)
    print(commit_id, end='')
