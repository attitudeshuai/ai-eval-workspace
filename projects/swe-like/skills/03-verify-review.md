---
name: swe-verify-review
description: "SWE 验收复盘：对照 nl_rubric.yaml 逐条验收，判定 requirement_met，按收录标准做收录决策，写 run_result 到 task.toml。Use when: SWE 验收, nl_rubric, requirement_met, 收录判定。"
---

# SWE 验收复盘（Verify & Review）

> 规范见 `../docs/SWE-like Repo-v3.md`（第 5 / 6 节）。

## 功能概述

1. 读取 `tests/nl_rubric.yaml`（验收前已冻结，不得事后倒改）
2. 逐条验收（f2p / p2p），记录通过 / 失败
3. 判定 `requirement_met`（完成 / 部分完成 / 未完成 / 无法判断）
4. 按收录标准做收录决策
5. 写 `run_result`（逐条对应 rubric）回填 `task.toml`

## 命令

| 命令 | 说明 |
|------|------|
| review | 默认命令。读 rubric + 产物 → 逐条验收 → requirement_met + 收录决策 → 写 task.toml 的 run_result |
| verify | 仅执行 rubric 逐条验收，输出通过/失败清单 |

## 执行流程

1. **读冻结的 rubric**：`tests/nl_rubric.yaml`。验收开始后冻结，不得根据模型结果调整。
2. **逐条验收**（可运行验证优先），记录：
   - 通过：产物满足该条可观察行为与预期结果
   - 失败：产物不满足，或无法复现 / 无证据
3. **判定 requirement_met**：
   - 完成：全部通过
   - 部分完成：部分通过
   - 未完成：基本未通过
   - 无法判断：产物缺失或运行环境不可复现
4. **收录决策**（只看「有效轮数 + requirement_met」两列，运行完即可自判，不等质检）：

   | 有效轮数 | requirement_met | 收录 |
   |------|------|------|
   | > 100 | 任意 | 长程题 |
   | ≤ 100 | 完成 | 不收录（不计酬） |
   | ≤ 100 | 部分完成 / 未完成 / 无法判断 | 难题 |

5. **写 run_result**：逐条对应 rubric，每条一行：`rubric id + 通过/未通过 + 未通过原因`，回填 `task.toml`。

## 注意事项

1. **Rubric 冻结**：验收开始后不得根据模型结果调整标准。
2. **证据驱动**：每条验收须有可复现证据（运行结果、日志、patch），避免主观。
3. **收录只看两列**：有效轮数 + requirement_met，与实现好坏无关。
4. **run_result 必须逐条对应 rubric**，且与 requirement_met 一致；矛盾会被退回。
