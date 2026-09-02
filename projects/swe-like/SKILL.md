---
name: swe-like
description: "SWE-like 长程代码任务：基于真实开源 Repo 独立出题，Trae+Seed 单 Prompt 运行，Verify Rubric 验收，按收录标准入库并交付飞书。Use when: SWE 出题, 长程任务, 真实 repo 难题, Seed 评测, 题库建设。"
---

# SWE-like 长程代码任务（Swe-like Repo）

扩充真实且具有难度的 SWE 类题目，用于提升 Seed 模型在 SWE 类题目上的能力。人员画像：1 年以上开发者、有长期使用的开源 Repo、熟悉 Vibe Coding。模型与终端：**Trae CN + Seed Evolving**。

## 技能列表

| 序号 | 技能 | 文件 | 说明 |
|:--:|------|------|------|
| 1 | **题目创建** | [skills/01-task-create.md](skills/01-task-create.md) | 选 Repo + 锁版本 → 独立出题（不照抄 Issues）→ Verify Rubric → 生成任务目录 |
| 2 | **运行记录** | [skills/02-run-record.md](skills/02-run-record.md) | Trae+Seed 单 Prompt 运行 → 记录 Session ID / 有效轮数（= 模型输出步数）/ 产物 |
| 2a | **步数统计** | [skills/02-step-count.md](skills/02-step-count.md) | 有效轮数抓取顺序：文件操作 + 终端命令，防漏终端命令 |
| 3 | **验收复盘** | [skills/03-verify-review.md](skills/03-verify-review.md) | 对照 Verify Rubric 逐条验收 → 完成/质检判定 → 收录决策 |
| 4 | **交付导出** | [skills/04-export-delivery.md](skills/04-export-delivery.md) | 任务记录 → 24 字段映射（含 Type / Commit URL）→ 追加飞书多维表格（地址见 config.toml `[feishu]`） |

## 共享 Agent

| Agent | 路径 | 说明 |
|------|------|------|
| implementation-reviewer | `skills/implementation-reviewer/SKILL.md` | 代码实现评价（6 维度），用于验收复盘辅助 |
| humanizer-zh | `skills/humanizer-zh/SKILL.md` | 去 AI 写作痕迹（验收/质检文字） |

> 出题需求**独立提出**，不使用 prompt-architect 批量出题；不直接照抄 Top Open Issues、热门讨论或既有题目。

## 工作流程

```
题目创建 → Trae+Seed 单 Prompt 运行 → 验收复盘（含收录判定） → 交付导出
```

- **单 Prompt 纪律**：运行过程中不追加人工澄清、任务拆解或引导性提示；完整记录 Trae Session ID 与有效轮数，确保过程可追溯。
- **Verify Rubric 纪律**：验收前固定，评判口径一致，不得根据模型结果事后调整标准。
- **收录标准**（有效轮数 > 100 → 长程题收录；≤ 100 且实现明显差 → 难题收录；≤ 100 且实现较好 → 不收录）。
- **步数统计**：跑完任务尽快把 Session ID + 步数统计文档发给 Codex 读取 Trae 日志，得到「模型输出步数」= 有效轮数（有效 TC 次数）记入 `run-log.md`（日志动态清除，务必及时）。
- **表单规范**（见 `docs/内部规范.md`）：字段不得含 Markdown 标签（去 AI 味）；本轮语言仅限 Go / Python；一个 Repo 最多 3 条；Prompt 像真实 MR 需求，题要和 Repo 匹配。

## 文档

| 文档 | 说明 |
|------|------|
| [docs/SWE-like Repo-v2.md](docs/SWE-like%20Repo-v2.md) | 出题规范（试行·现行版）：出题/交付示例/DeepSWE 参考/反例/收录标准（v1 已归档） |
| [docs/内部规范.md](docs/内部规范.md) | 内部规范：账号积分 / 步数统计 / 表单填写规范 / 省积分经验 |
| [docs/步数统计.md](docs/步数统计.md) | Trae Session 有效 TC 次数自查指南（=「模型输出步数」统计口径） |
| [docs/runbook.md](docs/runbook.md) | 逐步操作手册（指令模板） |
| [docs/structure-example.md](docs/structure-example.md) | 完整目录结构样例（含路径映射） |

## 目录结构

```
projects/swe-like/
├── config.toml                 # 项目配置（出题参数、收录标准、飞书配置）
├── SKILL.md                    # 本文件（索引导航）
├── skills/                     # 详细技能文件
│   ├── 01-task-create.md       # 题目创建
│   ├── 02-run-record.md        # 运行记录
│   ├── 02-step-count.md        # 步数统计（有效轮数抓取顺序）
│   ├── 03-verify-review.md     # 验收复盘
│   └── 04-export-delivery.md   # 交付导出（追加到飞书多维表格）
├── secrets-simple.toml         # 本地敏感配置模板
├── docs/
│   ├── SWE-like Repo-v2.md     # 出题规范（试行·现行版）
│   ├── 内部规范.md              # 账号积分 / 步数统计 / 表单填写规范 / 省积分
│   ├── 步数统计.md              # 有效 TC 次数自查指南
│   ├── runbook.md
│   └── structure-example.md
├── templates/
│   ├── task-form.md            # 出题表单
│   └── delivery-form.md        # 交付表单（24 字段映射）
└── scripts/
    ├── create_task.py          # 题目创建脚本（生成任务目录，含空 session.md）
    └── append_delivery_feishu.py   # 交付导出脚本
```

## 快速开始

1. 配置 `secrets.toml`（从 `secrets-simple.toml` 复制并填入真实值）
2. 使用 [题目创建](skills/01-task-create.md) 选 Repo 并出题，生成任务目录
3. 用户在 Trae 中让 Seed 单 Prompt 运行，使用 [运行记录](skills/02-run-record.md) 记录过程（含尽快获取步数）
4. 使用 [验收复盘](skills/03-verify-review.md) 对照 Verify Rubric 验收并做收录决策
5. 使用 [交付导出](skills/04-export-delivery.md) 把任务记录追加到飞书多维表格
