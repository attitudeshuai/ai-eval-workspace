"""通用工具函数。"""

import json
import re
import shutil
import tomllib
from pathlib import Path
from typing import Any

import yaml


# 复制时默认忽略的路径
DEFAULT_IGNORE_PATTERNS = {"node_modules", ".git", "__pycache__", ".cache", "dist", "build"}


def workspace_root() -> Path:
    """返回工作空间根目录。"""
    return Path(__file__).resolve().parents[2]


def project_dir(project_id: str) -> Path:
    """返回项目目录。"""
    return workspace_root() / "projects" / project_id


def tasks_dir(project_id: str) -> Path:
    """返回项目任务根目录。"""
    return project_dir(project_id) / "tasks"


def sources_dir(project_id: str) -> Path:
    """返回项目源码根目录。"""
    return project_dir(project_id) / "sources"


def task_prefix(project_id: str) -> str:
    """返回项目配置中的任务前缀。"""
    config_path = project_dir(project_id) / "config.toml"
    if config_path.exists():
        data = load_toml(config_path)
        return data.get("project", {}).get("task_prefix", "task")
    return "task"


def all_task_prefixes(project_id: str) -> list[str]:
    """返回所有有效的任务前缀（当前前缀 + 旧前缀），用于向后兼容查找。"""
    prefixes = [task_prefix(project_id)]
    config_path = project_dir(project_id) / "config.toml"
    if config_path.exists():
        data = load_toml(config_path)
        legacy = data.get("project", {}).get("legacy_task_prefixes", [])
        if isinstance(legacy, list):
            prefixes.extend(legacy)
    return prefixes


def task_id_pattern(prefix: str) -> re.Pattern:
    """返回任务 ID 正则：prefix-NN[.NN]*"""
    return re.compile(rf"^{re.escape(prefix)}-(\d+(?:\.\d+)*)$")


def is_task_dir(path: Path, prefix: str | list[str] | None = None) -> bool:
    """判断一个目录是否是有效的任务目录。

    标准：目录名匹配任一任务前缀的 ID 格式，且包含 metadata.json。
    prefix 可以是单个前缀字符串、前缀列表，或 None（自动从项目配置推断）。
    """
    if not path.is_dir():
        return False
    if prefix is None:
        # 从路径推断项目 ID
        parts = path.relative_to(workspace_root() / "projects").parts
        if len(parts) < 1:
            return False
        prefixes = all_task_prefixes(parts[0])
    elif isinstance(prefix, str):
        prefixes = [prefix]
    else:
        prefixes = prefix

    if not (path / "metadata.json").exists():
        return False
    return any(bool(task_id_pattern(p).match(path.name)) for p in prefixes)


def find_task_dir(project_id: str, task_id: str) -> Path | None:
    """根据 task_id 查找任务目录（支持层级目录结构和多前缀向后兼容）。"""
    td = tasks_dir(project_id)
    prefixes = all_task_prefixes(project_id)

    # 至少匹配一个前缀
    if not any(task_id_pattern(p).match(task_id) for p in prefixes):
        return None

    # 优先直接匹配：tasks/<task-id>/
    direct = td / task_id
    if is_task_dir(direct, prefixes):
        return direct

    # 递归查找
    for path in td.rglob(task_id):
        if is_task_dir(path, prefixes):
            return path
    return None


def find_source_dir(project_id: str, task_id: str) -> Path | None:
    """根据 task_id 查找外部源码目录（支持层级目录结构和多前缀向后兼容）。"""
    sd = sources_dir(project_id)
    prefixes = all_task_prefixes(project_id)

    # 至少匹配一个前缀
    if not any(task_id_pattern(p).match(task_id) for p in prefixes):
        return None

    # 优先直接匹配：sources/<task-id>/
    direct = sd / task_id
    if direct.is_dir():
        return direct

    # 递归查找
    for path in sd.rglob(task_id):
        if path.is_dir():
            return path
    return None


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_yaml(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def save_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def render_template(template_path: Path, variables: dict[str, Any]) -> str:
    """简单模板替换，支持 {{key}} 语法。非字符串值会序列化为 JSON。"""
    import json

    text = template_path.read_text(encoding="utf-8")
    for key, value in variables.items():
        replacement = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        text = text.replace("{{" + key + "}}", replacement)
    return text


def _should_ignore(path: Path, ignore_patterns: set[str]) -> bool:
    """判断路径是否应该被忽略。"""
    return any(part in ignore_patterns for part in path.parts)


def copy_tree(src: Path, dst: Path, ignore_patterns: set[str] | None = None) -> None:
    """递归复制目录，跳过已存在文件，默认忽略 node_modules 等。"""
    ignore = ignore_patterns if ignore_patterns is not None else DEFAULT_IGNORE_PATTERNS

    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return

    for item in src.rglob("*"):
        if _should_ignore(item.relative_to(src), ignore):
            continue
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def list_projects() -> list[Path]:
    """列出 projects/ 下所有项目目录。"""
    projects_dir = workspace_root() / "projects"
    if not projects_dir.exists():
        return []
    return sorted([p for p in projects_dir.iterdir() if p.is_dir()])


def list_tasks(project_id: str) -> list[Path]:
    """递归列出指定项目下所有任务目录（支持多前缀向后兼容）。"""
    td = tasks_dir(project_id)
    if not td.exists():
        return []

    prefixes = all_task_prefixes(project_id)
    return sorted([p for p in td.rglob("*") if is_task_dir(p, prefixes)])


def resolve_template(project_id: str, template_name: str) -> Path:
    """优先返回项目级模板，不存在则返回全局模板。"""
    project_template = project_dir(project_id) / "templates" / template_name
    if project_template.exists():
        return project_template
    global_template = workspace_root() / "templates" / template_name
    return global_template


def resolve_starter_template(project_id: str) -> Path:
    """优先返回项目级 starter 模板，不存在则返回全局 starter 模板。"""
    project_starter = project_dir(project_id) / "templates" / "starter"
    if project_starter.exists():
        return project_starter
    return workspace_root() / "templates" / "starter"


def default_source_dir(project_id: str, task_id: str) -> Path:
    """返回项目约定的外部源码目录：projects/<project>/sources/<task-id>/

    保持扁平路径作为默认值；实际查找请使用 find_source_dir。
    """
    return project_dir(project_id) / "sources" / task_id
