---
name: claudccode
description: "Claude Code 用户满意度标注。一个会话（任务）内至多 10 轮对话，每一轮对话为一条数据，按五维打分并汇总为正式提交表。Use when: 满意度标注, Coding Agent 标注, Claude Code 标注, 五维打分, 每轮一条数据, 用户反馈数据生产。"
---

# Claude Code 用户满意度标注

还原真实用户在 Coding Agent 产品中的反馈信号：以真实用户口径出题、在 **Claude Code** 中与模型交互，**一轮对话 = 一条数据**，按五维逐轮打分，最终汇总为正式提交表。

> 📄 项目源规范见 [docs/ClaudeCcode 用户满意度标注.docx](docs/ClaudeCcode%20用户满意度标注.docx)（0926 期）。本文档 + skills 是把该规范落成可执行流程。

## 数据模型（先读）

```
一个任务(会话窗口)  ── 至多 10 轮对话
      │
      ├─ 第 1 轮（首轮原始需求）  ─→  一条数据
      ├─ 第 2 轮（继续/修复/追问）─→  一条数据
      └─ ...（≤ 10 轮）
```

- **任务 = 会话**：同一个 `SessionID` 下的一个会话窗口。运行环境字段（Harness / Harness版本 / 操作系统 / 环境可复现等级 / 初始环境快照）同一会话各轮填**同一组值**。
- **仓库（项目）→ 任务**：一个素材仓库（项目）可派生多个任务，每个任务 = 仓库 × 类型 × 一个会话窗口，各自独立工作副本、独立初始快照（不同 commit）、独立远程仓库、独立记录目录。**任务 ID = 仓库目录名-类型slug**（如 `solocc-0001-codegen`）；slug 对照 `config.toml [task_types].aliases`：`0-1代码生成`→`codegen`、`Feature迭代`→`feat`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。例：`solocc-0001-codegen`（从零生成）、`solocc-0001-feat`（在生成产物上迭代）、`solocc-0001-bugfix`（埋点后修复）。
- **一轮 = 一条数据**：一次交互（用户提问 + 模型回答）。每条数据独立按五维打分，独立提交、独立验收。
- **多数据归属**：一个任务可提交多条数据，每条来自该会话中的一轮对话；导出一轮一行。
- **SessionID / TurnID**：`SessionID` 同一道题所有轮次填同一个值（把多轮聚合回一道题）；`TurnID/PromptID` 每轮唯一（Claude Code 取本轮 user 消息的 promptId）。**两者 agent 可从轨迹自取，无需用户手动回填**：Claude Code → 本机 `records/{TASK_ID}/{TASK_ID}-trajectory.jsonl`（来自容器导出，容器入口按操作系统见 runbook.md / runbook-windows.md；`type==user` 且 content 为字符串的条目 promptId = TurnID；**一轮 = 一次用户键入**）。多轮识别详见 [skills/02-round-capture.md](skills/02-round-capture.md)。

## 技能列表

| 序号 | 技能 | 文件 | 说明 |
|:--:|------|------|------|
| 1 | **任务初始化** | [skills/01-task-create.md](skills/01-task-create.md) | 建任务目录 + 初始快照（commit permalink）+ 环境字段 + 出题（首轮提示词） |
| 2 | **单轮录入** | [skills/02-round-capture.md](skills/02-round-capture.md) | 一轮交互后回填：User Prompt / TurnID / SessionID / 任务类型 / 难度 / 语言框架；SessionID 与 TurnID 由 agent 从本机轨迹自取、多轮自动拆轮 |
| 3 | **五维打分** | [skills/03-score-annotate.md](skills/03-score-annotate.md) | 读轨迹 → 调 implementation-reviewer + 过程分析 → 五维打分（1-5）+ 依据录入 + 硬性校验 |
| 4 | **导出提交** | [skills/04-export-submit.md](skills/04-export-submit.md) | 所有任务数据 → 正式提交表 CSV（每轮一行）+ 质检 → 投递飞书多维表格（目标见 config.toml `[feishu]`） |

