---
name: swe-task-create
description: "SWE 题目创建：给定一个 Repo，一次为 3 个分支（{repo}-01/02/03）各出一道真实且有难度的题，创建分支/worktree，写 Verify Rubric 并生成 3 个任务目录。Use when: SWE 出题, 选 repo, 写需求, Verify Rubric。"
---

# SWE 题目创建（Task Create）

> 配置从 `../config.toml` 读取，`secrets.toml` 中可覆盖。
> 依赖 agent：无（需求独立提出，不调用 prompt-architect）

SWE-like 流水线的第一步，也是核心。目标：给定一个 Repo，**一次产出 3 道**真实且有难度的 SWE 题（对应 3 个分支 {repo}-01/02/03）——选对 Repo、锁对版本、写出可观察、可验收的需求与 Rubric，并建好分支与 worktree。

## 功能概述

这个技能负责：

- 选择自己熟悉的开源 Repo，记录 Repo URL 与版本（默认获取最新 Commit ID，可固定到某 commit/tag）
- 基于对项目真实使用场景和代码结构的理解，**独立提出**需求
- 撰写真实性与难度说明、可能涉及模块
- 撰写 Verify Rubric（可观察行为 + 输入条件 + 预期结果）
- 创建 3 个分支 `{repo}-01/02/03` + 3 份 worktree，并生成 3 个任务目录（各含 `task.md` / `meta.json` / `verify-rubric.md` / `session.md`）

这个技能不负责：

- 从 Issues、热门讨论或既有题目照抄需求（**严禁**）
- 预先指定单元测试、实现模块或技术方案（不写死实现）
- 运行模型或记录回答（由 `02-run-record.md` 负责）

## 命令

| 命令 | 说明 |
|------|------|
| create | 默认命令。给定 Repo（项目名）→ 锁版本 → 独立出 3 题 → 建 3 分支/worktree → 生成 3 个任务目录 |

## 执行流程

1. **选择 Repo**：用户提供项目名/Repo（URL），一次处理 3 道题。支持从 `repo-fetcher` 素材池选择。
2. **锁定版本**：默认自动获取该 Repo 的**最新 Commit ID** 写入 `meta.json`（如需固定到某 commit/tag 可由用户指定）。出题与运行必须基于同一版本，保证可复现。
3. **类型与语言**：根据 Repo 主语言与需求性质，从 `config.toml [task]` 中选任务类型（功能新增 / Bug 修复 / 测试增强 / 重构/性能 / 配置/工具链 / 其他 / 问题修复）与主要语言。**本轮 100 题语言仅限 Go / Python**（见 `docs/内部规范.md`）。
4. **独立出题**：撰写 **3 份**需求 Prompt（分别写入 3 个分支的 `task.md`，三道题各不同）。每份要求：
   - 明确目标、适用场景及**可观察的预期行为**，避免仅描述抽象方向
   - 需求描述长度不限
   - 不直接照抄 Top Open Issues、热门讨论或既有题目
   - 不预先指定单元测试、实现模块或技术方案（但可描述涉及的模块范围）
   - **像真实 MR 需求**：MR 改什么就写什么，不要扩展成「大而全」需求文档；用平实自然语言，交付字段不得含 Markdown 标签——尤其是反引号（命令/选项名直接写裸词，如 flask config、--json，不用反引号包裹）、加粗、斜体、——、「」
   - **题要与 Repo 匹配**：是该 Repo 管理员可能会合并到主分支的需求
   - **反例自查**（存在任一即不收录）：无法由 Repo 独立实现；已有功能（未查重）；与 Repo 定位不符；与 Repo 不匹配 / 维护者不会合并
5. **撰写交付内容**：
   - 真实性与难度说明
   - 可能涉及模块
   - Verify Rubric（见下节）
6. **Verify Rubric 反例自查**（必做）：Rubric 不得是主观描述、不得写死文件/类名/实现方案、不得依赖稀缺或不可访问的外部状态、不得事后倒改。
7. **生成任务目录 + 分支**：在 `repos/{repo}/origin` 创建 3 个分支 `{repo}-01/02/03`，用 `git worktree add` 拉出 3 份工作目录；写入 3 组 `task.md` / `meta.json` / `verify-rubric.md`（三个分支共用同一 commit），并为每个任务目录创建**空的 `session.md`**（供 02 阶段粘贴 Trae 完整会话），输出题目名称与路径。

## Verify Rubric 规范

每条 Rubric 应包含**可观察行为 + 输入条件 + 预期结果**，不同质检人可稳定复现。

