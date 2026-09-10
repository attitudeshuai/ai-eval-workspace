---
name: cc-solo-round-capture
description: "cc-solo 单轮录入：一轮交互后创建/回填该轮数据文件（一轮=一条数据），含 User Prompt/TurnID/任务类型/难度/语言框架。SessionID 与 TurnID 可由 agent 从轨迹自取（Claude Code 读容器导出到本机的 `{任务}-trajectory.jsonl`），也支持人工覆盖。Use when: cc-solo 录入单轮, 回填对话, TurnID, 每轮一条数据。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取。路径变量同 [01-task-create](01-task-create.md)。
> 依赖 agent：`skills/humanizer-zh/SKILL.md`（去 AI 化，代起草「继续」等话术必用）

# cc-solo 单轮录入

## 功能概述

用户在某个任务（会话窗口）内完成**一轮** Claude Code 交互后，把该轮的提交字段录成一条独立数据文件（`{任务}-R{NN}.md`）。

每轮创建/更新一个数据文件 = 后续导出一行。

**关键**：SessionID 与 TurnID/PromptID **不必用户手动回填**——agent 可直接读取轨迹文件定位（Claude Code 读容器导出到本机的轨迹，见下「会话轨迹与轮次识别」）。仅在轨迹无法读取或用户要求时，才人工补充这三项。

**不负责**：在 Claude Code 中代跑对话；撰写五维打分与依据（那是 `03-score-annotate`：人工撰写或 AI 起草→去 AI 化→人工复核）。

## 命令

| 命令 | 说明 |
|------|------|
| round `<N>` | 默认。录入第 N 轮（N=1..10） |
| list | 列出任务已录入的轮次与字段完整性 |

## 输入（round N 需向用户确认）

用户只需给 `cc {任务} round N`，以下全部由 agent 从轨迹/仓库自动推断（有疑问才回问确认）：

- User Prompt（**完整 prompt 原文**，从轨迹 `type==user` 且 content 为字符串的条目取）
- TurnID/PromptID（Claude Code：本轮 user 消息的 promptId）
- SessionID（同一任务所有轮同一值）
- 任务类型（按本轮主要意图单选，7 选 1）
- 任务难度（4 选 1，人类视角）
- 语言/框架（本轮实际主要涉及，多个逗号分隔；从轨迹/仓库推断，须人工确认）

## 会话轨迹与轮次识别（自取 SessionID / TurnID）

轨迹文件按「哪个 CLI 做的」分行存放（`config.toml [trajectory]`）：

- **Claude Code（在 docker 容器 `cc-solo-{任务}` 里做）**：由 agent 用 `docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/." {RECORD_DIR}/{项目}/{项目}-{类型}/{任务}/` 把容器内轨迹导出到本机任务记录目录（见 runbook.md / runbook-windows.md 第 3 步），本题的会话文件是**一个 `.jsonl`**，文件名 UUID = `SessionID`。**题目身份 = 容器名（`cc-solo-{任务}`）+ 挂载的本机运行目录**；容器内路径不含题号（详见 [../docs/image-upgrade-review.md](../docs/image-upgrade-review.md)）。


### 1. 定位会话（SessionID）

Claude Code（容器）的轨迹是**一个 `.jsonl` 文件**，文件名 UUID 就是 `SessionID`。**一个容器 = 一道题 = 一个会话**，所以该容器 `-workspace/` 下那个 `.jsonl` 就是本题的会话文件；容器内工作目录恒为 `/workspace`，轨迹目录恒为 `/home/node/.claude/projects/-workspace/`。例如：

```
任务 app-12-codegen-06  →  容器 cc-solo-app-12-codegen-06，容器内工作目录 /workspace
→ 容器内轨迹目录 /home/node/.claude/projects/-workspace/
→ 导出到本机 records/app-12/app-12-codegen/app-12-codegen-06/91598858-1626-4537-a317-e397e3aaf56d.jsonl
→ SessionID = 91598858-1626-4537-a317-e397e3aaf56d
```

> 找不到时：先 `docker ps -a --filter name=cc-solo-` 定位本题容器，再 `docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/." <目标目录>/`。若该目录下出现**多个 `.jsonl`**，说明容器被复用了（新版 Mac 镜像本就拒绝在同一容器里开第二次会话），按 `task-info.md` 记录的 SessionID 取本轮那份并回报异常。

### 2. 拆轮次（一轮 = 一次用户键入）

在 `.jsonl` 里，**用户键入**的条目是：

```
type == "user" 且 message.content 是字符串（用户实际输入的那段文字）
```

这类条目的 `promptId` 字段就是该轮的 **TurnID**。注意区分：

- **同一次键入会产生很多 `type==user` 的「工具结果回填」条目**（`message.content` 为数组/非字符串），它们**复用同一个 promptId**，**不算新轮次**。
- 只有 `content` 为字符串的 user 条目才是一个轮次的起点；它之后、下一次键入之前的所有 assistant 工具调用/回复，都归属本轮。

按「用户键入序号」计数 = 轮次：第 1 条键入 = 第 1 轮（R01），第 2 条 = 第 2 轮（R02）……（≤ 10）。

> **一个会话窗口（SessionID）的所有轮次都记录在同一个 `.jsonl` 轨迹文件里**（就是那个 `<SessionID>.jsonl`，随轮次追加）。**SessionID 各轮相同；每一轮的 user 键入条目各有自己独立的 `promptId`（TurnID），各轮互不相同**。（工具结果回填复用所属轮次的 promptId，不产生新 TurnID。）

