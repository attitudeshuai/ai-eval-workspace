---
name: swe-like
description: "SWE-like 长程代码任务：基于真实开源 Repo 独立出题，Trae/TraeX/miniswe + Seed Evolving 单 Prompt 运行，Verify Rubric 验收，按收录标准以伪 Harbor zip 形式交付。Use when: SWE 出题, 长程任务, 真实 repo 难题, Seed 评测, 题库建设。"
---

# SWE-like 长程代码任务（Swe-like Repo）

扩充真实且具有难度的 SWE 类题目，用于提升 Seed 模型在 SWE 类题目上的能力。人员画像：1 年以上开发者、有长期使用的开源 Repo、熟悉 Vibe Coding。模型与终端：**Trae CN（推荐 TraeX）或 mini-swe-agent + Seed Evolving**。

> 现行规范：`docs/SWE-like Repo-v3.md`（出题与交付）、`docs/内部规范-v1.md`（积分/步数/表单）、`docs/常见问题.md`。旧 v1/v2 已归档。

## 技能列表

| 序号 | 技能 | 文件 | 说明 |
|:--:|------|------|------|
| 1 | **题目创建** | [skills/01-task-create.md](skills/01-task-create.md) | 选 Repo + 锁 base_commit → 独立出题（不照抄 Issues / 不内置化改写）→ 生成 harbor 交付包（task.toml + instruction.md + nl_rubric.yaml + Dockerfile） |
| 2 | **运行记录** | [skills/02-run-record.md](skills/02-run-record.md) | 单 Prompt 单轮运行 → 记录 Session ID / 有效轮数 / 取证（trajectory + patch + screenshots） |
| 2a | **步数统计** | [skills/02-step-count.md](skills/02-step-count.md) | agent step 口径：TraeX 用 count_steps.py，miniswe 取 api_calls |
| 3 | **验收复盘** | [skills/03-verify-review.md](skills/03-verify-review.md) | 对照 nl_rubric.yaml 逐条验收 → 完成/未完成判定 → 收录决策 |
| 4 | **交付导出** | [skills/04-export-delivery.md](skills/04-export-delivery.md) | 填 task.toml → toml2base.py 体检（--dry-run）→ 回填底稿网站表单 |

## 共享 Agent

| Agent | 路径 | 说明 |
|------|------|------|
| implementation-reviewer | `skills/implementation-reviewer/SKILL.md` | 代码实现评价（6 维度），用于验收复盘辅助 |

> 出题需求**独立提出**，不使用 prompt-architect 批量出题；不照抄 Issues，也不得「对某 issue 同一诉求做内置化改写」。

## 工作流程

```
题目创建（harbor 包） → 单 Prompt 运行 + 取证 → 验收复盘（含收录判定） → toml2base.py 回填底稿
```

- **单 Prompt 纪律**：运行过程中不追加人工澄清、任务拆解或引导性提示；完整记录 Session ID 与有效轮数（agent step）。
- **Rubric 纪律**：nl_rubric.yaml 验收前固定，评判口径一致，不得事后调整。
- **收录标准**：有效轮数 > 100 → 长程题；≤ 100 且「完成」→ 不收录；≤ 100 且「未完成」→ 难题。
- **步数统计**：agent step 口径（一次模型调用 = 1 步），TraeX 用 count_steps.py 对原始轨迹计数，miniswe 取 api_calls（见 `skills/02-step-count.md`）。
- **表单规范**（见 `docs/内部规范-v1.md`）：字段不得含 Markdown 标签；本轮语言仅 Go / Python；一个 Repo 最多 5 条；Prompt 像真实 MR 需求，题要和 Repo 匹配。

## 文档

| 文档 | 说明 |
|------|------|
| [docs/SWE-like Repo-v3.md](docs/SWE-like%20Repo-v3.md) | 出题规范（现行）：交付结构 / task.toml / instruction.md / nl_rubric.yaml / Dockerfile / 取证 / 收录标准 / 回填 |
| [docs/内部规范-v1.md](docs/内部规范-v1.md) | 内部规范：Commit URL / 积分 / 步数统计（Hook）/ 表单填写 / 省积分 |
| [docs/常见问题.md](docs/常见问题.md) | 常见问题：issue 查重 / 轮次少 / 模板化 |

## 目录结构

```
projects/swe-like/
├── config.toml                 # 项目配置（出题参数、收录标准、harness）
├── SKILL.md                    # 本文件（索引导航）
├── skills/                     # 详细技能文件
│   ├── 01-task-create.md       # 题目创建
│   ├── 02-run-record.md        # 运行记录
│   ├── 02-step-count.md        # 步数统计（agent step 口径）
│   ├── 03-verify-review.md     # 验收复盘
│   └── 04-export-delivery.md   # 交付导出（toml2base.py 回填底稿）
├── docs/
│   ├── SWE-like Repo-v3.md     # 出题规范（现行）
│   ├── 内部规范-v1.md           # 内部规范
│   ├── 常见问题.md              # 常见问题
│   └── runbook.md
└── templates/
    └── harbor/                 # 伪 Harbor 交付模板
        ├── task.toml
        ├── instruction.md
        ├── nl_rubric.yaml
        └── Dockerfile
```

## 快速开始

1. 用 [题目创建](skills/01-task-create.md) 选 Repo、锁 base_commit、独立出题，生成 harbor 交付包（`templates/harbor/` 为骨架）。
2. 用户在 Trae/TraeX/miniswe 中让 Seed 单 Prompt 运行，用 [运行记录](skills/02-run-record.md) 记录过程并取证（trajectory + patch + screenshots）。
3. 用 [步数统计](skills/02-step-count.md) 按 agent step 口径算有效轮数。
4. 用 [验收复盘](skills/03-verify-review.md) 对照 nl_rubric.yaml 验收并做收录决策。
5. 用 [交付导出](skills/04-export-delivery.md) 填 task.toml，经 toml2base.py 体检后回填底稿网站表单。
