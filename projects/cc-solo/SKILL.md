---
name: cc-solo
description: "Claude Code 用户满意度标注。一个会话（任务）内至多 10 轮对话，每一轮对话为一条数据，按五维打分并汇总为评价结果文件（按提交表单 24 字段，一轮一条）。Use when: 满意度标注, Coding Agent 标注, Claude Code 标注, 五维打分, 每轮一条数据, 评价结果, 用户反馈数据生产。"
---

# cc-solo 单模型代码评估（容器化）

从一份素材源码出发，按 7 类任务批量生成「任务副本 + 提示词」，**每题一个容器**执行（容器内 `/workspace` = 本题任务副本内容），导出轨迹与代码，按五维逐轮打分并汇总导出。合并了 code-eval-solo 的「按类型批量出题 + 全局索引」与 claudccode 的「容器执行 + 会话/轮次 + 五维打分」。

> 📄 项目源规范见 [docs/ClaudeCcode 用户满意度标注.docx](docs/ClaudeCcode%20用户满意度标注.docx)（0926 期）。本文档 + skills 是把该规范落成可执行流程。

> 🧑💻 **分工：你只发指令，命令由 agent 跑**。你只需发自然语言指令（`cc-solo {项目} generate`、`cc-solo {任务} round N` / `score N`、`cc-solo export`），本仓库里出现的 `docker …` 与 `python scripts/cc-solo/…` 全部由 **agent 在宿主机执行**。唯一需要你自己敲的是「进容器跟 Claude 对话」那两条 docker 命令（见 runbook）。

> 📌 **交付约定：agent 每完成一步，都要在同一条回复里写出下一步**——① 下一步要敲的**命令原文**（可直接照抄，要替换的值标出来）+ ② **怎么操作**（预期看到什么、常见报错、出错查哪一节）。不要只说「已完成」把下一步留到下一轮问答；多题批次还要讲清**哪几题、什么顺序、哪些能并行**。Windows 侧多题批量建容器优先用 `foreach` 循环一次起（见 [runbook-windows.md](docs/runbook-windows.md) 第 2 步「单题 vs 多题」）；Mac 侧因镜像要求空目录 + 启动后播种 + 会话不可恢复，**不能照搬循环**（见 [runbook.md](docs/runbook.md) 第 2 步）。

> ⛔ **本阶段只生成、先不提交**：提交接口已就位（`config.toml [submission].submit_url`），但当前只做到「生成评价结果 + 质检」，**不上传轨迹附件、不调提交接口**；要提交时用户说一声，由 agent 执行。

## 数据模型（先读）

```
一个任务(会话窗口)  ── 至多 10 轮对话
      │
      ├─ 第 1 轮（首轮原始需求）  ─→  一条数据
      ├─ 第 2 轮（继续/修复/追问）─→  一条数据
      └─ ...（≤ 10 轮）
```

- **任务 = 会话 = 容器 = 本机工作目录**：1 任务对应 1 个 Claude Code 会话窗口，跑在 1 个独立容器里（容器名 `cc-solo-{任务}`），容器内工作目录恒为 `/workspace`（内容 = 本题任务副本），轨迹恒在 `/home/node/.claude/projects/-workspace/`。同一个 `SessionID` 下的一个会话窗口。运行环境字段（Harness / Harness版本 / 操作系统 / 环境可复现等级 / 初始环境快照 / 镜像 tag+digest）同一会话各轮填**同一组值**。
- **项目 → 任务副本**：一份素材源（项目，如 `app-12`）复制成多份任务副本，按任务类型分组、全局索引累加。**任务名 = 副本目录名 = 提示词名 = 容器名（前缀 `cc-solo-`）= `{项目}-{类型slug}-{索引}`**（如 `app-12-bugfix-01`）。类型 slug 对照 `config.toml [task_types].aliases`：`0-1代码生成`→`codegen`、`Feature迭代`→`feature`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。
- **一轮 = 一条数据**：一次交互（用户提问 + 模型回答）。每条数据独立按五维打分，独立提交、独立验收。
- **多数据归属**：一个任务可提交多条数据，每条来自该会话中的一轮对话；导出一轮一行。
- **SessionID / TurnID**：`SessionID` 同一道题所有轮次填同一个值（把多轮聚合回一道题）；`TurnID/PromptID` 每轮唯一（Claude Code 取本轮 user 消息的 promptId）。**两者 agent 可从轨迹自取，无需用户手动回填**：Claude Code → 本机 `records/{任务}/{任务}-trajectory.jsonl`（来自容器导出，容器入口按操作系统见 runbook.md / runbook-windows.md；`type==user` 且 content 为字符串的条目 promptId = TurnID；**一轮 = 一次用户键入**）。多轮识别详见 [skills/02-round-capture.md](skills/02-round-capture.md)。

