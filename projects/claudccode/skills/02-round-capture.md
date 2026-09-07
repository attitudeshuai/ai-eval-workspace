---
name: claudccode-round-capture
description: "claudccode 单轮录入：一轮交互后创建/回填该轮数据文件（一轮=一条数据），含 User Prompt/TurnID/任务类型/难度/语言框架。SessionID 与 TurnID 可由 agent 从本机轨迹（~/.claude/projects 或 ~/.codex/sessions）自取，也支持人工覆盖。Use when: claudccode 录入单轮, 回填对话, TurnID, 每轮一条数据。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取。路径变量同 [01-task-create](01-task-create.md)。
> 依赖 agent：`skills/humanizer-zh/SKILL.md`（去 AI 化，代起草「继续」等话术必用）

# claudccode 单轮录入

## 功能概述

用户在某个任务（会话窗口）内完成**一轮** Claude Code / Codex 交互后，把该轮的提交字段录成一条独立数据文件（`{REPO}-R{NN}.md`）。

每轮创建/更新一个数据文件 = 后续导出一行。

**关键**：SessionID 与 TurnID/PromptID **不必用户手动回填**——agent 可直接读取本机轨迹文件定位（见下「会话轨迹与轮次识别」）。仅在轨迹无法读取或用户要求时，才人工补充这三项。

**不负责**：在 Claude Code / Codex 中代跑对话；撰写五维打分与依据（那是 `03-score-annotate`：人工撰写或 AI 起草→去 AI 化→人工复核）。

## 命令

| 命令 | 说明 |
|------|------|
| round `<N>` | 默认。录入第 N 轮（N=1..10） |
| list | 列出任务已录入的轮次与字段完整性 |

## 输入（round N 需向用户确认）

- 第 N 轮 User Prompt（**完整 prompt 原文**；通常 agent 已从轨迹解析，无需手贴）
- TurnID/PromptID（Codex：本轮 `task_started` 的 turn_id；Claude Code：本轮 user 消息的 promptId；agent 自取，可覆盖）
- SessionID（同一任务所有轮同一值；agent 自取）
- 任务类型（按本轮主要意图单选，7 选 1）
- 任务难度（4 选 1）
- 语言/框架（本轮实际主要涉及，多个逗号分隔；agent 可从轨迹/仓库推断，但**须人工确认**）

## 会话轨迹与轮次识别（自取 SessionID / TurnID）

轨迹文件按「哪个 CLI 做的」分行存放（`config.toml [trajectory]`）：

- **Claude Code** → `~/.claude/projects/<项目目录名>/<SessionID>.jsonl`
- **Codex CLI** → `~/.codex/sessions/<SessionID>/`（里面是该会话的会话文件）

### 1. 定位会话（SessionID）

Claude Code 的记录是**一个 `.jsonl` 文件**，文件名 UUID 就是 `SessionID`。项目目录名 = 启动 Claude Code 时的工作目录，`/`、`.`、空格等换成 `-`。例如：

```
工作目录 sessions/claudccode/session-0907/repos/solocc-0001
→ ~/.claude/projects/-Users-lilixian------AI-ai-eval-workspace-sessions-claudccode-session-0907-repos-solocc-0001/
→ 里面放 91598858-1626-4537-a317-e397e3aaf56d.jsonl
→ SessionID = 91598858-1626-4537-a317-e397e3aaf56d
```

> 用 `find ~/.claude/projects -iname '*.jsonl' -path "*<repo>*"` 可快速命中该仓库的会话文件（相对路径含 `-repos-<repo>`）。

### 2. 拆轮次（一轮 = 一次用户键入）

在 `.jsonl` 里，**用户键入**的条目是：

```
type == "user" 且 message.content 是字符串（用户实际输入的那段文字）
```

这类条目的 `promptId` 字段就是该轮的 **TurnID**。注意区分：

- **同一次键入会产生很多 `type==user` 的「工具结果回填」条目**（`message.content` 为数组/非字符串），它们**复用同一个 promptId**，**不算新轮次**。
- 只有 `content` 为字符串的 user 条目才是一个轮次的起点；它之后、下一次键入之前的所有 assistant 工具调用/回复，都归属本轮。

按「用户键入序号」计数 = 轮次：第 1 条键入 = 第 1 轮（R01），第 2 条 = 第 2 轮（R02）……（≤ 10）。

> 若用户在 Claude Code 里只发了一条消息、模型一直在工具循环，那是**一轮**；若两次键入之间无任何新产出，由人工判断是否合并为同一轮。认不准时人工确认，不硬拆。

### 3. 语言/框架与难度建议

从轨迹推断：本轮实际改动的文件后缀/引入的依赖、仓库技术栈可判断语言/框架；难度按人类视角判断（首轮严禁「简单」）。这属于判断项，**须人工确认后落盘**。

