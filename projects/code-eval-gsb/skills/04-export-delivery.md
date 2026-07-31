---
name: gsb-export-delivery
description: "GSB 交付导出：汇总分析完成后，把评价汇总表单追加为一行记录到交付 Excel（【成都】GSB0731.xlsx）。Use when: GSB 导出, 交付表追加, 汇总入库, 交付 Excel。"
---

# GSB 交付导出 · 追加记录到交付 Excel

> 配置从 `../config.toml` 读取。
> 脚本：`scripts/code-eval-gsb/append_delivery.py`（依赖 openpyxl，使用工作台 `.venv`）

每次 `analyze` 汇总完成、用户确认评价汇总表单后执行本技能：把表单内容映射为交付 Excel 的一行，追加到 `docs/【成都】GSB0731.xlsx` 的「数据表」。

## 功能概述

1. 读取该题的 `-评价汇总.md`（必须是人工核对后的最终版）
2. 按交付表 104 列逐列映射，生成记录 JSON
3. 调用 `append_delivery.py` 先 `--dry-run` 校验，再正式追加
4. 输出追加结果（行号、留空列清单），提示用户核对

**本技能不负责：**

- 生成或修改评价汇总表单（由 `03-summary-analysis.md` 完成）
- 替人工确认评分（表单中残留占位标记时中止）

## 命令

| 命令 | 说明 |
|------|------|
| export | 默认命令。评价汇总表单 → 追加一行到交付 Excel |

## 执行流程

**输入：**
```
项目名：<项目名>
类型：<类型>
提交人：<姓名>
TraeCN用户ID：<ID>
```

**步骤：**

1. **读取评价汇总表单**：
   `{work_root}/{session}/ai-model-result/<项目名>/<项目名>-{ALIAS}/A-<项目名>-{ALIAS}-评价汇总.md`

2. **完成度检查（不满足则中止）**：
   - 表单中不得残留 `【待用户填写】` / `【参考值，请确认】` 占位标记
   - 4 个模型的 SessionID、交互轮次、是否触发自动压缩、context 占用必须齐全
   - 3 组 GSB 结论、4 条「评价模型 XXX」必须齐全
   - context ≥ 200K 的模型，长上下文保持能力的评分/问题标签/理由必须齐全；未达 200K 的理由必须为 `N/A`

3. **生成记录 JSON**：写入 `/tmp/<项目名>-{ALIAS}-delivery.json`，键名与 Excel 表头**逐字一致**，映射规则见下节。

4. **校验并追加**（在工作台根目录执行）：

   ```bash
   # 首次使用先建环境（已有 .venv 则跳过）
   python3 -m venv .venv && .venv/bin/pip install openpyxl

   # 先 dry-run 校验列名与留空情况
   .venv/bin/python scripts/code-eval-gsb/append_delivery.py \
     --xlsx "projects/code-eval-gsb/docs/【成都】GSB0731.xlsx" \
     --json /tmp/<项目名>-{ALIAS}-delivery.json --dry-run

   # 确认无误后正式追加
   .venv/bin/python scripts/code-eval-gsb/append_delivery.py \
     --xlsx "projects/code-eval-gsb/docs/【成都】GSB0731.xlsx" \
     --json /tmp/<项目名>-{ALIAS}-delivery.json
   ```

   - 脚本按「Github Repo」查重，重复时需用户确认后加 `--force`
   - 「提交时间」缺省由脚本自动填入当前时间

5. **输出结果**：追加的行号 + 留空列清单，提示用户在 Excel 中抽查该行。

## 字段映射规则

### 基础信息（A-K 列）

| Excel 列 | 来源 |
|----------|------|
| Prompt | 表单「Prompt」段原文（首轮提示词，含约束标签） |
| 提交时间 | 脚本自动填充，无需提供 |
| 提交人 | 用户输入 |
| Github Repo | 表单「环境信息」 |
| Repo介绍 | 表单「环境信息」 |
| 任务类型 | 表单「题目标签」（用标准类型名，不用别名） |
| 业务领域 | 表单「题目标签」 |
| 修改范围 | 表单「题目标签」 |
| 指令约束（多选） | 表单的约束标签列表，顿号连接（如：技术栈或依赖约束、业务逻辑约束） |
| 指令约束种类数（左边选了几个标签就填几个） | 约束标签数量 N |
| 操作系统 | 表单「题目标签」 |

### 模型区块（每模型 21 列，键名格式 `{字段} - {模型名}`）

⚠️ Excel 中模型区块顺序为 **Natasha → Thor → Steve → Tony**（与 config.toml 顺序不同），按键名映射即可，与列顺序无关。

| 字段 | 来源（表单 item 段） |
|------|------|
| SessionID | 原文复制，禁止改写 |
| GithubPR | PR 链接 / N/A |
| 交互轮次 | N（3-6） |
| 交付完整性 / 指令遵循 / 任务规划 / 推理能力 / 边界感 | 1-5 |
| 是否打断模型 | 是 / 否 |
| 打断分析反馈 | 有则填（Natasha 列表头为 `打断分析反馈 -Natasha`，无空格，照原样写键名） |
| 是否触发自动压缩 | 是 / 否 |
| context占用 | 统一格式：`X% of YK` 或 `X% of YK，触发自动压缩时 Z% of YK` |
| 长上下文保持能力 | 1-5；未达 200K 留空 |
| 出现的问题(长上下文) | 多选标签，顿号连接；未达 200K 留空 |
| 打分理由(长上下文) | 理由原文；未达 200K 填 `N/A` |
| 思考效率 | 1-5 |
| 出现的问题(思考) | 多选标签，顿号连接 |
| 打分理由(思考) | 理由原文 |
| ToolCall效率 | 1-5 |
| 出现的问题(ToolCall) | 多选标签，顿号连接 |
| 打分理由(ToolCall) | 理由原文（须含出问题的工具名） |

### GSB 与评价（CR-CZ 列）

| Excel 列 | 来源 |
|----------|------|
| Natasha和Steve谁更好 | GSB「Steve vs Natasha」的胜出模型名 |
| Thor和Steve谁更好 | GSB「Steve vs Thor」的胜出模型名 |
| Tony和Steve谁更好 | GSB「Steve vs Tony」的胜出模型名 |
| 评价模型Natasha / 评价模型Thor / 评价模型Steve / 评价模型Tony | 表单「评价模型」段，每题必填 4 条。固定格式：首行 Bad Pattern 概括（无则「无明显Bad Pattern 。」），随后按编号逐个对比其余每个模型（「N、与X对比：更好/差一点，理由」） |
| 其它信息 | 表单「其它信息备注」（含美观度，如有） |
| TraeCN用户ID | 用户输入 |

## 注意事项

1. **必须先 dry-run 再正式追加**；dry-run 输出的留空列清单需人工过目，确认留空都是"本就无数据"而非漏映射。
2. 键名与表头逐字一致（含空格、全角括号），脚本对未知键名直接报错。
3. 交付 Excel 是最终交付物，追加前确认表单已定稿；追加错误行需在 Excel 中手动删除后重新导出。
4. 所有评价文字已在 analyze 阶段经 humanizer-zh 处理，导出时**原文搬运，不得再改写**。
