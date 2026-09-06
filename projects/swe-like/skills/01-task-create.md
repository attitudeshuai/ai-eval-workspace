---
name: swe-task-create
description: "SWE 题目创建：给定一个 Repo，独立出一道真实且有难度的题（不照抄 Issues，不做同一诉求内置化改写），生成 harbor 交付包（task.toml + instruction.md + nl_rubric.yaml + Dockerfile）。Use when: SWE 出题, 选 repo, 写需求, nl_rubric, Dockerfile。"
---

# SWE 题目创建（Task Create）

> 规范见 `../docs/SWE-like Repo-v3.md`、`../docs/内部规范-v1.md`、`../docs/常见问题.md`。
> 交付形态：一题一个 zip（伪 Harbor），目录名 = 题目名称。骨架见 `../templates/harbor/`。

## 功能概述

这个技能负责：

- 选择开源 Repo，记录 `repo_url` 与 40 位完整 `base_commit`
- 独立提出需求（不照抄 Issues，也不做「同一诉求内置化改写」）
- 写 `instruction.md`（需求 Prompt 原文）
- 写 `tests/nl_rubric.yaml`（≥5 条，含 f2p / p2p）
- 写 `environment/Dockerfile`（ARG BASE_SHA = base_commit）
- 生成 `task.toml`（16 键）

这个技能不负责：运行模型（02）、验收（03）、回填底稿（04）。

## 交付结构（伪 Harbor）

```
<题目名称>/
├── task.toml                 # 16 键底稿字段
├── instruction.md            # 需求 Prompt 原文
├── environment/Dockerfile    # 基线 public.ecr.aws/x8v8d7g8/mars-base:latest
├── tests/nl_rubric.yaml      # 自然语言判分标准
├── solution/                 # 本批允许留空
└── evidence/                 # 运行后取证（trajectory + model.patch + screenshots/）
```

## 候选池（一个 repo 一个文件）

- 每个 repo 一次出 **10 个候选提示词**，集中写入 `sessions/swe-like/<session>/tasks/{repo}/prompt-candidates.md`；不同 repo 不混放。
- 候选入池前三重自检：①本地代码验证功能不存在（grep 证据）；②公开 Issues 查重（open + closed，见下）；③难度门槛自检（见下）。
- 池内每条记录：题名、base_commit、复杂度要点（命中的难度维度）、查重证据（搜索词 + issue 编号 + 排除理由）、提示词正文。
- 候选**通过需求预检后**才落地：用户反馈通过编号（如 `swe {repo} create 通过：候选 1、2`），AI 逐条把正文复制进任务目录的 instruction.md，补齐 rubric / Dockerfile / task.toml，检查分支与 worktree 是否就位，并跑 `preflight_check.py --stage create` 自检。
- 被击毙的方向（撞 issue / base 已实现 / 超出 repo 能力）记入该文件末尾的「调研阵亡名单」，防止重复踩坑。

## 执行流程

1. **选 Repo + 锁 base_commit**：40 位完整 SHA，须与 Dockerfile 的 ARG BASE_SHA 一致。
2. **生成候选池**：对该 repo 出 10 个候选提示词，写入 `tasks/{repo}/prompt-candidates.md`（一个 repo 一个文件，格式见上节「候选池」）；每个候选提示词**起草时即过 humanizer-zh**（见下节「去 AI 化」）。
3. **写 instruction.md**：候选通过需求预检后，把正文落到任务目录。平实自然语言，像真实 MR 需求；明确目标、适用场景、可观察预期行为；不用 Markdown 标签，也不用 `-`/`*` 等列表符号，并禁用 `「」`、`——`、反引号、加粗滥用（见下节「去 AI 化」）——预期行为用完整句子分段叙述；不写死实现。
4. **写 nl_rubric.yaml**：≥5 条，每条 `id` + `type`(f2p/p2p) + `text`；至少各 1 条 f2p 和 p2p。
5. **写 Dockerfile**：基线 `public.ecr.aws/x8v8d7g8/mars-base:latest`，ARG BASE_SHA = base_commit，装仓库依赖（含需求新增依赖）。
6. **写 task.toml**：16 键，title = zip 目录名；除 submitter 外每键对应一个底稿列。

## 去 AI 化（强制红线，必做）

**全程自动套 humanizer-zh**：从候选提示词、instruction.md、nl_rubric.yaml 每条 text，到 task.toml 的自然语言字段（真实性与难度说明、产物结果、notes）以及底稿交付字段，**每一步产物一写出来就立即过** `skills/humanizer-zh/SKILL.md`，而不是到最后统一补。命中即改，不允许保留；未过 humanizer-zh 的文本不得进入候选池、落地或交付，预检/验收/交付脚本都会据此打回：