## 技能列表

| 序号 | 技能 | 文件 | 说明 |
|:--:|------|------|------|
| 1 | **任务初始化** | [skills/01-task-create.md](skills/01-task-create.md) | 建任务目录 + 初始快照（commit permalink）+ 环境字段 + 出题（首轮提示词） |
| 2 | **单轮录入** | [skills/02-round-capture.md](skills/02-round-capture.md) | 一轮交互后回填：User Prompt / TurnID / SessionID / 任务类型 / 难度 / 语言框架；SessionID 与 TurnID 由 agent 从本机轨迹自取、多轮自动拆轮 |
| 3 | **五维打分** | [skills/03-score-annotate.md](skills/03-score-annotate.md) | 读轨迹 → 调 implementation-reviewer + 过程分析 → 五维打分（1-5）+ 依据录入 + 硬性校验 |
| 4 | **评价结果与提交** | [skills/04-export-submit.md](skills/04-export-submit.md) | 按提交表单字段规范（`docs/submission/fields.json`，24 字段）生成「一轮 = 一条」评价结果 JSON（+ 核对 CSV + 质检报告）；提交接口已就位（`POST https://solo2.jzxhnh.com/api/v1/submissions`）但**本阶段先不提交**。脚本 `extract_submit_fields.py` / `build_eval_result.py` / `submit_eval_result.py` 全部由 **agent 执行**，用户只发 `cc-solo export` 这类指令。旧的 CSV 提交表与飞书投递已退役 |

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
任务初始化(建任务+快照+环境+出题) → 启动本题容器(人工 docker run，一题一个)
    → agent 播种任务副本到容器 /workspace（Mac：启动后播种；Windows：直接挂载，无此步）
    → 用户在容器内 Claude Code 连续交互（一个会话窗口，中途不要退出）
    └→ [第 N 轮] agent 导出轨迹 → 单轮录入 → 五维打分(去AI化+人工复核) → 决定是否继续(≤10 轮)
        → 会话结束(导出轨迹 + 回导源码 + 删容器) → 生成评价结果文件（每轮一条）→ 质检 → （本阶段先不提交）提交接口 `POST https://solo2.jzxhnh.com/api/v1/submissions`
