"""
GSB 提示词文件生成器
根据配置生成对话内容文件和评价结果文件。
支持任意数量的模型。
"""

import os
from config_loader import load_config
from path_resolver import (
    ensure_result_dirs,
    get_dialogue_file_path,
    get_review_file_path,
)


def generate_dialogue_template(project_name: str, task_type: str, prompt_text: str,
                                constraints: list, config: dict = None) -> dict:
    """
    生成所有模型的对话内容文件。
    返回 {"created": [path, ...], "skipped": [path, ...]}
    """
    cfg = config or load_config()
    max_rounds = cfg.get("max_rounds", 3)
    models = cfg.get("models", [])
    suffix = cfg.get("dialogue_suffix", "对话内容")
    type_safe = task_type.replace(" ", "")

    ensure_result_dirs(project_name, task_type, cfg)

    created = []
    skipped = []

    # 若未传入约束，默认使用配置中的全部5种约束类型（带占位提示）
    if not constraints:
        constraints = [f"{t}：<具体约束内容>" for t in cfg.get("constraint_types", [])]

    constraint_lines = "\n".join([f"- {c}" for c in constraints])

    # 构建轮次模板（从第2轮开始，因为第1轮已在文件头部）
    rounds_lines = []
    for r in range(2, max_rounds + 1):
        cn_num = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][r] if r <= 10 else str(r)
        rounds_lines.append(f"\n用户第{cn_num}次提示词：\n")
        rounds_lines.append(f"\n模型第{cn_num}次回答 trae session id：\n")
        rounds_lines.append(f"\n模型第{cn_num}次回答内容：\n")

    # 构建第一轮固定内容（包含 session id 和回答内容占位）
    first_round = """\n模型第一次回答 trae session id：\n\n模型第一次回答内容：\n"""

    # 最后一轮 context 占用记录（本期新增必填字段）
    context_usage_field = """\n\n最后一轮 context 占用：<X% of YK>（如触发自动压缩，则记录“在第 N 轮触发了自动压缩”）\n"""

    rounds_text = first_round + "\n".join(rounds_lines) + context_usage_field

    for m in models:
        slug = m.get("slug", "")
        if not slug:
            continue
        path = get_dialogue_file_path(project_name, task_type, slug, cfg)
        if os.path.exists(path):
            skipped.append(path)
            continue

        # 代码理解类型特殊提示
        type_hint = ""
        if "代码理解" in task_type:
            type_hint = "\n【类型强制要求：代码理解任务必须将理解过程输出为新的 .md 文件并提交到仓库】\n"

        content = f"""{project_name}-{type_safe}-01

用户第一次提示词：{prompt_text}

约束标签：
{constraint_lines}

注：约束标签必须包含上述全部 5 种类型，固定格式为『约束类型：内容』。{type_hint}

是否开启 Max：<是 / 否>（本期要求同一题三个模型保持一致）
{rounds_text}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)

    return {"created": created, "skipped": skipped}


def generate_review_template(project_name: str, task_type: str, config: dict = None) -> dict:
    """
    生成所有模型的评价结果文件。
    返回 {"created": [path, ...], "skipped": [path, ...]}
    """
    cfg = config or load_config()
    max_rounds = cfg.get("max_rounds", 3)
    models = cfg.get("models", [])
    dimensions = cfg.get("review_dimensions", ["提示词理解准确度", "技术深度", "回答完整性"])
    suffix = cfg.get("review_suffix", "评价结果")
    type_safe = task_type.replace(" ", "")

    ensure_result_dirs(project_name, task_type, cfg)

    created = []
    skipped = []

    round_blocks = []
    for r in range(1, max_rounds + 1):
        cn_num = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][r] if r <= 10 else str(r)
        dim_lines = "\n".join([f"{d}：" for d in dimensions])
        round_blocks.append(f"""## 第{cn_num}轮评价

{dim_lines}

## Session ID

【必须原文逐字复制，禁止改写】

""")
    rounds_text = "\n\n".join(round_blocks)

    for m in models:
        slug = m.get("slug", "")
        name = m.get("name", "")
        if not slug:
            continue
        path = get_review_file_path(project_name, task_type, slug, cfg)
        if os.path.exists(path):
            skipped.append(path)
            continue

        content = f"""{project_name}-{type_safe}-{slug}-{suffix}

模型：{name}（分支：{slug}）

{rounds_text}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)

    return {"created": created, "skipped": skipped}


def generate_all(project_name: str, task_type: str, prompt_text: str = "",
                  constraints: list = None, config: dict = None) -> dict:
    """
    同时生成对话内容文件和评价结果文件。
    """
    cfg = config or load_config()
    d_result = generate_dialogue_template(project_name, task_type, prompt_text, constraints or [], cfg)
    r_result = generate_review_template(project_name, task_type, cfg)
    return {
        "dialogue": d_result,
        "review": r_result,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python prompt_file_generator.py <project_name> <task_type> [prompt_text]")
        sys.exit(1)
    pname = sys.argv[1]
    ttype = sys.argv[2]
    ptext = sys.argv[3] if len(sys.argv) > 3 else ""
    cons = sys.argv[4].split("|") if len(sys.argv) > 4 else []
    result = generate_all(pname, ttype, ptext, cons)
    print("Dialogue files:", result["dialogue"])
    print("Review files:", result["review"])
