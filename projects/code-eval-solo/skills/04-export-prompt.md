---
name: solo-export-prompt
description: "Solo 提示词导出：把原始提示词文件中的轮次信息导出为 CSV（仅导出含 trae session id 的轮次），并与主 export 做 Session ID 一致性校验。Use when: 导出提示词, Trae Session ID 汇总。"
---

> 配置从 `../config.toml` 读取。路径变量同 [01-prompt-generate](01-prompt-generate.md)。
> 依赖脚本：`scripts/code-eval-solo/export_prompt_csv.py`、`scripts/code-eval-solo/compare_exports.py`

# Solo 提示词导出

## 功能概述

读取原始 `.md` 提示词文件，将每个带有 `trae session id` 的对话轮次提取并汇总为 CSV，并与主 export 做全字段对比。

**仅当某轮存在 trae session id 时才输出 CSV 一行。**

## 执行流程

### 步骤 1：确认扫描范围

单个项目目录 / 某个 ai-model-result 根目录下所有项目 / 用户指定路径。

### 步骤 2：确定输出路径

- 单项目：`deliverables/code-eval-solo/{SESSION_NAME}/{项目名}/csv-{项目名}-prompt-export.csv`
- 批量：`deliverables/code-eval-solo/{SESSION_NAME}/{批次名}/csv-{批次名}-prompt-export.csv`

### 步骤 3：执行导出

```bash
python scripts/code-eval-solo/export_prompt_csv.py
```

### 步骤 4：对比两份导出（强制）

用 `compare_exports.py` 逐行对比提示词导出与评价结果导出，**Session ID 以提示词文件为准**：

```bash
python scripts/code-eval-solo/compare_exports.py <prompt_csv> <eval_csv>
```

对比维度：
- **Session ID 匹配**：以提示词导出的 Session ID 为权威，找出仅在某一侧存在的行
- **Repo ID 一致性**：对比两边的 Repo ID 是否相同
- **User Prompt 一致性**：对比两边的提示词原文是否一致

输出格式：
```
🔴 仅在提示词导出中存在（评价结果缺失）: N 条
🟡 仅在评价结果中存在（提示词未导出）: N 条
🔴 字段不匹配: N 条（以提示词导出值为准）
✅ 完全一致
```

### 步骤 5：修正不匹配项

若存在差异：
- **仅提示词导出有、评价结果缺失** → 评价结果文件可能未填写 Session ID，需补填
- **仅评价结果有、提示词未导出** → 提示词文件中 Session ID 格式有误（需 20 位以上 hex）
- **字段不匹配** → 以提示词文件中的值为准，修正评价结果文件

修正后重新对比，直至 `✅ 完全一致`，**禁止跳过**。

## CSV 输出字段

`Repo ID`, `Trae Session ID`, `User Prompt`

## Python 脚本核心逻辑

```python
import csv, os, re, glob

HEADERS = ['Repo ID', 'Trae Session ID', 'User Prompt']

def extract_rounds_from_prompt_file(file_path):
    """从单个提示词文件中提取所有带有 trae session id 的轮次"""
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    # 定位用户提示词、session id、回答内容标记行
    # 提取 session id（必须包含 20 位以上连续十六进制字符）
    # 仅导出存在有效 session id 的轮次
    ...

def main():
    # 扫描所有 .md 文件（排除 *-评价结果.md）
    # 逐文件提取轮次，生成 CSV
    ...
```

## 注意事项

1. 只导出含有效 trae session id 的轮次。
2. excel-diff 对比是强制步骤，不可跳过。
3. 若 session id 不含 20 位以上十六进制字符（如误提取了"修改范围:"），跳过该轮。