## 共享资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 工作台根规范 | `AGENTS.md` | 工作台级约定（含「不要用 Set-Content 改写中文文件」） |
| 去 AI 化 Agent | `skills/humanizer-zh/SKILL.md` | 去除 AI 写作痕迹；**AI 生成的提示词与交付文本必须经它处理后才能使用/投递** |
| 提示词起草 Agent | `skills/prompt-architect/SKILL.md` | 可选：辅助出题起草（随后必须经 humanizer-zh 去 AI 化） |
| 代码评价 Agent | `skills/implementation-reviewer/SKILL.md` | 6 维度全栈代码评价；**打分路线 A 必调（红线）** |
| 分析范式参照 | `projects/code-eval-solo/skills/02-result-analysis.md` | 双路分析范式（读对话内容 → 读轨迹文件）；03 打分按它适配 |
| 项目源规范 | `docs/ClaudeCcode 用户满意度标注.docx` | 本期标注口径（表头、评分、质检） |
| 快速参考 | `docs/annotate-guide.md` | 评分表 / 难度 / 类型 / 原因写法速查（人工可读） |

> **去 AI 化说明**：AI 生成并进入交付物的文字（首轮提示词、追问/继续话术、AI 起草的五维打分依据等），无论练习还是正式，落盘/投递前**都须先经 `skills/humanizer-zh/SKILL.md` 去 AI 化**（练习阶段无需人工确认；正式交付再人工复核）。见下方「质量红线」。

## 工作流程

```
任务初始化(建任务+快照+环境+出题) → 用户在 Claude Code 中交互
    └→ [第 N 轮] 单轮录入 → 五维打分(去AI化+人工复核) → 决定是否继续(≤10 轮)
        → 会话结束 → 导出正式提交表（每轮一行）→ 质检 → 投递飞书多维表格
```

## ⚠️ 质量红线（分析必读轨迹 + 调 implementation-reviewer；AI 交付文本必去 AI 化；违反=整批拒收/退出项目）

> **当前阶段口径（重要）**：本项目当前为**练习/内部试用**，允许 AI（agent）直接起草并填写五维打分与依据描述，**无需人工逐条确认/复核**即可落盘；但**交付文本仍必须先经 `humanizer-zh` 去 AI 化**，且**必须严格按五维评分模式**：各维 1-5 整数、五条依据必填、描述含可核验证据（文件/报错/步骤）、保留「其他问题」。进入**正式交付/投递**阶段后，再在去 AI 化基础上补一次人工复核。

1. **AI 生成的交付文本必须先经去 AI 化**：凡 AI 起草、将进入交付物（用户提示词、五维打分依据、其他问题等）的文本，落盘/投递前**必须先经 `skills/humanizer-zh/SKILL.md` 去 AI 化**。**去 AI 化 = 实际调用并执行该 skill 的完整流程**（28 条规则全查：AI 符号、AI 词汇、句式套路、三/金字式、翻译腔、长定语等），**不得只做删符号、避关键词这种手动修补**。练习阶段允许 AI 直接打分与写依据、无需人工逐条确认，但去 AI 化这一步不可省；正式交付在此基础上再人工复核。
2. **人工原文不改写**：专家/用户亲手输入的 prompt、亲手撰写的打分依据，保持原文原样录入；不得为了“显得自然”擅自用 AI 改写人工内容（除非用户明确要求）。
3. **依据必须可核验**：打分依据需基于真实轨迹与产物，写明具体证据（文件/报错/步骤/动作）。AI 起草时不得脱离依据编造；人工复核时逐条核对。
4. **分析必须读轨迹 + 调用 implementation-reviewer（红线）**：AI 代打分数时，**必须**读真实轨迹文件（`records/{TASK_ID}/{TASK_ID}-trajectory.jsonl`）并**必须**调用 `skills/implementation-reviewer/SKILL.md` 做代码产物评价，二者缺一即视为脱离依据、整批拒收；分析方法参照 `projects/code-eval-solo/skills/02-result-analysis.md`（把「读对话内容」适配为「读轨迹文件」）。交付文本仍须经 humanizer-zh 去 AI 化。
5. **分数与描述必须一致（红线）**：打多少分，对应的依据描述就必须写到那个档位——4/5 分不得出现「未完成/失败/报错/虚假」等失败表述；1/2 分必须写明负面证据，不得「低分却写得像满分」。分数与描述打架直接整批拒收，不得提交。
6. 所有数据不允许返修：不符合质量要求直接拒收；被抽检高频不合格或检出未去 AI 化的 AI 文本，历史数据全部拒收。