- `「」` 直角引号 → 一律换成中文全角双引号 `""`
- `——` 双破折号 → 按转折/解释/列举关系改逗号、冒号或删掉
- 反引号包裹方法名/字段名/命令 → 直接写出名称或转中文，去除代码格式感
- 加粗滥用、`**XX：**` 内联标题列表、emoji、三段式（恰好罗列三项）、否定式排比（不仅…而且…）→ 去除或改写
- Markdown 标签、`-`/`*` 列表符号 → 改用完整句子分段叙述
- AI 高频词（此外、至关重要、赋能、彰显、格局、然而等）→ 删除或用更朴素的说法

判定标准：以上任一残留即出题阶段打回重写，不得靠「提交后再修」通过。

## 难度门槛（自检清单）

预检高频打回原因：「太简单」。定稿前按清单自检，**至少命中 3 项**才算复杂度足够：

- **跨模块/跨层**：改动横跨 2 个以上模块或层次（如请求处理 + 配置解析 + 状态管理）
- **状态生命周期**：涉及启动、运行、重载、失败恢复等状态的语义设计
- **并发与竞态**：请求间隔离、共享状态的原子性、goroutine / 进程安全
- **配置面**：需要新增配置项（数据格式、解析、校验、非法值处理）
- **边界与失败路径**：有非平凡分支语义（全部不可用、部分恢复、空结果、超大输入等）
- **向后兼容**：默认行为不变、旧配置/旧数据不回归，且这一点本身需要专门设计

复杂度不足的反例（必被打回）：单文件改动；新增一个配置开关；对现有能力的薄封装（语法糖）；只有 happy path 的功能。

## 公开 Issues 相似查重（必做，加严流程）

1. **先查代码，再写题**：base_commit 越新，越多「明显缺口」其实已被填补。在本地仓库 grep 确认功能不存在（含相近命名、相近能力的变体），避免「已有功能」型打回。
2. **open + closed 都查**：closed issue 同样算重复（历史被拒或已搁置的同一诉求）。
3. **同义词多搜几轮**：中英文、功能名/场景名都试（如 mirror / shadow / copy / tee）。
4. **判定标准是「可观察行为重合」**：核心对象、触发阶段、预期行为三者一致即判高相似，换实现方式不等于独立；命中即换题，不得靠改写 Prompt / Rubric 硬过。
5. **留证**：搜索词、命中/排除的 issue 编号与理由记入 task.toml 的 notes，供预检复核。

### 预检失败案例（caddy 实践，2026-09）

| 候选 | 死因 |
|------|------|
| p2c + peak-EWMA 负载均衡 | 撞 open issue #7879（同一诉求） |
| 一致性哈希负载均衡 | 撞 closed issue #1804（closed 也算重复） |
| 访问日志 sampling | base_commit 已实现（LogSampling + Caddyfile sampling 块） |
| map 正则捕获映射 / 默认值 | base_commit 已实现（input_regexp / Defaults） |
| 自定义 browse 模板 | base_commit 已实现（template_file） |
| 上游 CONNECT 代理 | base_commit 已实现（HTTPTransport Proxy 字段） |
| admin 配置 dry-run | 撞 open issue #4717 |

## 反例：不应收录的伪需求

| 反例需求 | 问题类型 | 为什么不收录 |
|------|------|------|
| 为 Claude Code 增加完整 CoT 的自动保存、展示和导出功能。 | 无法由 Repo 独立实现 | 依赖上游模型能力与安全策略变化，客户端 Repo 无法获取或还原 |
| 为 Codex CLI 增加 side chat。 | 已有功能 | Codex CLI 已提供 `/side`，属未查重的重复需求 |
| 让 FastAPI 内置 Kubernetes 自动扩缩容控制器。 | 与 Repo 定位不符 | 属部署与集群编排，非 Web 框架核心职责 |
| 为 Flask 增加「未处理 HTTPException 默认返回 JSON」的配置项。 | 公开 Issue 高相似（同一诉求内置化改写） | Issue #2144 已要求 want all Errors return JSON，#5255 亦记录同场景；换实现方式仍是同一诉求 |

## nl_rubric.yaml 规范

- 每条一句自然语言，只额外标 `type`，不拆字段级、不写死文件名/类名/实现方案。
- `f2p`：原本做不对、新需求下应该做对；`p2p`：原本就能对、新需求下也应保持对。
- 至少各 1 条 f2p 和 p2p，整体不少于 5 条。

## 注意事项

1. 需求必须独立提出，**不得照抄 Issues**，也不得「对同一诉求做内置化改写」。
2. 本轮语言仅 Python / Go；一个 Repo 最多 5 条。
3. 题要和 Repo 匹配，是该 Repo 管理员可能会合并到主分支的需求。
4. base_commit 与 Dockerfile BASE_SHA 必须一致。
