---
name: claudccode-task-create
description: "claudccode 任务初始化：新建一个任务（会话窗口），打初始环境快照（commit permalink），填共享运行环境字段，起草首轮提示词。Use when: claudccode 新建任务, 满意度标注任务初始化, 初始快照, 出题。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取；`secrets.toml` 可覆盖 `active_session`、`repo_base_path`、`records_dir`、`annotator`。
> 依赖 agent：`skills/humanizer-zh/SKILL.md`（去 AI 化，AI 起草提示词必用）、`skills/prompt-architect/SKILL.md`（可选起草）
> 路径变量：`{work_root}`=`[paths].work_root`、`{SESSION_NAME}`=`[sessions].active`、`{RECORD_DIR}`=`{work_root}/{SESSION_NAME}/[paths].records_dir`、`{REPO_BASE_PATH}`=`{work_root}/{SESSION_NAME}/[paths].repo_base_path`、`{REPO}`=仓库目录名（`repos/<repo>` 的目录名，即项目/素材名）、`{TASK_ID}`=`{REPO}-{类型slug}`（任务 ID）。旧 `{TASK_PREFIX}` 已不再用于记录标识。

# claudccode 任务初始化

## 功能概述

为一个**任务（= 一个会话窗口，≤ 10 轮）**建立数据档案：

1. 校验被标注仓库（干净、无凭据泄漏、已 git init、可 push）
2. **打初始环境快照**：首轮交互前提交 baseline 并 push，记录 commit permalink（完整 40 位 SHA）
3. 建任务目录与 `task-info.md`（共享运行环境字段）
4. 起草**首轮提示词**（真实用户口径：AI 起草须先 humanizer-zh 去 AI 化，再人工确认后写盘）

**不负责**：在 Claude Code / Codex 中代跑对话；代替人工决定任务类型/难度。

## ⚠️ 出题与埋点要求（create 必守）

1. **首轮提示词必须「难」**：要能考出模型能力，做高难度、多需求、跨模块/多约束的题；严禁简单/单文件/纯函数级题目（对照 docs/annotate-guide.md §7 雷同题与「过于简单题判定」）。
2. **Bug修复 = 先埋点**：由出题人在**初始化/打快照阶段**把 bug **写进仓库源码**，使其成为初始状态（模型要修的正是它）。要求：
   - 埋的 bug 要**真实、可复现**，造成明显错误行为，但**不能加注释/标记说明「这是个 bug」**；
   - 埋点做成一段看似正常的逻辑改动，藏在业务代码里，别一眼看穿；
   - 首轮 prompt 只**以用户视角描述症状/现象**，不透露 bug 位置与根因；
   - 埋点后的 commit 即初始环境快照（permalink 指向它）。
3. **0-1代码生成 / Feature迭代**：首轮 prompt 作为**新项目/新模块或功能扩展**的最高要求，覆盖面要广、有明确的工程与质量约束（如 Docker、真实数据、禁 Mock、UI 规范等），体现难度。

## 命令

| 命令 | 说明 |
|------|------|
| create | 默认。校验仓库 → 打快照 → 建 task-info → 起草首轮提示词 |
| info | 仅校验仓库状态与展示将填写的字段，不写文件 |

## 默认配置

> 任务 ID = **`{REPO}-{类型slug}`**（如 `solocc-0001-codegen`）。记录目录与轮次文件都以它为前缀。同一仓库可开多个不同类型任务，各任务独立目录、独立快照、独立远程仓库。
> 类型 slug 对照（`config.toml [task_types].aliases`）：`0-1代码生成`→`codegen`、`Feature迭代`→`feat`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。
> 任务目录：`{RECORD_DIR}/{TASK_ID}/`；共享字段文件：`{RECORD_DIR}/{TASK_ID}/task-info.md`
> records 支持两层（可选）：`{RECORD_DIR}/{REPO}/{TASK_ID}/`（项目分组）或扁平 `{RECORD_DIR}/{TASK_ID}/`；导出脚本两种都认（含 `task-info.md` 的目录 = 任务）。任务 ID/题号始终扁平 `{REPO}-{slug}`。
> 仓库：用户给的**素材源**本地/远端路径（如 `{REPO_BASE_PATH}/{REPO}`，只读内容来源）；任务工作副本为 `{REPO_BASE_PATH}/{TASK_ID}`（按任务 baseline 检出，origin 指向新建远程仓库）。
> Claude Code 在 docker 容器（`benzhi-claude-code`）里做，**题号 = 任务 ID**，工作目录 `/workspace/<题号>`、轨迹在容器内 `/home/node/.claude/projects/-workspace-<题号>/`（Mac 与 Windows 相同）；容器入口与导出命令按操作系统见 runbook.md（Mac）/ runbook-windows.md（Windows）。做题后需导出到本机 `records/{TASK_ID}/` 供 `02-round-capture` 读取。

