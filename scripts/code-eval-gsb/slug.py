"""
GSB 模型名称 slug 化工具
将模型原始名称转换为可用于分支名、文件名的安全标识。
"""

import re


def to_slug(name: str) -> str:
    """
    将模型名称转换为 slug：
    1. 全部转为小写
    2. 空格替换为 -
    3. 删除所有非字母、数字、- 的特殊字符
    示例：
      "Claude 3.7 Sonnet" -> "claude-3-7-sonnet"
      "GPT-4o" -> "gpt-4o"
      "Gemini 2.5 Pro" -> "gemini-2-5-pro"
    """
    s = name.lower()
    s = s.replace(" ", "-")
    s = re.sub(r"[^a-z0-9\-]", "", s)
    # 合并连续的 -
    s = re.sub(r"\-+", "-", s)
    s = s.strip("-")
    return s


def validate_slug(slug: str) -> bool:
    """验证 slug 是否合法。"""
    if not slug:
        return False
    return bool(re.match(r"^[a-z0-9\-]+$", slug))


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or ["Claude 3.7 Sonnet", "GPT-4o", "Gemini 2.5 Pro", "Test Model V1.0"]
    for n in names:
        print(f"{n!r} -> {to_slug(n)!r}")