| Bad Case | 问题 |
|------|------|
| “功能正常、体验良好、代码质量高。” | 判定标准主观，无观察行为/输入/预期，无法稳定复现 |
| “必须修改 app.rs，并新增 AutoResetManager 类。” | 无必要写死文件/类名/实现方案，可能误判行为正确的替代实现 |
| “使用真实账户耗尽额度，并消耗一次真实 reset credit 验证。” | 依赖稀缺/不可访问外部状态，成本高难复现；应允许 mock/日志/可控状态 |
| “先看模型怎么实现，再补充它没有做到的检查项。” | 事后倒改标准；Rubric 可在出题前后完善，但必须在最终判定前固定 |

## 反例：不应收录的伪需求

| 反例需求 | 问题类型 | 为什么不收录 |
|------|------|------|
| 为 Claude Code 增加完整 CoT 的自动保存、展示和导出功能。 | 无法由 Repo 独立实现 | 依赖上游模型能力与安全策略变化，客户端 Repo 无法获取或还原 |
| 为 Codex CLI 增加 side chat。 | 已有功能 | Codex CLI 已提供 `/side`（别名 `/btw`），属未查重的重复需求 |
| 让 FastAPI 内置 Kubernetes 自动扩缩容控制器。 | 与 Repo 定位不符 | 属部署与集群编排，非 Web 框架核心职责 |
| 给 Web 框架加一个与框架无关的通用工具（如内置拼写检查器）。 | 与 Repo 不匹配 | 不是该 Repo 管理员会合并到主分支的需求（见 `docs/内部规范.md`） |

## 路径规则

```
# 源码目录（fork clone，与 tasks 平级）
{work_root}/{session}/repos/{repo}/origin/       # 主分支基线
{work_root}/{session}/repos/{repo}/{repo}-01/   # 分支 {repo}-01（第 1 题）
{work_root}/{session}/repos/{repo}/{repo}-02/   # 分支 {repo}-02（第 2 题）
{work_root}/{session}/repos/{repo}/{repo}-03/   # 分支 {repo}-03（第 3 题）

# 任务根目录
{work_root}/{session}/tasks/{repo}/{branch}/
├── task.md           # 需求 Prompt（原文，交付表「需求 Prompt（原文）」来源）
├── meta.json         # Repo URL / Commit/版本 / 主要语言 / 任务类型 / Seed 模型/版本 / 题目名称
├── verify-rubric.md  # Verify Rubric（验收前固定）
├── session.md        # Trae 完整会话（出题阶段创建空文件，02 阶段用户粘贴，供步数统计）
├── run-log.md        # Trae Session ID / 有效轮数（02 阶段写入）
├── result.md         # 产物结果 / 产物补充材料（02 阶段写入）
└── review.md         # 是否完成 / 是否通过质检 / 收录判定（03 阶段写入）
```

> `{work_root}` 与 `{session}` 由 `config.toml [paths]` / `[sessions]` 决定。分支命名 `{repo}-01/02/03`；task-id = 分支名（`{repo}-XX`），任务目录 `tasks/{repo}/{branch}/`。

## 交付字段前置填写

出题阶段即确定以下交付表字段（写入 `meta.json`）：

| 交付表字段 | 来源 |
|------|------|
| 题目名称 | 出题时定义（task-id 或短名） |
| 提交人 | 不填写：飞书表格该字段有默认值，无需录入 |
| Repo URL | 选定的 Repo |
| Commit/版本 | 默认最新 Commit ID（可固定到某 commit/tag） |
| 主要语言 | Repo 主语言（单选） |
| 任务类型 | 需求性质（单选） |
| 需求 Prompt（原文） | `task.md` 原文 |
| 真实性与难度说明 | 出题交付 |
| 可能涉及模块 | 出题交付 |
| Verify Rubric | `verify-rubric.md`（验收前固定） |
| Seed 模型/版本 | 运行所用模型（默认 `config.toml [run].model`） |

## 注意事项

1. 需求必须独立提出，**不得照抄 Issues、热门讨论或既有题目**。
2. 出题与运行使用同一固定版本；版本变更需重新出题。
3. 单 repo 最多提交 3 条数据（`config.toml [task].max_tasks_per_repo`；见 `docs/内部规范.md`）。
4. Verify Rubric 一旦验收开始即冻结，不得根据模型结果调整。
5. 本轮语言仅限 Go / Python；Prompt 用平实自然语言书写，交付字段不得含 Markdown 标签。
