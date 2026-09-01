---
name: swe-verify-review
description: "SWE 验收复盘：对照已冻结的 Verify Rubric 逐条验收模型产物，判定是否完成需求与是否通过质检，并按收录标准做收录决策。Use when: SWE 验收, Verify Rubric, 收录判定, 质检。"
---

# SWE 验收复盘（Verify & Review）

> 配置从 `../config.toml` 读取。
> 依赖 agent：`skills/implementation-reviewer/SKILL.md`（辅助评审）、`skills/humanizer-zh/SKILL.md`（去 AI 化，如启用）

运行完成后，对照**已冻结**的 Verify Rubric 逐条验收模型产物，判定完成度与质检结果，并按收录标准决定是否入库。

## 功能概述

1. 读取 `verify-rubric.md`（验收前已固定，不得事后倒改）
2. 读取 `run-log.md` / `result.md` / 产物补充材料（patch、verifier 日志）
3. 逐条对照 Rubric 验收，记录通过/失败
4. 判定是否完成需求（完成 / 部分完成 / 未完成 / 无法判断）
5. 判定是否通过质检（通过 / 未通过）
6. 按收录标准做收录决策（长程题 / 难题 / 不收录）
7. 写入 `review.md`

这个技能不负责：

- 修改 Verify Rubric 或需求 Prompt（冻结）
- 替代人工确认最终判定（Reviewer 字段由人工填写确认）

## 命令

| 命令 | 说明 |
|------|------|
| review | 默认命令。读取 Rubric + 产物 → 逐条验收 → 完成/质检判定 → 收录决策 → 写入 review.md |
| verify | 仅执行 Rubric 逐条验收，输出通过/失败清单，不写 review.md |

## 执行流程

1. **读取冻结的 Rubric**：`tasks/{task-id}/verify-rubric.md`。⚠️ 验收开始后 Rubric 即冻结，不得根据模型结果调整。
2. **读取运行记录**：`run-log.md`（Session ID / 有效轮数）、`result.md`（产物描述）、产物补充材料（`model.patch`、verifier 日志、失败测试列表等）。
3. **逐条验收**：对 Rubric 每条，核对产物证据（可运行验证优先），记录：
   - 通过：产物满足该条可观察行为与预期结果
   - 失败：产物不满足，或无法复现/无证据
4. **调用 `implementation-reviewer`**（可选辅助）：对代码产物做 6 维度评审，为"实现明显差"判断提供依据。
5. **完成度判定**：
   - 完成：Rubric 全部通过
   - 部分完成：部分通过
   - 未完成：基本未通过
   - 无法判断：产物缺失或运行环境不可复现
6. **质检判定**：
   - 通过：题面验收全部满足
   - 未通过（题面验收未全部满足）：存在任一 Rubric 失败
7. **收录决策**（`config.toml [task]`）：

   | 运行结果 | 是否收录 | 标注 |
   |------|------|------|
   | 有效轮数 > `long_horizon_min_rounds`，效果好或差 | 收录 | 长程题 |
   | 有效轮数 ≤ `long_horizon_min_rounds`，但实现明显差 | 收录 | 难题 |
   | 有效轮数 ≤ `long_horizon_min_rounds`，且实现较好 | 不收录 | — |
8. **（可选）去 AI 化**：若 `config.toml [review].use_humanizer = true`，验收/质检文字经 `humanizer-zh` 处理。
9. **写入 `review.md`**：完成度、质检、Reviewer、收录判定、备注。

## 路径规则

```
# 输入
{work_root}/{session}/tasks/{task-id}/verify-rubric.md
{work_root}/{session}/tasks/{task-id}/run-log.md
{work_root}/{session}/tasks/{task-id}/result.md

# 输出
{work_root}/{session}/tasks/{task-id}/review.md
```

## 交付字段前置填写

验收阶段确定以下交付表字段：

| 交付表字段 | 来源 |
|------|------|
| 是否完成需求 | 完成度判定（单选：完成 / 部分完成 / 未完成 / 无法判断） |
| Reviewer | 验收人 |
| 是否通过质检 | 质检判定（单选：通过 / 未通过（题面验收未全部满足）） |
| 备注 | 收录判定结论（长程题/难题/不收录）及其他补充 |

## 注意事项

1. **Rubric 冻结**：验收开始后不得根据模型结果调整标准，评判口径保持一致。
2. **证据驱动**：每条验收须有可复现证据（运行结果、日志、patch），避免主观。
3. **收录判定**按 `config.toml` 标准执行；不收录的题目仍可保留任务目录存档，但**不交付**飞书（除非人工确认）。
4. `review.md` 完成后，`【待填写】` 占位字段需人工确认后才可进入交付导出。