```

> **任务初始化第一步必检两件事**：① **雷同题红线**——素材源项目落在 `docs/annotate-guide.md` §7「不被允许的雷同题」清单即中止、提示换素材，不得建副本/出题；② **仓库结构**——素材源须位于 `source-code/{项目}/`（项目根 = 唯一 git 仓库），其下按类型分组 `{项目}-{类型}/` 嵌套任务副本 `{项目}-{类型}-{索引}/`。结构不规范时先列出差异、**提示用户确认**，确认后整理成该格式再继续。详见 [skills/01-task-create.md](skills/01-task-create.md)。

## ⚠️ 质量红线（分析必读轨迹 + 调 implementation-reviewer；AI 交付文本必去 AI 化；违反=整批拒收/退出项目）

> **当前阶段口径（重要）**：本项目当前为**练习/内部试用**，允许 AI（agent）直接起草并填写五维打分与依据描述，**无需人工逐条确认/复核**即可落盘；但**交付文本仍必须先经 `humanizer-zh` 去 AI 化**，且**必须严格按五维评分模式**：各维 1-5 整数、五条依据必填、描述含可核验证据（文件/报错/步骤）、保留「其他问题」。进入**正式交付/投递**阶段后，再在去 AI 化基础上补一次人工复核。

0. **雷同题红线（出题/建任务前第一步必检）**：素材源项目若落在 `docs/annotate-guide.md` §7「不被允许的雷同题」清单（经典小游戏与变种、塔防/2D 解谜/潜行/平台跳跃、粒子物理、喂食小动物、CLI 工具、CRUD/后台/电商/预约系统、报表看板、番茄钟/天气/记账等），**命中即中止**——不得建副本、出题、打快照，先提示用户换素材。

1. **AI 生成的交付文本必须先经去 AI 化**：凡 AI 起草、将进入交付物（用户提示词、五维打分依据、其他问题等）的文本，落盘/投递前**必须先经 `skills/humanizer-zh/SKILL.md` 去 AI 化**。**去 AI 化 = 实际调用并执行该 skill 的完整流程**（28 条规则全查：AI 符号、AI 词汇、句式套路、三/金字式、翻译腔、长定语等），**不得只做删符号、避关键词这种手动修补**。**提交 body 里的所有字段都要过这一步**（不只五维描述）；`build_eval_result.py` 只做机械兜底（humanizer 强制符号命中即 error 阻塞提交、AI 高频词记 warn），**替代不了实际调用该 skill**。练习阶段允许 AI 直接打分与写依据、无需人工逐条确认，但去 AI 化这一步不可省；正式交付在此基础上再人工复核。
   - **评价结果里一律不用 AI 套话词**：`落地`、`模型`、`赋能`、`助力`、`闭环`、`抓手`、`沉淀`、`复用`、`对齐`、`打通`、`链路`、`颗粒度`、`场景化`、`心智`、`拉通`、`复盘`、`生态`、`矩阵`、`调性`、`层面`、`体现`。
   - 两个容易混的写法：**指被评测的 AI 时用「它」**（全篇都在评它，反复写「模型」是废话且是 AI 腔）；**指 Django 数据模型时写「数据定义」或直接引用 `models.py` 里的类名**（技术术语不能硬换，否则失真）。
   - **尽量写成中文，不要出现长英文串（红线）**：评价里避免连续 ≥12 个英文字符的命令、参数、标识符或路径（如 `--break-system-packages`、`unique_together`、`config/settings/local.py`）。平台的 **B-5「公共长片段」查重按连续字符比对**，这类长英文串在别人的提交里也常见，极易被判「套模板」打回——已有实测打回记录。改成中文说法（「包管理器的强制安装参数」「唯一约束」「本地配置模块」）；短标识（JWT、400、HTTP 这类）不受影响。
   - 这两条已做成 `build_eval_result.py` 的**机械检查**：套话词与 ≥16 字符的长英文串记 error（阻塞提交），AI 高频词与 12–15 字符的长串记 warn；词表以 `docs/annotate-guide.md` §9 为准。
2. **人工原文不改写**：专家/用户亲手输入的 prompt、亲手撰写的打分依据，保持原文原样录入；不得为了“显得自然”擅自用 AI 改写人工内容（除非用户明确要求）。
3. **依据必须可核验**：打分依据需基于真实轨迹与产物，写明具体证据（文件/报错/步骤/动作）。AI 起草时不得脱离依据编造；人工复核时逐条核对。
4. **分析必须读轨迹 + 调用 implementation-reviewer（红线）**：AI 代打分数时，**必须**读真实轨迹文件（`records/{任务}/{任务}-trajectory.jsonl`）并**必须**调用 `skills/implementation-reviewer/SKILL.md` 做代码产物评价，二者缺一即视为脱离依据、整批拒收；分析方法参照 `projects/code-eval-solo/skills/02-result-analysis.md`（把「读对话内容」适配为「读轨迹文件」）。交付文本仍须经 humanizer-zh 去 AI 化。
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

> **提交（对外接口，2026-09-10 已确认）**：`POST https://solo2.jzxhnh.com/api/v1/submissions`（地址在 `config.toml [submission].submit_url`）
> - 请求体：`{"data": {24 字段}, "schema_fingerprint": "cc4da53236368ac2"}`；其中 `trace_file` 是**附件数组** `[{"name": "…-trajectory.jsonl", "path": "uploads/<id>.jsonl", "size": 321940}]`——先传 `…/submissions/upload`（multipart 字段 `file`）拿 `path` 再回填。
> - 响应：`{"id":1196,"status":"SUBMITTED","round_no":1,"schema_stale":false,"message":…}`；`schema_stale=true` 说明表单字段变了。
> - 凭据在 `secrets.toml [submission]`：`cookie`（或 `token`）+ `username` / `password`；**cookie 约 2 天过期，脚本会自动登录刷新并回写**（`--login-only --commit` 可手动刷新）：登录结果缓存在 `projects/cc-solo/.solo_session.json`（gitignore），**未过期不会重复登录**，`--status` 查状态。字段规范在 `docs/submission/fields.json`（从 `submitfrom.js` 抽取，24 字段）。
> - ⚠️ 轨迹附件是**整份会话轨迹**，同一 SessionID 各轮共用 ⇒ **导出与提交要在该任务会话结束之后做**。
> - 生成与提交：`python scripts/cc-solo/build_eval_result.py` → `python scripts/cc-solo/submit_eval_result.py --result <json> --commit`（不加 `--commit` 为 dry-run）。细节见 [skills/04-export-submit.md](skills/04-export-submit.md)。

