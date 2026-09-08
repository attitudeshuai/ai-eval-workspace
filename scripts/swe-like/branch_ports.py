#!/usr/bin/env python3
"""打印某分支的专属端口映射（验证阶段用，避免多分支固定端口冲突）。

规则：分支序号 N（取分支名末尾数字）→ 偏移 N×1000。
  http  9080 → 9080 + N×1000
  https 9443 → 9443 + N×1000
  admin 2999 → 2999 + N×1000
"""
import re
import sys


def ports(branch):
    m = re.search(r"(\d+)\s*$", branch)
    n = int(m.group(1)) if m else 0
    offset = n * 1000
    return {
        "http": 9080 + offset,
        "https": 9443 + offset,
        "admin": 2999 + offset,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: branch_ports.py <分支名>", file=sys.stderr)
        sys.exit(2)
    p = ports(sys.argv[1])
    for k, v in p.items():
        print(f"{k}={v}")
