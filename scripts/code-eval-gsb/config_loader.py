"""
GSB 配置加载器
统一读取 scripts/gsb/config.yaml，所有脚本和 skill 均通过此模块获取配置。
"""

import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def load_config(path: str = None) -> dict:
    """加载 YAML 配置文件，返回字典。"""
    p = path or CONFIG_PATH
    if not os.path.exists(p):
        raise FileNotFoundError(f"配置文件不存在: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_workspace_root(config: dict = None) -> str:
    """获取工作区根目录（绝对路径）。"""
    cfg = config or load_config()
    root = cfg.get("workspace_root", "")
    if not os.path.isabs(root):
        # 相对于项目根目录（假设 scripts/gsb/ 在项目根下）
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", root))
    return root


def resolve_path(relative_path: str, config: dict = None) -> str:
    """将相对于 workspace_root 的路径解析为绝对路径。"""
    root = get_workspace_root(config)
    return os.path.abspath(os.path.join(root, relative_path))


def get_models(config: dict = None) -> list:
    """获取模型列表。"""
    cfg = config or load_config()
    return cfg.get("models", [])


def get_comparisons(config: dict = None) -> list:
    """获取对比组合列表。"""
    cfg = config or load_config()
    return cfg.get("comparisons", [])


def get_model_by_slug(slug: str, config: dict = None) -> dict:
    """根据 slug 查找模型配置。"""
    for m in get_models(config):
        if m.get("slug", "").lower() == slug.lower():
            return m
    return {}


def get_model_by_index(index: int, config: dict = None) -> dict:
    """根据下标查找模型配置。"""
    models = get_models(config)
    if 0 <= index < len(models):
        return models[index]
    return {}


def get_task_types(config: dict = None) -> list:
    """获取任务类型列表。"""
    cfg = config or load_config()
    return cfg.get("task_types", [])


def get_github_config(config: dict = None) -> dict:
    """获取 GitHub 配置。"""
    cfg = config or load_config()
    return {
        "username": cfg.get("github_username", ""),
        "pat": cfg.get("github_pat", ""),
    }


if __name__ == "__main__":
    cfg = load_config()
    print("Workspace Root:", get_workspace_root(cfg))
    print("Models:", [m["name"] for m in get_models(cfg)])
    print("Comparisons:", [c["name"] for c in get_comparisons(cfg)])
