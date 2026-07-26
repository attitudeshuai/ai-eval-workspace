---
name: code-eval-solo
description: "单模型代码评估。根据项目源码批量生成提示词、收集模型回答、分析评估模型代码能力。Use when: 代码评估, 单模型评测, 批量提示词生成, Bug修复/代码生成/Feature迭代等任务类型的模型能力分析。"
---

# 单模型代码评估（Code Eval Solo）

对单个 AI 模型的代码能力进行批量评估：按任务类型生成多条提示词，收集模型回答，逐条分析是否完成 prompt 要求。

## 技能列表

| 序号 | 技能 | 文件 | 说明 |
|:--:|------|------|------|
| 1 | **提示词生成** | [skills/01-prompt-generate.md](skills/01-prompt-generate.md) | 批量生成提示词 → Bug 注入 → git 推送 |
| 2 | **分析** | [skills/02-result-analysis.md](skills/02-result-analysis.md) | implementation-reviewer + 10维度过程分析 → 评价结果 |
| 3 | **结果导出** | [skills/03-export-results.md](skills/03-export-results.md) | 评价结果 → CSV（含 Session ID / Commit ID 验证） |
| 4 | **提示词导出** | [skills/04-export-prompt.md](skills/04-export-prompt.md) | 提示词文件 → CSV（仅含有效 Session ID 轮次） |

## 共享 Agent

| Agent | 路径 | 说明 |
|------|------|------|
| implementation-reviewer | `skills/implementation-reviewer/SKILL.md` | 代码实现评价（6维度） |
| humanizer-zh | `skills/humanizer-zh/SKILL.md` | 去 AI 写作痕迹 |
| prompt-architect | `skills/prompt-architect/SKILL.md` | 提示词生成 |

## 工作流程

```
提示词生成 → Git 推送 → 用户 Trae 执行 → 分析（可多轮） → 结果导出 → 提示词导出
```

- **多轮任务**：提示词文件支持最多 5 轮对话，分析后生成下一轮推荐提示词
- **双路分析**：路线 A（代码产物，implementation-reviewer）+ 路线 B（对话过程，10维度）
- **Git 驱动**：所有提示词在主仓 main 分支执行，commit message = trae session id

## 文档

| 文档 | 说明 |
|------|------|
| [runbook.md](docs/runbook.md) | 逐步操作手册（指令模板） |
| [structure-example.md](docs/structure-example.md) | 完整目录结构样例（含路径映射） |
| [workflow.md](docs/workflow.md) | 详细技术流程 |
