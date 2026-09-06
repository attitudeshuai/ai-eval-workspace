---
name: swe-run-record
description: "SWE 运行记录：把 instruction.md 需求 Prompt 提交给 Trae/TraeX/miniswe + Seed Evolving 单 Prompt 单轮运行，记录 Session ID、有效轮数（有效 TC）与取证。Use when: SWE 运行, 记录 Session ID, effective_turns, 取证。"
---

# SWE 运行记录（Run Record）

> 规范见 `../docs/SWE-like Repo-v3.md`（第 4 节）、`../docs/内部规范-v1.md`。
> 步数口径：有效轮数 = 有效 TC（Hook），见 [02-step-count.md](02-step-count.md)。

## 功能概述

这个技能负责：

- 确认 `instruction.md` / `nl_rubric.yaml` / `Dockerfile` 就绪，repo 已 fork
- 记录 `trae_session_id` 与 `effective_turns`（agent step）
- 取证：trajectory + model.patch + screenshots
- 填 `task.toml` 的运行字段

这个技能不负责：出题（01）、验收（03）、回填底稿（04）。

## 命令

| 命令 | 说明 |
|------|------|
| run | 默认命令。提示用户到 Trae/TraeX/miniswe 执行，执行完成后录入 Session ID / 有效轮数 / 取证 |
| record | 只做记录录入（运行已完成时使用） |

## 执行流程

1. **就绪检查**：`instruction.md` + `tests/nl_rubric.yaml` + `environment/Dockerfile` 已就绪且冻结；目标 Repo 已 fork 并 clone。
2. **运行（用户在 Trae/TraeX/miniswe 执行）**：
   - 把 `instruction.md` 的 Prompt **原文**提交，**单 Prompt 单轮**运行
   - 运行过程中**不追加人工澄清、任务拆解或引导性提示**
   - 记录 `trae_session_id`（miniswe 无，留空）与 `harness`（Trae / TraeX / miniswe）
3. **取证**（每题只交一次运行的取证）：
   - trajectory：TraeX 取 `.trae/cli/sessions/` 下本次会话轨迹 → `evidence/trajectory.jsonl`；Trae IDE 导出会话 → `evidence/trajectory.md`；miniswe 取 `.traj.json` → `evidence/trajectory.json`
   - model.patch：`git diff --binary --cached <base_commit> > evidence/model.patch`（diff 基准必须是 base_commit，不得用 HEAD~1）
   - screenshots：至少 1 张运行结果截图，放 `evidence/screenshots/`
4. **验证 + 截图（AI 执行，用户粘贴对话后触发）**：
   - 在对应 worktree 里**运行验证**：Python 跑 pytest / Go 跑 go test，优先复用会话里模型自跑的命令与环境（如 `PYTHONPATH=src`、`GOPROXY` 指向国内源），确认实现是否成功、回归是否通过
   - 把验证结果**截图**（终端输出渲染成 PNG）保存到 `evidence/screenshots/`，至少 1 张，用于底稿「产物截图」附件与验收证据
   - 验证跑不通时，如实记录失败项，不要伪造通过截图
5. **算有效轮数**：按 [02-step-count.md](02-step-count.md) 的有效 TC 口径得 `effective_turns`。
6. **填 task.toml**：`trae_session_id`、`effective_turns`、`harness`、`seed_model`。
7. **commit 到 fork**：把模型改动做成一个单独 commit（**只含模型修改**）push 到 fork，记录 commit URL（见 `docs/内部规范-v1.md`）。**本地代码先不要删除**。

## 注意事项

1. **单 Prompt 单轮纪律**：不追加人工澄清、任务拆解或引导性提示。
2. **Session ID 纪律**：原文复制，禁止改写或推断。
3. **步数口径**：有效轮数 = 有效 TC（PostToolUse 工具调用，按 tool_use_id 去重、排除轮询/配置/补丁类工具）；TraeCode CN/Trae 用 Hook、TraeX 用 count_steps.py、miniswe 取 api_calls。
4. **取证**：patch 基准必须是 base_commit；screenshots 非空。
5. **省积分**：执行超过 2 小时可停止，按「>100 轮且效果差」提交（见 `docs/内部规范-v1.md`）。
