---
name: cc-solo-task-create
description: "cc-solo 任务初始化：新建一个任务（会话窗口），打初始环境快照（commit permalink），填共享运行环境字段，起草首轮提示词。Use when: cc-solo 新建任务, 满意度标注任务初始化, 初始快照, 出题。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取；`secrets.toml` 可覆盖 `active_session`、`repo_base_path`、`records_dir`、`annotator`。
> 依赖 agent：`skills/humanizer-zh/SKILL.md`（去 AI 化，AI 起草提示词必用）、`skills/prompt-architect/SKILL.md`（可选起草）
> 路径变量：`{work_root}`=`[paths].work_root`、`{SESSION_NAME}`=`[sessions].active`、`{RECORD_DIR}`=`{work_root}/{SESSION_NAME}/[paths].records_dir`、`{REPO_BASE_PATH}`=`{work_root}/{SESSION_NAME}/[paths].repo_base_path`（= `source-code`）、`{项目}`=项目名（素材源目录名，如 `app-12`）、`{任务}`=任务名 = `{项目}-{类型}-{索引}`（如 `app-12-bugfix-01`）。

# cc-solo 任务初始化

## 功能概述

为一个**任务（= 一个会话窗口，≤ 10 轮）**建立数据档案：

1. 校验被标注仓库（干净、无凭据泄漏、已 git init、可 push）+ **校验仓库结构**（素材源位于 `source-code/{项目}/`；不规范则提示用户确认后整理）
2. **打初始环境快照**：首轮交互前提交 baseline 并 push，记录 commit permalink（完整 40 位 SHA）
3. 建任务目录与 `task-info.md`（共享运行环境字段）
4. 起草**首轮提示词**（真实用户口径：AI 起草须先 humanizer-zh 去 AI 化，再人工确认后写盘）

**不负责**：在 Claude Code 中代跑对话；代替人工决定任务类型/难度。

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
| create | 默认。校验仓库（**先查仓库结构**，不规范则提示用户确认后整理成 `source-code/{项目}/{项目}-{类型}/{项目}-{类型}-{索引}/`）→ 建副本 + 出题 → 起草首轮提示词 |
| info | 仅校验仓库状态与展示将填写的字段（含结构检查结果），不写文件 |

## 默认配置

> 任务名 = **`{项目}-{类型}-{索引}`**（如 `app-12-bugfix-01`）。记录目录与轮次文件都以它为前缀。同一项目按类型复制多份任务副本，各任务独立目录。
> 类型 slug 对照（`config.toml [task_types].aliases`）：`0-1代码生成`→`codegen`、`Feature迭代`→`feature`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。
> 任务目录（R0N 模型）：`{RECORD_DIR}/{项目}/{项目}-{类型}/{任务}/`；共享字段文件：`{RECORD_DIR}/{项目}/{项目}-{类型}/{任务}/task-info.md`
> 每轮数据文件：`{RECORD_DIR}/{项目}/{项目}-{类型}/{任务}/{任务}-R{NN}.md`（一轮 = 一条数据）。
> **仓库与目录结构（create 第一步必检）**：素材源（项目根 = 唯一 git 仓库 = base commit 快照）位于 `{REPO_BASE_PATH}/{PROJECT}/`（如 `source-code/app-12/`），其下按规范嵌套：
> - 素材源内容（`src/`、`README.md`、`.git` 等）直接放 `{PROJECT}/` 下；
> - 任务副本 = `{REPO_BASE_PATH}/{PROJECT}/{PROJECT}-{slug}/{PROJECT}-{slug}-{index}/`（复制素材源内容 + 目录名改为任务名，无 .git，不提交/push）。
> - **判断规范**：`source-code/{项目}/` 是唯一 git 仓库；任务副本按类型分组 `{项目}-{slug}/` 嵌套在项目根下，索引全局累加；素材源文件平铺、副本错级/错名，都视为**结构不规范**。
> - **处理**：先列出「当前实际结构 vs 规范结构」的差异 → **提示用户确认** → 确认后整理成 `source-code/{项目}/{项目}-{slug}/{项目}-{slug}-{index}/` 再继续；**未获用户确认，不得擅自移动文件**。
> Claude Code 在 docker 容器（**1 题 1 容器**，容器名 `cc-solo-{任务}`）里做，**容器内工作目录恒为 `/workspace`**（= 本题任务副本内容；Windows 直接挂载副本目录，Mac 由 agent 在首轮交互前播种），轨迹恒在容器内 `/home/node/.claude/projects/-workspace/`（不再有 `-workspace-<题号>`）；容器入口与导出命令按操作系统见 runbook.md（Mac）/ runbook-windows.md（Windows）。每轮由 agent 执行 docker 命令导出轨迹（`records/{项目}/{项目}-{类型}/{任务}/`）；代码产物已在挂载/播种目录（无需回导），供 `02-round-capture` 读取。

## 输入（create 需向用户确认）

- **仓库名 + 任务类型**（用户只需给这两项；任务类型 7 选 1，决定 slug 与快照/埋点策略；首轮严禁「简单」难度）
- 任务 ID 由 agent 拼：`{仓库名}-{slug}`（`h5-demo` + 代码理解 → `h5-demo-understand`）
- 以下由 agent 自动推断（用户未指定时用默认值，显式指定则覆盖）：
  - 仓库路径（素材源）= `source-code/{项目}`
  - 目标说明 = 按任务类型 + 仓库内容起草（`prompt-architect` + `humanizer-zh`）
  - Harness = `Claude Code`；Harness 版本从 `secrets.toml [harness]` 按操作系统自动带入
  - 操作系统 = 当前机器（`MacOS/Linux` / `Windows`）
  - 环境可复现等级 = 默认 `无外部依赖`（有依赖时需确认）

