---
name: swe-run-record
description: "SWE 运行记录：把需求 Prompt 提交给 Trae CN + Seed Evolving 单 Prompt 运行，记录 Trae Session ID、有效轮数（= 模型输出步数）与产物。Use when: SWE 运行, 记录 Session ID, 有效轮数。"
---

# SWE 运行记录（Run Record）

> 配置从 `../config.toml` 读取。

出题完成后，由用户把 `task.md` 的需求 Prompt 交给 **Trae CN + Seed Evolving** 运行。本技能负责把运行过程完整、可追溯地记录下来。

## 功能概述

这个技能负责：

- 确认任务目录与需求 Prompt 就绪
- 记录 Trae Session ID（原文复制）与有效轮数（= 模型输出步数 / 有效 TC 次数）
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

1. **就绪检查**：确认 `tasks/{repo}/{branch}/task.md`（需求 Prompt）与 `verify-rubric.md` 已存在且冻结。
2. **分支准备（AI 执行，`run` 命令时）**：
   - 确认 Repo 已 fork 到用户的 GitHub（未 fork 则先提示用户 fork，作为后续 commit 目标）
   - 用户把 fork 主分支 clone 到 `{work_root}/{session}/repos/{repo}/origin/`（clone 由用户执行，沙箱无法访问 GitHub）
   - AI 在 `origin` 创建 3 个分支 `{repo}-01/02/03`，用 `git worktree add` 拉出 `repos/{repo}/{repo}-01/`、`repos/{repo}/{repo}-02/`、`repos/{repo}/{repo}-03/`，各自 checkout 到对应题 `meta.json` 的 `commit`
3. **运行（用户在 Trae 中执行）**：
   - 打开 `repos/{repo}/{branch}/`（{repo}-01/02/03 之一）项目，新建任务窗口，选择 Trae CN + Seed Evolving（SOLO Agent 模式，关闭 Auto）
   - 把 `task.md` 的 Prompt **原文**提交，单 Prompt 运行
   - 运行过程中**不追加人工澄清、任务拆解或引导性提示**
   - 记录 Trae Session ID（对话窗口 ID）与有效轮数（= 模型输出步数，通过下方第 4 步从 Trae 日志读取）
   - **省积分经验**（见 `docs/内部规范.md`）：执行超过 1.5 小时可停止并按「>100 轮且效果差」提交；若模型正在跑测试/执行任务或马上结束，可再等等尽量提交完整数据；不要为省积分故意出难题
4. **获取有效轮数（= 模型输出步数 / 步数）**：跑完**尽快**执行——Trae 日志会动态清除：
   - 复制完整 Trae Session ID
   - 把 `docs/步数统计.txt` 的内容 + Session ID 发给 Codex，让 Codex 只读 Trae 日志统计有效 TC 次数
   - 该数字即「有效轮数」= 模型输出步数 = 有效 TC（工具调用）次数，按 `toolCallId`/`serverCallId` 去重
5. **记录录入**：将以下内容写入 `run-log.md`：
   - Trae Session ID【必须原文逐字复制，禁止改写】
   - 有效轮数（= 模型输出步数，数字）
   - 运行环境备注（Max 是否开启等，如有）
6. **产物收集**：将模型产物描述与补充材料路径写入 `result.md`：
   - 产物结果：模型交付了什么（功能/代码/配置变更摘要）
   - 产物补充材料：`model.patch`、verifier 测试日志、失败测试列表及轨迹等文件的路径
7. **提交 + 记录 commitUrl（导出飞书前）**：模型改完代码后，AI 在对应 `repos/{repo}/{branch}/` 里 commit 并 push 到 fork，得到 commit URL 写入 `run-log.md`（导出飞书时填 `commitUrl` 字段，与 gsb 类似）。**本地代码先不要删除**。
8. **确认**：输出记录摘要，提示可进入验收复盘。

## 路径规则

```
# 输入
{work_root}/{session}/tasks/{repo}/{branch}/task.md

# 输出
{work_root}/{session}/tasks/{repo}/{branch}/run-log.md
{work_root}/{session}/tasks/{repo}/{branch}/result.md
```

## 交付字段前置填写

运行阶段确定以下交付表字段：

| 交付表字段 | 来源 |
|------|------|
| Seed 模型/版本 | 实际运行模型（默认 `config.toml [run].model`） |
| Trae Session ID | `run-log.md` 原文复制 |
| 有效轮数（= 模型输出步数） | `run-log.md`（数字，Codex 读 Trae 日志得到的有效 TC 次数） |
| 产物结果 | `result.md` 产物描述 |
| 产物补充材料 | `result.md` 材料路径 |
| commitUrl | `run-log.md`（fork 后 commit 的 URL；填写规范待同步） |

## 注意事项

1. **单 Prompt 纪律**：运行过程不追加人工澄清、任务拆解或引导性提示；如需追加，该轮次仍如实计入有效轮数，但过程不可追溯性会在验收时记录到备注。
2. **Session ID 纪律**：原文复制，禁止改写或推断。
3. 有效轮数统计口径需与 Repo-v2 规范一致：以模型主动推进任务的有效 TC 次数计（= 模型输出步数），不计人为"继续"提示。
4. **步数及时获取**：Trae 日志动态清除，跑完尽快通过 Codex + Session ID 获取步数并记入 `run-log.md`；有效轮数 = 模型输出步数（口径见 `docs/步数统计.txt`）。
5. **省积分**：超过 1.5 小时可停止；不要为省积分故意出难题。
6. **本地代码先不要删除**：模型跑完后的本地代码（含改动）保留，用于 commit 与后续复核。
7. **commitUrl**：修改前 fork、改完 commit，记录 commit URL。**push 走 HTTPS + PAT**（`secrets.toml` 的 `github_pat` / `github_username`），不用 SSH（AI 沙箱 SSH 会失败）。
