"""
pairwise-gsb 项目统一配置读取模块。

所有脚本通过本模块读取 config.toml，避免硬编码路径、列名、标签集合。
"""

import os
import sys
from pathlib import Path

# Python 3.11+ 内置 tomllib；否则尝试 tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        print("需要 tomli 或 Python>=3.11: pip install tomli")
        sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.toml"


def _load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}")
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


_CONFIG = _load_config()


def get_config():
    """返回完整配置字典。"""
    return _CONFIG


def get_paths():
    return _CONFIG.get("paths", {})


def get_annotation_config():
    return _CONFIG.get("annotation", {})


def get_batch_config():
    return _CONFIG.get("batch", {})


def get_quality_config():
    return _CONFIG.get("quality", {})


def get_tags():
    """返回各类标签集合，用于校验。"""
    tags = _CONFIG.get("tags", {})
    return {
        "instruction": set(tags.get("instruction", {}).get("labels", [])),
        "consistency": set(tags.get("consistency", {}).get("labels", [])),
        "visual": set(tags.get("visual", {}).get("labels", [])),
    }


def get_tag_lists():
    """返回各类标签列表（保持 config.toml 中的定义顺序），用于生成下拉列表。"""
    tags = _CONFIG.get("tags", {})
    return {
        "instruction": list(tags.get("instruction", {}).get("labels", [])),
        "consistency": list(tags.get("consistency", {}).get("labels", [])),
        "visual": list(tags.get("visual", {}).get("labels", [])),
    }


def get_all_tags():
    """返回所有标签的并集。"""
    t = get_tags()
    return t["instruction"] | t["consistency"] | t["visual"]


def get_input_columns():
    return get_annotation_config().get("input_columns", [])


def get_output_columns():
    return get_annotation_config().get("output_columns", [])


def get_image_columns():
    return get_annotation_config().get("image_columns", [])


def get_gsb_values():
    return get_annotation_config().get("gsb_values", ["图片1更好", "图片2更好", "无法区分"])


def get_consistency_values():
    return get_annotation_config().get(
        "consistency_values", ["图片1更好", "图片2更好", "无法区分", "不涉及"]
    )


def get_tag_separator():
    """归因标签多选分隔符（默认英文逗号，兼容多维表格多选字段）。"""
    return get_annotation_config().get("tag_separator", ",")


def get_batch_size():
    return int(get_batch_config().get("batch_size", 15))


def get_batch_prefix():
    return get_batch_config().get("batch_prefix", "batch-")


def get_batch_num_width():
    return int(get_batch_config().get("batch_num_width", 2))


def get_default_session():
    return get_paths().get("default_session", "0724")


def get_sessions_dir():
    return WORKSPACE_ROOT / get_paths().get("sessions_dir", "sessions/pairwise-gsb")


def get_deliverables_dir():
    return WORKSPACE_ROOT / get_paths().get("deliverables_dir", "deliverables/pairwise-gsb")


def get_batch_input_dir():
    return get_paths().get("batch_input_dir", "input")


def get_batch_output_dir():
    return get_paths().get("batch_output_dir", "output")


def get_batch_images_dir():
    return get_paths().get("batch_images_dir", "images")


def get_batch_input_file():
    return get_paths().get("batch_input_file", "items_行{row_start}-{row_end}.xlsx")


def get_batch_output_file():
    return get_paths().get("batch_output_file", "annotated_行{row_start}-{row_end}.xlsx")


def get_full_output_file():
    return get_paths().get("full_output_file", "annotated-full_行{row_start}-{row_end}.xlsx")


def get_image_file_pattern():
    return get_paths().get("image_file_pattern", "row_{row:03d}_{col_type}")


def get_deliver_keep_input_columns():
    return get_paths().get("deliver_keep_input_columns", ["序号", "prompt_cn", "prompt_en"])


def format_batch_input_file(row_start, row_end):
    return get_batch_input_file().format(row_start=row_start, row_end=row_end)


def format_batch_output_file(row_start, row_end):
    return get_batch_output_file().format(row_start=row_start, row_end=row_end)


def format_full_output_file(row_start, row_end):
    return get_full_output_file().format(row_start=row_start, row_end=row_end)


def format_image_filename(row, col_type, ext=".png", index=None):
    """生成图片文件名，如 row_005_图片1.png；同单元格多图时追加序号。"""
    safe_type = str(col_type).replace("/", "_").replace("\\", "_").strip()
    base = get_image_file_pattern().format(row=row, col_type=safe_type)
    if index and index > 1:
        base = f"{base}_{index}"
    return f"{base}{ext}"


def find_batch_input_file(batch_dir):
    """在批次目录中定位输入 Excel，兼容新旧命名。"""
    import glob as _glob
    d = os.path.join(str(batch_dir), get_batch_input_dir())
    for pattern in ("items*.xlsx", "*.xlsx"):
        files = sorted(_glob.glob(os.path.join(d, pattern)))
        if files:
            return files[0]
    return None


def find_batch_output_file(batch_dir):
    """在批次目录中定位标注输出 Excel，兼容新旧命名。"""
    import glob as _glob
    d = os.path.join(str(batch_dir), get_batch_output_dir())
    for pattern in ("annotated*.xlsx", "*.xlsx"):
        files = sorted(_glob.glob(os.path.join(d, pattern)))
        if files:
            return files[0]
    return None


def get_batch_error_file():
    return get_paths().get("batch_error_file", "errors.txt")


def get_original_file():
    return get_paths().get("original_file", "original.xlsx")


def get_image_manifest():
    return get_paths().get("image_manifest", "manifest.json")


def get_difficult_cases_file():
    return get_paths().get("difficult_cases_file", "difficult-cases.xlsx")


def get_difficult_cases_log():
    return get_paths().get("difficult_cases_log", "difficult-cases-log.md")


def get_reviewed_dir():
    return get_paths().get("reviewed_dir", "reviewed")


def get_max_error_rate():
    return float(get_quality_config().get("max_error_rate", 0.0))


def get_undecided_warn_threshold():
    return float(get_quality_config().get("undecided_warn_threshold", 0.6))


def get_audit_sample_rate():
    return float(get_quality_config().get("audit_sample_rate", 0.1))


def session_date_dir(session, date):
    """返回 sessions/pairwise-gsb/<session>/<date> 的绝对路径。"""
    return get_sessions_dir() / session / date


def deliverable_date_dir(session, date):
    """返回 deliverables/pairwise-gsb/<session>/<date> 的绝对路径。"""
    return get_deliverables_dir() / session / date


def batch_name(index):
    """返回批次名，如 batch-01。"""
    return f"{get_batch_prefix()}{index:0{get_batch_num_width()}d}"


def build_column_index_map(headers):
    """
    根据 Excel 表头构建列名→列号映射。

    Args:
        headers: 表头列表（第一行单元格值）

    Returns:
        dict: {列名: 1-based 列号}
    """
    return {str(h).strip(): i for i, h in enumerate(headers, start=1) if h is not None}


def get_column_indices(headers, required_columns=None):
    """
    从表头中提取所需列的索引。

    Args:
        headers: 表头列表
        required_columns: 需要的列名列表，默认使用 input_columns + output_columns

    Returns:
        dict: {列名: 1-based 列号}，仅包含实际存在的列
    """
    col_map = build_column_index_map(headers)
    if required_columns is None:
        required_columns = get_input_columns() + get_output_columns()
    return {name: col_map[name] for name in required_columns if name in col_map}
