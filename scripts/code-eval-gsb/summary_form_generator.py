"""
GSB 评价汇总表单生成器
根据配置和已有数据生成评价汇总表单骨架或完整表单。
"""

import os
import re
from config_loader import load_config
from path_resolver import get_dialogue_file_path, get_summary_file_path
from session_id_tool import extract_session_ids_from_dialogue


def extract_first_prompt_from_dialogue(dialogue_path: str) -> str:
    """从对话内容文件中提取首轮提示词（含约束标签）。"""
    if not os.path.exists(dialogue_path):
        return ""
    with open(dialogue_path, "r", encoding="utf-8") as f:
        text = f.read()
    # 找 "用户第一次提示词：" 之后到 "约束标签：" 或 "模型第一次" 之前
    m = re.search(
        r"用户第一次提示词[：:]\s*(.*?)(?=\n约束标签[：:]|\n模型第一次|\n注[：:]|\n是否开启 Max[：:]|\n模型第一次回答 trae session id[：:]|\Z)",
        text,
        re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    return ""


def extract_constraints_from_dialogue(dialogue_path: str) -> list:
    """从对话内容文件中提取约束标签列表。"""
    if not os.path.exists(dialogue_path):
        return []
    with open(dialogue_path, "r", encoding="utf-8") as f:
        text = f.read()
    constraints = []
    in_constraints = False
    for line in text.splitlines():
        if "约束标签" in line and (":" in line or "：" in line):
            in_constraints = True
            continue
        if in_constraints:
            if line.strip().startswith("-") or line.strip().startswith("*"):
                constraints.append(line.strip().lstrip("-* ").strip())
            elif line.strip() == "" or line.strip().startswith("注："):
                continue
            else:
                break
    return constraints


def extract_max_mode_from_dialogue(dialogue_path: str) -> str:
    """从对话内容文件中提取是否开启 Max。"""
    if not os.path.exists(dialogue_path):
        return ""
    with open(dialogue_path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"是否开启 Max[：:]\s*(.+)", text)
    if m:
        return m.group(1).strip()
    return ""


def extract_context_usage_from_dialogue(dialogue_path: str) -> str:
    """从对话内容文件中提取最后一轮 context 占用，并去掉末尾提示说明。"""
    if not os.path.exists(dialogue_path):
        return ""
    with open(dialogue_path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"最后一轮 context 占用[：:]\s*(.+?)(?:\s*（|\s*\(|\s*$)", text)
    if m:
        return m.group(1).strip()
    return ""


def generate_summary_skeleton(project_name: str, task_type: str,
                               repo_url: str = "", tech_stack: str = "",
                               config: dict = None) -> str:
    """
    生成评价汇总表单骨架（init 模式）。
    返回文件路径。
    """
    cfg = config or load_config()
    models = cfg.get("models", [])
    comparisons = cfg.get("comparisons", [])
    type_safe = task_type.replace(" ", "")

    summary_path = get_summary_file_path(project_name, task_type, cfg)
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)

    # 读取任意一份对话内容文件提取 prompt、约束、Max 开关
    first_prompt = ""
    constraints = []
    max_mode = ""
    for m in models:
        slug = m.get("slug", "")
        dpath = get_dialogue_file_path(project_name, task_type, slug, cfg)
        if os.path.exists(dpath):
            first_prompt = extract_first_prompt_from_dialogue(dpath)
            constraints = extract_constraints_from_dialogue(dpath)
            max_mode = extract_max_mode_from_dialogue(dpath)
            break

    # 构建 item 1-N
    item_blocks = []
    for idx, m in enumerate(models, 1):
        slug = m.get("slug", "")
        name = m.get("name", "")
        # 提取 session id
        session_id = "【用户待填写】"
        context_usage = ""
        dpath = get_dialogue_file_path(project_name, task_type, slug, cfg)
        if os.path.exists(dpath):
            text = open(dpath, "r", encoding="utf-8").read()
            sids = extract_session_ids_from_dialogue(text)
            if sids:
                session_id = sids[0][1] if sids[0][1] else "【用户待填写】"
            context_usage = extract_context_usage_from_dialogue(dpath)

        context_usage_display = context_usage if context_usage else "【待用户填写】"

        item_blocks.append(f"""---

## item {idx}. 评测详情：{name}

SessionID：{session_id}【⚠️ 原文复制，禁止推断或修改】
GithubPR：<PR 链接 / N/A>
交互轮次：<N>
最后一轮 context 占用：{context_usage_display}（如触发自动压缩，则记录“在第 N 轮触发了自动压缩”）

### 基础维度

交付完整性：<1-5>【参考值，请确认】
指令遵循：<1-5>【参考值，请确认】
任务规划：<1-5>【参考值，请确认】
推理能力：<1-5>【参考值，请确认】
边界感：<1-5>【参考值，请确认】

### Add-on 维度

长上下文保持能力：<1-5 / N/A>【参考值，请确认】（日常短窗口样本填 N/A）
- 出现的问题（长上下文）：<多选：前文约束遗忘 / 已改代码回退/重复劳动 / 路径幻觉（引用不存在文件等） / lost-in-the-middle（遗漏中段） / 前后自相矛盾 / 其他 / 未出现显著问题>
- 打分理由（长上下文）：<包含可定位证据（轮次+动作）、对交付/效率的具体影响、能力明显退化时的 context 占用百分比；选择「其他」需具体描述>

思考效率：<1-5>【参考值，请确认】
- 出现的问题（思考）：<多选：简单题过度思考 / 思考发散跑题 / 反复自我否定绕圈 / 思考不足直接猜 / 思考陷入死循环 / 其他 / 未出现显著问题>
- 打分理由（思考）：<包含可定位证据（轮次+动作）、对交付/效率的具体影响；选择「其他」需具体描述>

ToolCall效率：<1-5>【参考值，请确认】
- 出现的问题（ToolCall）：<多选：重复读取同一文件 / 文件间反复横跳 / 无效探索或无关调用 / 失败调用未能自行纠正 / 该用工具时不用 靠瞎猜 / 其他 / 未出现显著问题>
- 出现问题的工具名：<如涉及多个工具，填写所有工具名；无问题则填「无」>
- 打分理由（ToolCall）：<包含可定位证据（轮次+工具名称+动作+影响）、对交付/效率的具体影响；选择「其他」需具体描述>

平均分：<以上8项平均值（N/A 不计入），保留一位小数>【参考值，请确认】
Bad Pattern 识别：<列出该模型出现的 Bad Pattern 类型及具体表现；无则填「无」>
是否打断模型：<是 / 否>
打断分析反馈：<如有打断则说明（humanizer-zh 去 AI 化后），无则留空>
""")

    # 构建 GSB 对比块
    gsb_blocks = []
    gsb_start = len(models) + 1
    for idx, c in enumerate(comparisons, gsb_start):
        name = c.get("name", "")
        pair = c.get("pair", [])
        required = c.get("required", False)
        if len(pair) < 2:
            continue
        m1 = models[pair[0]] if pair[0] < len(models) else {}
        m2 = models[pair[1]] if pair[1] < len(models) else {}
        n1 = m1.get("name", "")
        n2 = m2.get("name", "")

        if not required:
            gsb_blocks.append(f"""---

## item {idx}. GSB：{n1} / {n2}

<!-- 本次评测未启用 {name} 对比时，填写「本次评测未启用 {name} 对比」；否则填写以下内容 -->

【强制】本期 GSB 不提供 Same 选项，必须明确分出高下。
【强制】GSB 结论必须与两模型平均分对齐：判定更好的模型，其平均分必须严格高于另一方。
【强制】每条 GSB 理由必须独立、具体，禁止在多组对比中复制同一套话术。
{n1} 和 {n2} 谁更好：<<{n1}> / <{n2}>>（必须二选一，禁止 same / 持平 / 一样好 / 各有优劣）
评价模型 {n2} 更好/更坏的原因：< {n1}更好，就说{n2}的更坏的点；{n2}更好，就说{n2}更好的点（humanizer-zh 去 AI 化后）>
评价模型 {n1} 更好/更坏的原因：< {n2}更好，就说{n1}的更坏的点；{n1}更好，就说{n1}更好的点（humanizer-zh 去 AI 化后）>
""")
        else:
            gsb_blocks.append(f"""---

## item {idx}. GSB：{n1} / {n2}

【强制】本期 GSB 不提供 Same 选项，必须明确分出高下。
【强制】GSB 结论必须与两模型平均分对齐：判定更好的模型，其平均分必须严格高于另一方。
【强制】每条 GSB 理由必须独立、具体，禁止在多组对比中复制同一套话术。
{n1} 和 {n2} 谁更好：<<{n1}> / <{n2}>>（必须二选一，禁止 same / 持平 / 一样好 / 各有优劣）
评价模型 {n2} 更好/更坏的原因：< {n1}更好，就说{n2}的更坏的点；{n2}更好，就说{n2}更好的点（humanizer-zh 去 AI 化后）>
评价模型 {n1} 更好/更坏的原因：< {n2}更好，就说{n1}的更坏的点；{n1}更好，就说{n1}更好的点（humanizer-zh 去 AI 化后）>
""")

    constraint_lines = "\n".join([f"{i + 1}. {c}" for i, c in enumerate(constraints)]) if constraints else ""
    max_mode_display = max_mode if max_mode else "<是 / 否>"

    content = f"""# {project_name}-{type_safe} 评价汇总

---

## Prompt

填入题目的完整 Prompt（仅需对话首轮）：
{first_prompt}【⚠️ 原文复制，不得修改】

---

## 环境信息

Github Repo：<{repo_url or "https://github.com/..."}>

Repo 介绍：<项目 README / 需求文档中的仓库介绍>

技术栈：<{tech_stack or "【待用户填写】"}>

---

## 题目标签

任务类型：{task_type}
业务领域：<从 business_domains 选择 / 【待用户填写】>
修改范围：<单文件 / 模块内多文件 / 跨模块多文件 / 跨系统多模块>
指令约束（多选）：
{constraint_lines}
指令约束种类数：<{len(constraints)}>
操作系统：<Windows / macOS / Linux / 【待用户填写】>
是否为长程任务：<是 / 否>
是否开启 Max：{max_mode_display}（三模型保持一致）

"""
    content += "\n".join(item_blocks)
    content += "\n"
    content += "\n".join(gsb_blocks)
    content += f"""
---

## 其它信息备注

是否对模型有一些特别的观点或注意到的现象希望模型方注意？

美观度：<有前端项目填 1-5 / 非 UI 类填 N/A>
"""

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(content)
    return summary_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python summary_form_generator.py <project_name> <task_type> [repo_url] [tech_stack]")
        sys.exit(1)
    pname = sys.argv[1]
    ttype = sys.argv[2]
    repo = sys.argv[3] if len(sys.argv) > 3 else ""
    tech = sys.argv[4] if len(sys.argv) > 4 else ""
    path = generate_summary_skeleton(pname, ttype, repo, tech)
    print(f"汇总表单已生成: {path}")