## 目录结构（详见 docs/structure-example.md）

```
projects/cc-solo/
├── SKILL.md                     # 本文件（索引导航）
├── config.toml                  # 项目配置（路径、类型、难度、评分、轮次上限）
├── secrets-simple.toml          # 本地敏感配置模板
├── README.md
├── docs/                        # runbook / structure-example / annotate-guide / 源 docx
├── skills/                      # 01-task-create / 02-round-capture / 03-score-annotate / 04-export-submit
└── templates/                   # task-info.md / round-file.md（submit-headers.csv 已随旧流程退役）

sessions/cc-solo/{SESSION_NAME}/            # 工作数据（gitignore；仅 demo 例子例外）
├── source-code/                 # 素材源 + 任务副本（由 "source code/" 改名）
│   └── {项目}/                  # 项目根
│       ├── {项目}/              # 素材源（唯一 git 仓库 = base commit 快照，原始源码）
│       │   ├── src/、README.md、.gitignore
│       │   └── .git/
│       ├── {项目}-bugfix/       # 类型分组（按类型 + 全局索引累加）
│       │   ├── {项目}-bugfix-01/  # 任务副本 = 复制素材源内容 + 改名（无 .git）
│       │   └── {项目}-bugfix-02/
│       ├── {项目}-codegen/
│       │   └── {项目}-codegen-06/
│       ├── {项目}-feature/
│       │   ├── {项目}-feature-11/
│       │   └── {项目}-feature-12/
│       ├── {项目}-understand/{项目}-understand-16/
│       ├── {项目}-refactor/{项目}-refactor-17/
│       ├── {项目}-engineering/{项目}-engineering-18/
│       └── {项目}-test/{项目}-test-19/
└── records/                     # 任务记录（R0N 模型：每任务一个目录，每轮一条数据）
    └── {项目}/
        └── {项目}-bugfix/
            └── {项目}-bugfix-01/            # 任务目录（= 任务名）
                ├── task-info.md             # 共享运行环境字段
                ├── {项目}-bugfix-01-R01.md  # 第 1 轮 = 一条数据（含五维打分）
                ├── {项目}-bugfix-01-R01-trajectory.jsonl   # 每轮轨迹切片
                └── {项目}-bugfix-01-trajectory.jsonl       # 完整轨迹
        …（{项目}-codegen/、{项目}-feature/ … 按类型分组，与 source-code 同名）

deliverables/cc-solo/{SESSION_NAME}/       # 评价结果（每轮一条）+ 核对 CSV + 质检报告
```