## 执行流程

### 1. 校验仓库与仓库结构

0. **校验仓库结构（create 第一步必检，规则见上文「仓库与目录结构」）**：
   - 判断 `{REPO_BASE_PATH}/{PROJECT}/`（素材源项目根，唯一 git 仓库）是否存在、任务副本是否按类型分组嵌套其下；副本错级/错名（未按 `{项目}-{slug}/{项目}-{slug}-{index}/`）即视为**不规范**。
   - **结构不规范**：把「当前实际结构」与「规范结构」的差异列给用户，**提示用户确认**；用户确认后，整理成 `source-code/{项目}/{项目}-{slug}/{项目}-{slug}-{index}/` 再继续；**未获确认不擅自移动**（可先走 `info` 只读展示）。
1. 确认路径存在且为 git 仓库。
2. `git status` 检查：若已出现未提交改动 → 提示先提交或清理（快照必须是会话首轮前的基线）。
3. **凭据检查**：确认 `.gitignore` 已覆盖 `.env` 以及各类密钥/连接串/token 文件；抽查 `git ls-files` 无凭据文件。有泄漏 → 中止并提示先处理，禁止带着凭据提交。
4. **新建独立远程仓库（关键前置，务必先做）**：被标注仓库的来源远端（如 `gsb0731-xxx`）通常是已使用/共享的仓库，**不能直接用它提交**。要为它**新建一个全新的远程仓库**，并只基于该新仓库走后续流程：
   - 用 `github_username` + PAT（`secrets.toml [github] github_pat`）创建新仓库，命名建议 `cc-solo-{任务}`（如 `cc-solo-app-12-codegen`）；
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

- 记录目录名 = 任务 ID = `{项目}-{类型slug}`（如 `app-12-codegen`）；同仓库同类型需多个窗口时再加 `-2`/`-3` 后缀（如 `app-12-codegen-2`），人工确认。
- 用模板 `templates/task-info.md` 生成，填入共享字段：
  `任务 ID / 仓库(项目) / 任务标题 / 任务类型 / Repo URL / 本地路径 / 初始环境快照 / Harness / Harness版本 / 操作系统 / 环境可复现等级 / SessionID(待首轮后由 round-capture 自取回填) / 轨迹根目录(SessionID 回填后定位：Claude Code→本机导出的 records/{任务}/{任务}-trajectory.jsonl, 容器来源 /home/node/.claude/projects/-workspace/) / annotator / 创建日期`。
- 共享字段整个会话各轮不变。

### 4. 起草首轮提示词（出题，需去 AI 化）

- 目标：像真实用户写给 Coding Agent 的自然需求；**纯自然语言**；难度/范围与任务类型匹配，不得过简（首轮严禁「简单」，也不得是雷同题/过于简单题，见 docs/annotate-guide.md §3/§7）。
- 起草：可调用 `skills/prompt-architect/SKILL.md` 协助起草，但 AI 起草的首轮提示词**必须先经 `skills/humanizer-zh/SKILL.md` 去 AI 化**，再由人工确认。
- 未去 AI 化 + 未经人工确认的提示词不写入 `-R01.md`（只暂存在 task-info.md「首轮提示词（待确认）」或输出给用户）。

### 5. 输出摘要

- 任务目录路径、快照 permalink、共享字段一览、首轮提示词。
- 提示用户下一步：到 Claude Code 打开工作区执行首轮提示词，完成后执行 `02-round-capture`。

## 输出模板（task-info.md，字段标题与 `templates/task-info.md` 一致，导出脚本按 `## ` 切块解析）

```markdown
# {任务} 任务信息（会话元信息）

## 任务 ID
{任务}  （= {项目}-{类型slug}，如 app-12-codegen）

## 仓库（项目）
{项目}  （source-code/{项目}/ 的目录名；一份素材源按类型复制多份任务副本）

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
<任务副本路径，如 sessions/cc-solo/{SESSION_NAME}/source-code/app-12/app-12-bugfix/app-12-bugfix-01>

## 初始环境快照
<https://github.com/<org>/<repo>/commit/<40位完整SHA>>

## Harness
<Claude Code>

## Harness版本
<版本号>

## 操作系统
<MacOS/Linux / Windows>

## 环境可复现等级
<无外部依赖 / 有外部依赖，未容器化 / 已容器化，可一键起环境>

## SessionID
<整个会话窗口 ID，所有轮同一值；首轮后回填>

## 轨迹根目录（轨迹文件）
<Claude Code（容器做，1 题 1 容器 cc-solo-{任务}）→ 本机 records/{任务}/{任务}-trajectory.jsonl（来源容器 /home/node/.claude/projects/-workspace/<SessionID>）；首轮 SessionID 回填后定位>

## 首轮提示词（已确认）
<首轮 prompt 原文；确认后作为该任务第 1 轮的 User Prompt 由 02-round-capture 录入到 {任务}-R01.md>
```

## 注意事项

1. 快照必须是会话首轮前的工作区状态；若模型已开始改动才补快照 → 该任务数据无法追溯，需重建任务。
2. 凭据不进仓库；push 到个人私有仓库等同没记录。
3. 记录目录名 = 任务 ID（`{项目}-{类型slug}`），不覆盖已存在目录（已存在 → 提示换后缀或确认续用）。
4. 写中文文件一律用写文件工具（UTF-8），禁止 PowerShell `Set-Content`。
5. 出题分布：按天统计须满足 `0-1代码生成/Feature迭代/Bug修复 > 代码理解 ≈ 代码重构 > 其他`（导出时校验）。
