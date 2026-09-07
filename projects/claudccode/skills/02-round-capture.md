---
name: claudccode-round-capture
description: "claudccode 单轮录入：一轮交互后创建/回填该轮数据文件（一轮=一条数据），含 User Prompt/TurnID/任务类型/难度/语言框架。Use when: claudccode 录入单轮, 回填对话, TurnID, 每轮一条数据。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取。路径变量同 [01-task-create](01-task-create.md)。

# claudccode 单轮录入

## 功能概述

用户在某任务（会话窗口）内完成**一轮** Claude Code / Codex 交互后，把该轮的提交字段录成一条独立数据文件（`{TASK_ID}-R{NN}.md`）。

每轮创建/更新一个数据文件 = 后续导出一行。

**不负责**：在 Claude Code / Codex 中代跑对话；撰写五维打分与依据（那是 `03-score-annotate`：人工撰写或 AI 起草→去 AI 化→人工复核）。

## 命令

| 命令 | 说明 |
|------|------|
| round `<N>` | 默认。录入第 N 轮（N=1..10） |
| list | 列出任务已录入的轮次与字段完整性 |

## 输入（round N 需向用户确认）

- 第 N 轮 User Prompt（**完整 prompt 原文，直接粘贴，不摘要不改写**；带附件/图片/选中代码时，末尾补一句说明）
- TurnID/PromptID（Codex：本轮 `task_started` 的 turn_id；Claude Code：本轮 user 消息的 promptId）
- 任务类型（按本轮主要意图单选，7 选 1）
- 任务难度（4 选 1）
- 语言/框架（本轮实际主要涉及，多个逗号分隔）
- 轨迹信息（从 `task-info.md` 继承 SessionID/轨迹根目录；轨迹目录须按 Harness 分行：Codex CLI→`~/.codex/sessions`、Claude Code→`~/.claude/projects`，仅当会话更换时更新）

## 执行流程

1. **确认任务与轮次**：读 `{RECORD_DIR}/{TASK_ID}/task-info.md` 校验存在；计算已有轮次。
   - 若 N > 已有最大轮次 + 1 → 提示中间有缺失轮次。
   - 若 N > `[limits].max_rounds`（10）→ **中止**：会话满 10 轮必须开新任务，不再录入。
2. **创建/回填数据文件** `{RECORD_DIR}/{TASK_ID}/{TASK_ID}-R{NN}.md`（NN 两位补零），按模板 `templates/round-file.md`：
   - 用模板 `templates/round-file.md` 的字段写入：User Prompt、任务类型、任务难度、语言/框架、TurnID/PromptID、模型回答存档（可选）、SessionID 引用（从 task-info 继承，不重复落盘）。
3. **SessionID 首次回填 + 轨迹根定位**：若 `task-info.md` 中 SessionID 为空，提示用户提供并回填（同一道题所有轮次同一值）；同时按 Harness 定位/校验「轨迹根目录」：Codex CLI → `~/.codex/sessions/<SessionID>`，Claude Code → `~/.claude/projects/<项目目录名>/<SessionID>`，与已填不符则提示修正。
4. **校验**（机械性）：
   - 任务类型在 7 类内；难度在 4 级内；语言/框架非空
   - 首轮（N=1）难度≠「简单」；后续轮难度可为「简单」（仅限因模型产物差产生的简单 bugfix）
   - TurnID 在该任务内唯一（不同轮次取值互不相同）
   - 轨迹根目录与 Harness 前缀对应（Codex→`~/.codex/sessions`、Claude Code→`~/.claude/projects`）
   - User Prompt 非空且为原文长度（过短 → 提示可能被摘要）
5. 输出文件路径，提示用户执行 `score <N>` 打分。

## 轮次口径（重要）

- 一轮 = 一次交互（用户提问 + 模型回答）。
- 显然的工程故障（网络波动/模型不稳定导致请求失败）**不计轮次**，可不提交该轮。
- **思考次数超限需人为「继续」→ 计入轮次**（这也是有效数据：prompt 写「继续」，类型/难度综合上一轮原始需求判断）。
- 对话满 10 轮后无论模型是否完成任务，都不应继续引导；应创建新任务（新会话窗口）。

## 路径规则

```
任务信息：{RECORD_DIR}/{TASK_ID}/task-info.md
第 N 轮数据：{RECORD_DIR}/{TASK_ID}/{TASK_ID}-R{NN}.md
```

## 示例

### 输入

```
任务 cc-1，录入第 2 轮
User Prompt: 用户输入了"继续"
TurnID: <Codex turn_id / Claude promptId>
任务类型: Bug修复
任务难度: 简单
语言/框架: Python
```

### 输出

```
已创建 records/cc-1/cc-1-R02.md
说明：本任务第 2 轮难度=简单，满足「后续轮次中因模型产物质量不佳而产生的简单 bugfix 可提交」
下一步：执行 score 2 进行五维打分
```

## 注意事项

1. User Prompt 必须原文逐字，禁止改写/摘要；这是质检回看轨迹的锚点。
2. TurnID/PromptID 唯一且必须准确回填——一旦填错/漏填，该轮产物无从追溯。
3. 每轮独立数据：即使同一任务，各轮分开成文件，导出每轮一行。
4. 不覆盖已存在轮次文件（已存在 → 提示确认或走 score/修正流程）。
5. 若 agent 代为起草「继续/追问」类话术，须先经 `skills/humanizer-zh/SKILL.md` 去 AI 化 + 人工确认后，才作为下一轮 User Prompt 录入。