## 执行流程

1. **确认任务与轮次**：读 `{RECORD_DIR}/{REPO}/task-info.md` 校验存在；计算已有轮次。
   - 若 N > 已有最大轮次 + 1 → 提示中间有缺失轮次。
   - 若 N > `[limits].max_rounds`（10）→ **中止**：会话满 10 轮必须开新任务，不再录入。
2. **定位本轮**：读取 `~/.claude/projects/<项目目录名>/<SessionID>.jsonl`（Claude Code）或 `~/.codex/sessions/<SessionID>`（Codex），按上面「拆轮次」找到第 N 轮的用户键入条目，取其 prompt 原文与 promptId；SessionID 取该轨迹所归属的会话。
   - 读取失败或用户明确要求 → 回到「输入」，向用户索要 SessionID/TurnID/User Prompt。
   - 把该会话的 `.jsonl` **复制一份**到 `{RECORD_DIR}/{REPO}/{REPO}-trajectory.jsonl`（重命名为仓库名，交付/上传用；`~/.claude/projects/...` 原始文件保留）。
3. **创建/回填数据文件** `{RECORD_DIR}/{REPO}/{REPO}-R{NN}.md`（NN 两位补零），按模板 `templates/round-file.md` 写入：User Prompt（原文）、任务类型、任务难度、语言/框架、TurnID/PromptID、模型回答存档（可选）。
4. **SessionID/轨迹根目录回填**：若 `task-info.md` 中 SessionID 为空 → 用本步解析到的 SessionID 回填，并按 Harness 分行定位「轨迹根目录」（Claude Code → `~/.claude/projects/<项目目录名>/<SessionID>`；Codex → `~/.codex/sessions/<SessionID>`），同任务所有轮同一值。
5. **校验**（机械性）：
   - 任务类型在 7 类内；难度在 4 级内；语言/框架非空
   - 首轮（N=1）难度≠「简单」；后续轮难度可为「简单」（仅限因模型产物差产生的简单 bugfix）
   - TurnID 在该任务内唯一（不同轮次取值互不相同）
   - 轨迹根目录与 Harness 前缀对应（Codex→`~/.codex/sessions`、Claude Code→`~/.claude/projects`）
   - User Prompt 非空且为原文长度（过短 → 提示可能被摘要）
6. 输出文件路径，提示用户执行 `score <N>` 打分。

## 轮次口径（重要）

- 一轮 = 一次交互（用户键入 + 模型回答）。
- 显然的工程故障（网络波动/模型不稳定导致请求失败）**不计轮次**，可不提交该轮。
- **思考次数超限需人为「继续」→ 计入轮次**（有效数据：prompt 写「继续」，类型/难度综合上一轮需求判断）。
- 对话满 10 轮后无论模型是否完成任务，都不应继续引导；应创建新任务（新会话窗口）。
- 同一会话窗口（同 SessionID）内的多条数据，靠 `SessionID` 聚合回一道题；轮次用 `R{NN}` 区分。

## 路径规则

```
任务信息：{RECORD_DIR}/{REPO}/task-info.md
第 N 轮数据：{RECORD_DIR}/{REPO}/{REPO}-R{NN}.md
轨迹文件副本：{RECORD_DIR}/{REPO}/{REPO}-trajectory.jsonl   （交付/上传用；复制自真实轨迹并重命名为仓库名）
其中 {REPO} = 记录目录名 = 仓库目录名（repos/<repo> 的目录名），即本任务 ID。
```

## 示例

### 输入

```
任务 solocc-0001，录入第 1 轮
（agent 已自取轨迹：SessionID/User Prompt/promptId 无需手贴）
任务类型: 0-1代码生成
任务难度: 困难
语言/框架: JavaScript
人工确认: 是
```

### 输出

```
已创建 records/solocc-0001/solocc-0001-R01.md
SessionID=91598858-1626-4537-a317-e397e3aaf56d
TurnID/PromptID=cf4de94b-6fdd-4cb4-bcab-1d52076677ee
说明：首轮难度=困难，符合「首轮非简单」。
下一步：执行 score 1 进行五维打分
```

## 注意事项

1. User Prompt 必须原文逐字，禁止改写/摘要；这是质检回看轨迹的锚点。从轨迹解析到的 prompt 原文直接写入。
2. TurnID/PromptID 唯一且必须准确——一旦填错/漏填，该轮产物无从追溯。
3. 每轮独立数据：即使同一任务，各轮分开成文件，导出每轮一行。
4. 不覆盖已存在轮次文件（已存在 → 提示确认或走 score/修正流程）。
5. 若 agent 代为起草「继续/追问」类话术，须先经 `skills/humanizer-zh/SKILL.md` 去 AI 化 + 人工确认后，才作为下一轮 User Prompt 录入。