> **容器镜像与 Harness 口径（2026-09-10 起，务必先读 [docs/image-upgrade-review.md](docs/image-upgrade-review.md)）**：
>
> - **Mac**：镜像固定 `adminfather/benzhi-claude-code:20260909-isolated-git`（digest `sha256:f77014d9e56cd3db2ac96627a286814cb1aa9f0b4bb807bea98a01383c9bc4d8`）——**不要写 `latest`**（`latest` 已在 2026-09-09 指向同一隔离镜像，且会继续漂移）。该镜像强制：一道题一个容器、`/workspace` 启动时为空（初始代码由 agent 在容器启动后播种）、**会话不可恢复**（`--continue`/`--resume` 与 `docker start` 一概被拒）、`--cap-drop ALL`（不能 chown）、容器内 Claude Code 以 `--safe-mode --disable-slash-commands --tools 'Bash,Read,Write,Edit,Glob,Grep'` 启动（版本锁 2.1.197）。
> - **Windows**：镜像 `nicehey/benzhi-claude-code:1.0`（**没有换镜像**，换的是用法）；常驻容器 + `docker exec`，`claude --continue` 仍可用（仅限同一道题）；把**本题任务副本目录**直接挂载为 `/workspace`（因此不需要 `docker cp` 代码、不需要回导），并显式传 5 个模型 env。
> - **任务名 = 容器名（前缀 `cc-solo-`）+ 运行目录**共同承载题目身份；容器内不再有 `/workspace/<题号>` 这种路径，轨迹目录也不再带题号。
> - ⚠️ **Harness 口径需评测方裁定**：Mac 新镜像的工具集被裁剪（无 `Task` 子代理、无 `TodoWrite`、无联网抓取、无斜杠命令），与「Harness = Claude Code」的历史口径**不可直接互比**，尤其影响「任务规划」维度。提交前须在 `task-info.md` 记录镜像 digest 与隔离模式。

## 文档

| 文档 | 说明 |
|------|------|
| [image-upgrade-review.md](docs/image-upgrade-review.md) | **镜像升级影响评估（2026-09-09 新镜像）**：新旧对比、硬约束、改写依据、待实测/待确认清单 |
| [docs/submission/](docs/submission/) | **提交表单字段规范**：`submitfrom.js`（前端定义原件）+ `fields.json`（抽取产物，24 字段/选项/必填/校验；轨迹上传接口也在这里） |
| [runbook.md](docs/runbook.md) | 逐步操作手册（指令模板，Mac：一题一容器 + 启动后播种） |
| [runbook-windows.md](docs/runbook-windows.md) | 逐步操作手册（指令模板，Windows：一题一容器 + 挂载任务副本） |
| [CLAUDE_CODE_DOCKER_MAC.md](docs/CLAUDE_CODE_DOCKER_MAC.md) | Claude Code Docker 使用说明（Mac，**现行隔离镜像用法**） |
| [CLAUDE_CODE_DOCKER_windows.md](docs/CLAUDE_CODE_DOCKER_windows.md) | Claude Code Docker 使用说明（Windows，**现行走法：挂载本题文件夹**） |
| [WINDOWS_DOCKER_SETUP.md](docs/WINDOWS_DOCKER_SETUP.md) | Windows 从安装 Docker 到跑通的完整引导 |
| [archive/](docs/archive/) | **已废弃**：旧版常驻容器说明（`cc <题号>` + `docker cp` 搬代码），仅对旧的 `20260907`/`20260908` 标签有效 |
| [structure-example.md](docs/structure-example.md) | 完整目录结构样例（含路径映射） |
| [annotate-guide.md](docs/annotate-guide.md) | 评分表 / 原因写法 / 雷同题清单速查 |
| [ai-cliche-wordlist.md](docs/ai-cliche-wordlist.md) | **AI 痕迹词表与改写对照**：A 表四类（344 词）/ B 表三组（64 词）/ 跨轮次与前后对比 / 句式与标点层 / 正反例 / 公开来源清单（机器表以 `scripts/cc-solo/build_eval_result.py` 为准） |
| [ClaudeCcode 用户满意度标注.docx](docs/ClaudeCcode%20用户满意度标注.docx) | 项目源规范 |

## 脚本

| 脚本 | 说明 |
|------|------|
| `scripts/cc-solo/build_eval_result.py` | 生成评价结果（24 字段 × 每轮一条）+ 核对 CSV + 质检报告；词表与符号检查的唯一来源 |
| `scripts/cc-solo/check_round_files.py` | **轮次文件机械校验**（只读）：分数/描述/词表/符号/跨轮次与前后对比/轨迹文件一次跑完，有 error 返回码 1，可当导出前门禁；支持 `--project` `--task` |
| `scripts/cc-solo/lint_round_prompt.py` | **下一轮提示词校验**（只读）：查是否「只写现象、不分条、无改法措辞」，附建议类措辞与 B 表密度 warn |
| `scripts/cc-solo/extract_submit_fields.py` | 从平台表单定义抽取 `docs/submission/fields.json` |
| `scripts/cc-solo/submit_eval_result.py` | 上传轨迹附件 + 提交评价结果（默认 dry-run，`--commit` 才真提交） |