## 输入（create 需向用户确认）

- **任务类型**（7 选 1，决定任务 ID 后缀 slug 与快照/埋点策略；首轮严禁「简单」难度）——用户只需给这一项 + 任务 ID
- 以下由 agent 自动推断（用户未指定时用默认值，显式指定则覆盖）：
  - 仓库路径（素材源）= 任务 ID 去掉类型 slug（`solocc-0001-codegen` → `repos/solocc-0001`）
  - 目标说明 = 按任务类型 + 仓库内容起草（`prompt-architect` + `humanizer-zh`）
  - Harness = 默认 `Claude Code`（`Codex CLI` 需显式指定）；Harness 版本从 `secrets.toml [harness]` 按操作系统自动带入
  - 操作系统 = 当前机器（`MacOS/Linux` / `Windows`）
  - 环境可复现等级 = 默认 `无外部依赖`（有依赖时需确认）

## 执行流程

### 1. 校验仓库

1. 确认路径存在且为 git 仓库。
2. `git status` 检查：若已出现未提交改动 → 提示先提交或清理（快照必须是会话首轮前的基线）。
3. **凭据检查**：确认 `.gitignore` 已覆盖 `.env` 以及各类密钥/连接串/token 文件；抽查 `git ls-files` 无凭据文件。有泄漏 → 中止并提示先处理，禁止带着凭据提交。
4. **新建独立远程仓库（关键前置，务必先做）**：被标注仓库的来源远端（如 `gsb0731-xxx`）通常是已使用/共享的仓库，**不能直接用它提交**。要为它**新建一个全新的远程仓库**，并只基于该新仓库走后续流程：
   - 用 `github_username` + PAT（`secrets.toml [github] github_pat`）创建新仓库，命名建议 `claudccode-{TASK_ID}`（如 `claudccode-solocc-0001-codegen`）；
   - 把本地远端（origin）指到该新仓库（`git remote set-url origin <新仓库>`)；
   - 之后基线提交、初始快照、模型交互都基于这个新仓库；来源仓库只作为初始内容来源，不再向其提交。
5. 确认新仓库可 push且评测团队可访问（设为 **public** 公开仓库，或至少加协作者）；如需才回退来源仓库，须人工确认。

### 2. 打初始环境快照

1. 若工作区与基线有差异且无提交：`git add -A && git commit -m "<baseline: task init.>"`（保持一个干净基线 commit）。
2. `git push` 到**刚新建的独立远程仓库**。
3. 取**完整 40 位 SHA**（`git rev-parse HEAD`），生成 permalink：`https://github.com/<owner>/<新仓库>/commit/<40位完整SHA>`。之后**禁止 force-push/rebase** 改写该快照。
   - 必须完整 SHA，禁止短 SHA/分支/tag。
   - 之后**禁止 force-push/rebase** 改写该快照。

### 3. 建任务目录 + task-info.md

- 记录目录名 = 任务 ID = `{REPO}-{类型slug}`（如 `solocc-0001-codegen`）；同仓库同类型需多个窗口时再加 `-2`/`-3` 后缀（如 `solocc-0001-codegen-2`），人工确认。
- 用模板 `templates/task-info.md` 生成，填入共享字段：
  `任务 ID / 仓库(项目) / 任务标题 / 任务类型 / Repo URL / 本地路径 / 初始环境快照 / Harness / Harness版本 / 操作系统 / 环境可复现等级 / SessionID(待首轮后由 round-capture 自取回填) / 轨迹根目录(SessionID 回填后按 Harness 分行定位：Codex→~/.codex/sessions、Claude Code→本机导出的 records/{TASK_ID}/{TASK_ID}-trajectory.jsonl, 容器来源 /home/node/.claude/projects/-workspace-<题号>/) / annotator / 创建日期`。
