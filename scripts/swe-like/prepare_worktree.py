#!/usr/bin/env python3
"""建分支后准备 worktree：确保工作台产物被 git 忽略，并打印该分支专属端口。

不修改 tracked 的 .gitignore，而是写入该 worktree 的 .git/info/exclude
（本地、不跟踪、不污染 diff）。
"""
import re
import sys
from pathlib import Path

IGNORE = [".trae/", "evidence/"]


def ports(branch):
    m = re.search(r"(\d+)\s*$", branch)
    n = int(m.group(1)) if m else 0
    offset = n * 1000
    return {"http": 9080 + offset, "https": 9443 + offset, "admin": 2999 + offset}


def ensure_ignored(worktree):
    exclude = Path(worktree) / ".git" / "info" / "exclude"
    if not exclude.exists():
        print(f"警告：{exclude} 不存在（这是 git worktree 吗？）", file=sys.stderr)
        return
    lines = exclude.read_text(encoding="utf-8").splitlines()
    missing = [p for p in IGNORE if not any(l.rstrip() == p for l in lines)]
    if missing:
        with exclude.open("a", encoding="utf-8") as f:
            f.write("\n# swe-like workspace artifacts (local, untracked)\n")
            for p in missing:
                f.write(p + "\n")
        print(f"已写入 .git/info/exclude: {missing}")
    else:
        print("工作台产物已忽略（.trae/ evidence/）")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: prepare_worktree.py <worktree路径> <分支名>", file=sys.stderr)
        sys.exit(2)
    ensure_ignored(sys.argv[1])
    p = ports(sys.argv[2])
    print("端口映射:", ", ".join(f"{k}={v}" for k, v in p.items()))
