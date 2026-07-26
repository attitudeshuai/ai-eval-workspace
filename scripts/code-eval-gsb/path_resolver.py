"""
GSB 路径解析器
根据项目名、类型、模型 slug 等，统一解析所有相关路径。
所有路径均基于 config.yaml 中的配置计算。
"""

import os
from config_loader import load_config, resolve_path


def get_project_name(project_id: str, config: dict = None) -> str:
    """补全项目名（添加前缀）。"""
    cfg = config or load_config()
    prefix = cfg.get("project_prefix", "")
    pid = project_id.strip()
    if not pid.startswith(prefix):
        return f"{prefix}{pid}"
    return pid


def get_main_branch_dir(project_name: str, config: dict = None) -> str:
    """获取本地主分支目录（origin）。"""
    cfg = config or load_config()
    base = cfg.get("local_main_branch_base", "")
    rel = os.path.join(base, project_name, project_name)
    return resolve_path(rel, cfg)


def get_model_branch_dir(project_name: str, slug: str, config: dict = None) -> str:
    """获取某模型的本地分支目录。"""
    cfg = config or load_config()
    base = cfg.get("local_main_branch_base", "")
    rel = os.path.join(base, project_name, f"{project_name}-{slug}")
    return resolve_path(rel, cfg)


def get_result_type_dir(project_name: str, task_type: str, config: dict = None) -> str:
    """获取某项目某类型的结果目录。"""
    cfg = config or load_config()
    base = cfg.get("result_base", "")
    # 类型中的空格替换为合理字符，保持与现有习惯一致
    type_safe = task_type.replace(" ", "")
    rel = os.path.join(base, project_name, f"{project_name}-{type_safe}")
    return resolve_path(rel, cfg)


def get_dialogue_file_path(project_name: str, task_type: str, slug: str, config: dict = None) -> str:
    """获取对话内容文件路径。"""
    cfg = config or load_config()
    suffix = cfg.get("dialogue_suffix", "对话内容")
    type_safe = task_type.replace(" ", "")
    dir_path = get_result_type_dir(project_name, task_type, cfg)
    # 文件名格式: <项目名>-<类型>-<slug>-对话内容.md
    # 注意：原始 skill 中文件名前有 A- 前缀，但 skill 内部说不要 A- 前缀；
    # 这里按 skill 文档的不带 A- 前缀处理，如果实际需要可以外部调整
    filename = f"{project_name}-{type_safe}-{slug}-{suffix}.md"
    return os.path.join(dir_path, filename)


def get_review_file_path(project_name: str, task_type: str, slug: str, config: dict = None) -> str:
    """获取评价结果文件路径。"""
    cfg = config or load_config()
    suffix = cfg.get("review_suffix", "评价结果")
    type_safe = task_type.replace(" ", "")
    dir_path = get_result_type_dir(project_name, task_type, cfg)
    filename = f"{project_name}-{type_safe}-{slug}-{suffix}.md"
    return os.path.join(dir_path, filename)


def get_summary_file_path(project_name: str, task_type: str, config: dict = None) -> str:
    """获取评价汇总文件路径。"""
    cfg = config or load_config()
    suffix = cfg.get("summary_suffix", "评价汇总")
    type_safe = task_type.replace(" ", "")
    dir_path = get_result_type_dir(project_name, task_type, cfg)
    filename = f"{project_name}-{type_safe}-{suffix}.md"
    return os.path.join(dir_path, filename)


def get_github_repo_url(project_name: str, config: dict = None) -> str:
    """获取 GitHub 仓库地址（HTTPS，无 .git 后缀）。"""
    cfg = config or load_config()
    username = cfg.get("github_username", "")
    return f"https://github.com/{username}/{project_name}"


def get_all_model_branch_dirs(project_name: str, config: dict = None) -> dict:
    """获取所有模型的本地分支目录，返回 {slug: path}。"""
    cfg = config or load_config()
    result = {}
    for m in cfg.get("models", []):
        slug = m.get("slug", "")
        if slug:
            result[slug] = get_model_branch_dir(project_name, slug, cfg)
    return result


def ensure_result_dirs(project_name: str, task_type: str, config: dict = None):
    """确保某项目某类型的结果目录存在。"""
    dir_path = get_result_type_dir(project_name, task_type, config)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python path_resolver.py <project_id> <task_type>")
        sys.exit(1)

    pid = sys.argv[1]
    ttype = sys.argv[2]
    pname = get_project_name(pid)
    print(f"Project Name: {pname}")
    print(f"Main Branch Dir: {get_main_branch_dir(pname)}")
    print(f"Result Type Dir: {get_result_type_dir(pname, ttype)}")
    for m in load_config().get("models", []):
        s = m["slug"]
        print(f"Model [{s}] Branch Dir: {get_model_branch_dir(pname, s)}")
        print(f"  Dialogue: {get_dialogue_file_path(pname, ttype, s)}")
        print(f"  Review  : {get_review_file_path(pname, ttype, s)}")
    print(f"Summary: {get_summary_file_path(pname, ttype)}")