- 共享字段整个会话各轮不变。

### 4. 起草首轮提示词（出题，需去 AI 化）

- 目标：像真实用户写给 Coding Agent 的自然需求；**纯自然语言**；难度/范围与任务类型匹配，不得过简（首轮严禁「简单」，也不得是雷同题/过于简单题，见 docs/annotate-guide.md §3/§7）。
- 起草：可调用 `skills/prompt-architect/SKILL.md` 协助起草，但 AI 起草的首轮提示词**必须先经 `skills/humanizer-zh/SKILL.md` 去 AI 化**，再由人工确认。
- 未去 AI 化 + 未经人工确认的提示词不写入 `-R01.md`（只暂存在 task-info.md「首轮提示词（待确认）」或输出给用户）。

### 5. 输出摘要

- 任务目录路径、快照 permalink、共享字段一览、首轮提示词。
- 提示用户下一步：到 Claude Code / Codex 打开工作区执行首轮提示词，完成后执行 `02-round-capture`。

## 输出模板（task-info.md，字段标题与 `templates/task-info.md` 一致，导出脚本按 `## ` 切块解析）

```markdown
# {TASK_ID} 任务信息（会话元信息）

## 任务 ID
{TASK_ID}  （= {REPO}-{类型slug}，如 solocc-0001-codegen）

## 仓库（项目）
{REPO}  （repos/<repo> 的目录名；一个项目可派生多个类型任务）

## 任务标题
<一句话说明这题让模型做什么>

## 任务类型
<0-1代码生成 / Feature迭代 / Bug修复 / 代码理解 / 代码重构 / 工程化 / 代码测试>

## 标注人
<TPM/专家名>

## 创建日期
<YYYY-MM-DD>

## Repo URL
<https://github.com/<org>/<repo>，去掉 .git>

## 本地路径
<任务工作副本路径，如 sessions/claudccode/{SESSION_NAME}/repos/solocc-0001-codegen>

## 初始环境快照
<https://github.com/<org>/<repo>/commit/<40位完整SHA>>

## Harness
<Claude Code / Codex CLI>

## Harness版本
<版本号>

## 操作系统
<MacOS/Linux / Windows>

## 环境可复现等级
<无外部依赖 / 有外部依赖，未容器化 / 已容器化，可一键起环境>

## SessionID
<整个会话窗口 ID，所有轮同一值；首轮后回填>

## 轨迹根目录（轨迹文件）
<按哪个 CLI 做的分行：Codex CLI → ~/.codex/sessions/<SessionID>；Claude Code（容器做，题号 = 任务 ID）→ 本机 records/{TASK_ID}/{TASK_ID}-trajectory.jsonl（来源容器 /home/node/.claude/projects/-workspace-<题号>/<SessionID>）；首轮 SessionID 回填后定位>

## 首轮提示词（已确认）
<首轮 prompt 原文；确认后作为该任务第 1 轮的 User Prompt 由 02-round-capture 录入到 {TASK_ID}-R01.md>
```

## 注意事项

1. 快照必须是会话首轮前的工作区状态；若模型已开始改动才补快照 → 该任务数据无法追溯，需重建任务。
2. 凭据不进仓库；push 到个人私有仓库等同没记录。
3. 记录目录名 = 任务 ID（`{REPO}-{类型slug}`），不覆盖已存在目录（已存在 → 提示换后缀或确认续用）。
4. 写中文文件一律用写文件工具（UTF-8），禁止 PowerShell `Set-Content`。
5. 出题分布：按天统计须满足 `0-1代码生成/Feature迭代/Bug修复 > 代码理解 ≈ 代码重构 > 其他`（导出时校验）。
