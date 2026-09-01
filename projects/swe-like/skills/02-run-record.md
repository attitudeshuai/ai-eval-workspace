---
name: swe-run-record
description: "SWE 运行记录：把需求 Prompt 提交给 Trae CN + Seed Evolving 单 Prompt 运行，记录 Trae Session ID、有效轮数与产物。Use when: SWE 运行, 记录 Session ID, 有效轮数。"
---

# SWE 运行记录（Run Record）

> 配置从 `../config.toml` 读取。

出题完成后，由用户把 `task.md` 的需求 Prompt 交给 **Trae CN + Seed Evolving** 运行。本技能负责把运行过程完整、可追溯地记录下来。

## 功能概述

这个技能负责：

- 确认任务目录与需求 Prompt 就绪
- 记录 Trae Session ID（原文复制）与有效轮数
- 记录产物结果描述与产物补充材料（patch / verifier 日志 / 测试日志等）
- 写入 `run-log.md` / `result.md`

这个技能不负责：

- 追加人工澄清、任务拆解或引导性提示（**单 Prompt 纪律，严禁**）
- 修改需求 Prompt 或 Verify Rubric
- 评价模型表现（由 `03-verify-review.md` 负责）

## 命令

| 命令 | 说明 |
|------|------|
| run | 默认命令。提示用户到 Trae 执行，执行完成后录入 Session ID / 有效轮数 / 产物 |
| record | 只做记录录入（运行已在 Trae 完成时使用） |

## 执行流程

1. **就绪检查**：确认 `tasks/{task-id}/task.md`（需求 Prompt）与 `verify-rubric.md` 已存在且冻结。
2. **运行（用户在 Trae 中执行）**：
   - 打开新任务窗口，选择 Trae CN + Seed Evolving（SOLO Agent 模式，关闭 Auto）
   - 把 `task.md` 的 Prompt **原文**提交，单 Prompt 运行
   - 运行过程中**不追加人工澄清、任务拆解或引导性提示**
   - 记录 Trae Session ID（对话窗口 ID）与有效轮数（模型主动推进的有效轮次）
3. **记录录入**：将以下内容写入 `run-log.md`：
   - Trae Session ID【必须原文逐字复制，禁止改写】
   - 有效轮数（数字）
   - 运行环境备注（Max 是否开启等，如有）
4. **产物收集**：将模型产物描述与补充材料路径写入 `result.md`：
   - 产物结果：模型交付了什么（功能/代码/配置变更摘要）
   - 产物补充材料：`model.patch`、verifier 测试日志、失败测试列表及轨迹等文件的路径
5. **确认**：输出记录摘要，提示可进入验收复盘。

## 路径规则

```
# 输入
{work_root}/{session}/tasks/{task-id}/task.md

# 输出
{work_root}/{session}/tasks/{task-id}/run-log.md
{work_root}/{session}/tasks/{task-id}/result.md
```

## 交付字段前置填写

运行阶段确定以下交付表字段：

| 交付表字段 | 来源 |
|------|------|
| Seed 模型/版本 | 实际运行模型（默认 `config.toml [run].model`） |
| Trae Session ID | `run-log.md` 原文复制 |
| 有效轮数 | `run-log.md`（数字） |
| 产物结果 | `result.md` 产物描述 |
| 产物补充材料 | `result.md` 材料路径 |

## 注意事项

1. **单 Prompt 纪律**：运行过程不追加人工澄清、任务拆解或引导性提示；如需追加，该轮次仍如实计入有效轮数，但过程不可追溯性会在验收时记录到备注。
2. **Session ID 纪律**：原文复制，禁止改写或推断。
3. 有效轮数统计口径需与 Repo-v1 规范一致：以模型主动推进任务的有效轮次计，不计人为"继续"提示。
