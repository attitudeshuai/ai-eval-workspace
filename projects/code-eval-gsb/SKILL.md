---
name: code-eval-gsb
description: "多模型代码对比评估（GSB）。源码推送 GitHub → 创建模型分支 → 生成提示词 → 轮次评价 → 汇总分析。Use when: 代码评估, 多模型对比, GSB 评测, 模型 PK, 1v1/2v1 对比。"
---

# 多模型代码对比评估（Code Eval GSB）

对多个 AI 模型在相同代码任务下的表现进行对比评估。

## 技能列表

| 序号 | 技能 | 文件 | 说明 |
|:--:|------|------|------|
| 1 | **提示词生成** | [skills/01-prompt-generate.md](skills/01-prompt-generate.md) | 源码推送 GitHub → 创建分支 → 生成提示词 → 写入结果文件 |
| 2 | **轮次分析** | [skills/02-round-review.md](skills/02-round-review.md) | 逐轮评价模型回答，满意/不满意判定，追问提示词生成 |
| 3 | **汇总** | [skills/03-summary-analysis.md](skills/03-summary-analysis.md) | 读取全部对话+代码变更，5 基础维度打分 + 4 Add-on 维度，GSB对比结论，生成汇总表单 |
| 4 | **交付导出** | [skills/04-export-delivery.md](skills/04-export-delivery.md) | 汇总确认后，把表单追加为一条记录到飞书多维表格（地址见 config.toml `[feishu]`） |

## 共享 Agent

| Agent | 路径 | 说明 |
|------|------|------|
| implementation-reviewer | `skills/implementation-reviewer/SKILL.md` | 代码实现评价（6维度） |
| humanizer-zh | `skills/humanizer-zh/SKILL.md` | 去 AI 写作痕迹 |
| prompt-architect | `skills/prompt-architect/SKILL.md` | 提示词生成 |

## 工作流程

```
提示词生成 → 用户在各模型中执行对话 → 轮次分析（可多轮） → 汇总 → 交付导出
```

- **轮次限制（0825 期）**：每题交互轮次 **≤ 3**（无最低轮数要求）；首轮未完成可继续对话引导，总轮次不得超过 3。工程故障（网络波动导致请求失败）不计入轮次，轮次超限需人为"继续"的计入轮次
- **0-1 代码生成**：origin 仓只含标准命名 `README.md` 需求规格书（项目名 = 需求 md 文件名）；首轮提示词固定为"通读 README、按文档开发整套系统"口径，第 2 轮起按模型交付与 README 的差距追问
- **Max 模式（0825 期）**：**60% 任务开启 Max，40% 不开启**（更复杂/更长程任务开启）；同一任务窗口内保持一致不可中途切换，同一任务所有横评模型必须一致；开启后自检对话底部显示 `X% of 1000K`
- **打断记录（0825 期）**：打断后重新给指令等价于新开一轮，计入 3 轮上限（工程故障例外）；四个模型一视同仁；交付表含"是否打断模型-模型名 / 打断分析反馈-模型名"字段
- **长程任务判定**：修改 ≥ 5 个文件、跨多模块、需多次调试纠错的为长程任务

## 文档

| 文档 | 说明 |
|------|------|
| [Seed模型 GSB 众测方案（0825）.md](docs/Seed模型GSB众测方案-0825.md) | 本期众测方案（出题分布、轮次、打分维度、交付字段） |
| [Seed模型 GSB 众测方案（0731）.md](docs/Seed模型%20GSB%20众测方案（0731）.md) | 上一期众测方案（存档参考） |
| [runbook.md](docs/runbook.md) | 逐步操作手册（指令模板） |
| [structure-example.md](docs/structure-example.md) | 完整目录结构样例（含路径映射） |

## 对比模式

从 `config.toml` 的 `[[models]]` 和 `[[comparisons]]` 读取，换模型只需改配置：

```toml
# 0825 期：4 模型 Anchor-based，共 3 组 GSB（无 Same 选项，必须二选一）
[[models]]; name = "Odysseus"; slug = "odysseus"    # anchor
[[models]]; name = "Athena";   slug = "athena"
[[models]]; name = "Poseidon"; slug = "poseidon"
[[models]]; name = "Cyclops";  slug = "cyclops"
[[comparisons]]; pair = [0, 1]; required = true   # Odysseus vs Athena
[[comparisons]]; pair = [0, 2]; required = true   # Odysseus vs Poseidon
[[comparisons]]; pair = [0, 3]; required = true   # Odysseus vs Cyclops
```

## 目录结构

```
projects/code-eval-gsb/
├── config.toml                 # 项目配置（模型、对比规则、评估参数）
├── SKILL.md                    # 本文件（索引导航）
├── skills/                     # 详细技能文件
│   ├── 01-prompt-generate.md   # 提示词生成
│   ├── 02-round-review.md      # 轮次分析
│   ├── 03-summary-analysis.md  # 汇总
│   └── 04-export-delivery.md   # 交付导出（追加到飞书多维表格）
├── secrets-simple.toml         # 本地敏感配置模板
├── README.md
├── docs/
│   ├── runbook.md
│   └── structure-example.md
└── templates/
    ├── prompt-file.md
    └── summary-form.md
```

## 快速开始

1. 配置 `secrets.toml`（从 `secrets-simple.toml` 复制并填入真实值）
2. 使用 [提示词生成](skills/01-prompt-generate.md) 初始化项目
3. 用户在 Trae 中让各模型分别完成提示词
4. 使用 [轮次分析](skills/02-round-review.md) 逐轮评价
5. 使用 [汇总](skills/03-summary-analysis.md) 生成最终对比报告
6. 使用 [交付导出](skills/04-export-delivery.md) 把汇总追加到飞书多维表格
