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
| 3 | **汇总** | [skills/03-summary-analysis.md](skills/03-summary-analysis.md) | 读取全部对话+代码变更，6维度打分，GSB对比结论，生成汇总表单 |

## 共享 Agent

| Agent | 路径 | 说明 |
|------|------|------|
| implementation-reviewer | `skills/implementation-reviewer/SKILL.md` | 代码实现评价（6维度） |
| humanizer-zh | `skills/humanizer-zh/SKILL.md` | 去 AI 写作痕迹 |
| prompt-architect | `skills/prompt-architect/SKILL.md` | 提示词生成 |

## 工作流程

```
提示词生成 → 用户在各模型中执行对话 → 轮次分析（可多轮） → 汇总
```

- **多轮任务**：每个模型最多支持 3 轮追问（首轮 + 2 次追问），不满意时自动生成下一轮追问提示词
- **长程任务判定**：修改 ≥ 5 个文件、跨多模块、需多次调试纠错的为长程任务

## 文档

| 文档 | 说明 |
|------|------|
| [runbook.md](docs/runbook.md) | 逐步操作手册（指令模板） |
| [structure-example.md](docs/structure-example.md) | 完整目录结构样例（含路径映射） |

## 对比模式

从 `config.toml` 的 `[[models]]` 和 `[[comparisons]]` 读取，换模型只需改配置：

```toml
# 2 模型 1v1
[[models]]; name = "A"; slug = "model-a"
[[models]]; name = "B"; slug = "model-b"
[[comparisons]]; name = "A vs B"; pair = [0, 1]; required = true

# 3 模型 2v1
[[models]]; name = "基准"; slug = "baseline"
[[models]]; name = "对比1"; slug = "compare1"
[[models]]; name = "对比2"; slug = "compare2"
[[comparisons]]; pair = [0, 1]; required = true
[[comparisons]]; pair = [0, 2]; required = true
[[comparisons]]; pair = [1, 2]; required = false  # 可选
```

## 目录结构

```
projects/code-eval-gsb/
├── config.toml                 # 项目配置（模型、对比规则、评估参数）
├── SKILL.md                    # 本文件（索引导航）
├── skills/                     # 详细技能文件
│   ├── 01-prompt-generate.md   # 提示词生成
│   ├── 02-round-review.md      # 轮次分析
│   └── 03-summary-analysis.md  # 汇总
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