## 核心口径速查（详见 docs/annotate-guide.md）

| 项 | 取值 |
|----|------|
| 任务类型（每轮单选） | 0-1代码生成 / Feature迭代 / Bug修复 / 代码理解 / 代码重构 / 工程化 / 代码测试 |
| 任务难度 | 简单 / 中等 / 困难 / 地狱（首轮严禁「简单」） |
| Harness | Claude Code（须记录版本号） |
| 操作系统 | MacOS/Linux / Windows |
| 可复现等级 | 无外部依赖 / 有外部依赖，未容器化 / 已容器化，可一键起环境 |
| 五维打分 | 交付完整性 / 指令遵循 / 任务规划 / 推理能力 / 执行能力，各 1-5 + 必填依据描述 |
| 轮次上限 | 每个会话窗口 ≤ 10 轮；工程故障（网络波动/请求失败）不计轮次，思考超限需人为「继续」**计**轮次 |

## 目录结构（详见 docs/structure-example.md）

```
projects/claudccode/
├── SKILL.md                     # 本文件（索引导航）
├── config.toml                  # 项目配置（路径、类型、难度、评分、轮次上限）
├── secrets-simple.toml          # 本地敏感配置模板
├── README.md
├── docs/                        # runbook / structure-example / annotate-guide / 源 docx
├── skills/                      # 01-task-create / 02-round-capture / 03-score-annotate / 04-export-submit
└── templates/                   # task-info.md / round-file.md / submit-headers.csv

sessions/claudccode/{SESSION_NAME}/            # 工作数据（gitignore）
├── repos/<repo>/                # 素材源（上游内容，只读；同时是项目分组）
│   ├── <repo>-<slug>/           # baseline（任务工作副本，模型输入，docker cp 进容器）
│   └── <repo>-<slug>-R01/ ...   # 每轮代码产物（容器导回，供本地跑/审 + git diff）
└── records/<repo>/              # 项目分组（可选一层，不含 task-info.md）；也可扁平直接放任务目录
    └── <repo>-<slug>/           # 任务目录；目录名 = 任务 ID = 仓库目录名-类型slug
        ├── task-info.md         # 共享会话/环境字段
        ├── <repo>-<slug>-R01.md ... # 每轮一条数据文件（R01..R10）
        ├── <repo>-<slug>-R01-trajectory.jsonl ... # 每轮轨迹切片（本轮打分用）
        └── <repo>-<slug>-trajectory.jsonl  # 完整轨迹（交付/上传用）

deliverables/claudccode/{SESSION_NAME}/正式提交表-{SESSION_NAME}-{date}.csv
```

> records 目录支持两种布局：**嵌套**（`records/<repo>/<repo>-<slug>/`，推荐，一个项目一层分组）或**扁平**（`records/<repo>-<slug>/`）。两种导出脚本都能识别：含 `task-info.md` 的目录 = 任务，不含但有子目录的 = 项目分组。任务 ID / 题号始终是扁平的 `{repo}-{slug}`（不能带 `/`，容器 `cc` 限制）。

## 文档

| 文档 | 说明 |
|------|------|
| [runbook.md](docs/runbook.md) | 逐步操作手册（指令模板，Mac） |
| [runbook-windows.md](docs/runbook-windows.md) | 逐步操作手册（指令模板，Windows） |
| [CLAUDE_CODE_DOCKER_MAC.md](docs/CLAUDE_CODE_DOCKER_MAC.md) | Claude Code Docker 使用说明（Mac） |
| [CLAUDE_CODE_DOCKER_windows.md](docs/CLAUDE_CODE_DOCKER_windows.md) | Claude Code Docker 使用说明（Windows） |
| [structure-example.md](docs/structure-example.md) | 完整目录结构样例（含路径映射） |
| [annotate-guide.md](docs/annotate-guide.md) | 评分表 / 原因写法 / 雷同题清单速查 |
| [ClaudeCcode 用户满意度标注.docx](docs/ClaudeCcode%20用户满意度标注.docx) | 项目源规范 |