> 若用户在 Claude Code 里只发了一条消息、模型一直在工具循环，那是**一轮**；若两次键入之间无任何新产出，由人工判断是否合并为同一轮。认不准时人工确认，不硬拆。

### 3. 语言/框架与难度建议

从轨迹推断：本轮实际改动的文件后缀/引入的依赖、仓库技术栈可判断语言/框架；难度按人类视角判断（首轮严禁「简单」）。这属于判断项，**须人工确认后落盘**。

## 执行流程

0. **导出本轮轨迹（agent 执行 docker 命令）**：
   - 等模型答完、静止时再导（别在它正跑工具时拷，否则最新几条不完整）。
   - 导出轨迹：`docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/." {RECORD_DIR}/{项目}/{项目}-{类型}/{任务}/`（Windows PowerShell 把 `/` 换成 `\`；容器已停止时也能导出）。
   - **代码产物不需要回导**：容器 `/workspace` 就是本机挂载目录（Mac 是本题运行目录、Windows 是任务副本目录），模型改完的代码已经在盘上。任务收尾时再由 agent 按 `.gitignore` 排除依赖包（node_modules/.venv/__pycache__/dist 等），把源码同步/回导到任务副本 `{REPO_BASE_PATH}/{项目}/{项目}-{类型}/{任务}/`，供打分环节做 git diff 对照。
1. **确认任务与轮次**：读 `{RECORD_DIR}/{项目}/{任务}/task-info.md` 校验存在；计算已有轮次。
   - 若 N > 已有最大轮次 + 1 → 提示中间有缺失轮次。
   - 若 N > `[limits].max_rounds`（10）→ **中止**：会话满 10 轮必须开新任务，不再录入。
2. **定位本轮 + 切片**：读取本机轨迹（Claude Code：刚导出的 `<SessionID>.jsonl`），按上面「拆轮次」找到第 N 轮 user 键入条目，取其 prompt 原文与 promptId；把第 N 轮那段（该 user 条目到下一个 user 条目之前，不含下一个）**切出来**存 `{RECORD_DIR}/{项目}/{任务}/{任务}-R{NN}-trajectory.jsonl`（**仅用于打分阶段定位单轮**）；完整会话保留为 `{RECORD_DIR}/{项目}/{任务}/{任务}-trajectory.jsonl`（**提交时的轨迹附件**：平台 `trace_file` 的 help_text 指向 `~/.codex/sessions/` 或 `~/.claude/projects/`，要的就是这份原始会话文件，配 SessionID + TurnID 定位到某一轮）。
   - 读取失败或用户明确要求 → 回到「输入」，向用户索要 SessionID/TurnID/User Prompt。
3. **创建/回填数据文件** `{RECORD_DIR}/{项目}/{任务}/{任务}-R{NN}.md`（NN 两位补零），按模板 `templates/round-file.md` 写入：User Prompt（原文）、任务类型、任务难度、语言/框架、TurnID/PromptID、模型回答存档（可选）。
4. **SessionID/轨迹根目录回填**：若 `task-info.md` 中 SessionID 为空 → 用本步解析到的 SessionID 回填，并按 Harness 分行定位「轨迹根目录」（Claude Code → 本机 `records/{项目}/{任务}/{任务}-trajectory.jsonl`，来源容器 `cc-solo-{任务}` 的 `/home/node/.claude/projects/-workspace/<SessionID>.jsonl`），同任务所有轮同一值。
5. **校验**（机械性）：
   - 任务类型在 7 类内；难度在 4 级内；语言/框架非空
   - 首轮（N=1）难度≠「简单」；后续轮难度可为「简单」（仅限因模型产物差产生的简单 bugfix）
   - TurnID 在该任务内唯一（不同轮次取值互不相同）
   - 轨迹根目录与 Harness 前缀对应（Claude Code→本机导出的 `{任务}-trajectory.jsonl`）
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
任务记录目录（R0N 模型）：{RECORD_DIR}/{项目}/{项目}-{类型}/{项目}-{类型}-{索引}/
第 N 轮数据（含五维打分）：…/{项目}-{类型}-{索引}-R{NN}.md
第 N 轮轨迹切片：…/{项目}-{类型}-{索引}-R{NN}-trajectory.jsonl
完整轨迹：…/{项目}-{类型}-{索引}-trajectory.jsonl
素材源（唯一 git 仓库）：{REPO_BASE_PATH}/{项目}/
任务副本：{REPO_BASE_PATH}/{项目}/{项目}-{类型}/{项目}-{类型}-{索引}/   （模型输入；Windows 直接挂载为容器 /workspace）
容器：cc-solo-{任务}（1 容器 = 1 任务）
容器内工作目录：/workspace（= 本题任务副本内容；无题号层级）
容器内轨迹目录：/home/node/.claude/projects/-workspace/
其中 {项目} = 项目名（素材源目录名，如 app-12）；{项目}-{类型} = 类型分组目录；{索引} 全局累加两位补零。
```

## 示例

### 输入

```
任务 app-12-codegen，录入第 1 轮
（agent 已自取轨迹：SessionID/User Prompt/promptId 无需手贴）
任务类型: 0-1代码生成
任务难度: 困难
语言/框架: JavaScript
人工确认: 是
```

### 输出

```
已创建 records/app-12/app-12-codegen/app-12-codegen-R01.md
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
