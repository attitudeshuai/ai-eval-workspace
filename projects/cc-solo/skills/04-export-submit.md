---
name: cc-solo-export-submit
description: "cc-solo 生成评价结果并提交：按平台提交表单的字段规范（24 字段，含五维分数与描述、会话轨迹定位），把全部任务/轮次合成「一轮 = 一条」的评价结果 JSON（附人工核对 CSV + 质检报告），再（URL 待补）上传轨迹附件并调用提交接口。Use when: cc-solo 生成评价结果, 评价结果文件, 质检, 提交接口, 轨迹上传。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取（`[submission]` 段），敏感信息在 `secrets.toml [submission]`（gitignore）。
> 依赖脚本：
> - `scripts/cc-solo/extract_submit_fields.py` —— 从表单定义抽取字段规范
> - `scripts/cc-solo/build_eval_result.py` —— 生成评价结果 + 质检
> - `scripts/cc-solo/submit_eval_result.py` —— 上传轨迹 + 提交（默认 dry-run）
> - 旧流程脚本 `export_submit.py`（CSV 提交表）/ `append_delivery_feishu.py`（飞书投递）**已退役**，勿再用。

# cc-solo 生成评价结果 · 提交接口

> **2026-09-10 起：不再导出「正式提交表 CSV」也不投递飞书多维表格**，改为按平台提交表单的字段规范生成评价结果文件，再通过提交接口（URL 待管理员提供）提交。

## 功能概述

按 `projects/cc-solo/docs/submission/fields.json`（从 `docs/submission/submitfrom.js` 抽取的表单字段规范）把
`{RECORD_DIR}/` 下每个任务的共享字段（`task-info.md`）与每轮数据（`{任务}-R{NN}.md`）合成**一轮 = 一条**的评价结果：

| 产物 | 用途 |
|---|---|
| `deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json` | **主产物**：提交接口的载荷来源（24 字段 / 条 + 轨迹附件路径） |
| `…-{date}.csv` | 人工核对（中文表头，字段顺序与表单一致） |
| `…-{date}-质检报告.md` | 逐条 error / warn 明细 |

## 命令

| 命令 | 说明 |
|------|------|
| build | 默认。扫描全部任务 → 评价结果 JSON + CSV + 质检报告 |
| build `<TASK_ID>` | 只生成指定任务（`--task`） |
| submit | 提交：先上传轨迹附件拿远端 path，再调提交接口（**默认 dry-run**，加 `--commit` 才发请求） |
| fields | 重新抽取表单字段规范（表单改动后重跑） |

```bash
# 0) 表单字段有变化时：重新抽取规范
python scripts/cc-solo/extract_submit_fields.py

# 1) 生成评价结果（只读记录，不改数据）
python scripts/cc-solo/build_eval_result.py
python scripts/cc-solo/build_eval_result.py --session session-0909 --task h5-demo-feature-01

# 2) 先看提交计划（不发请求）
python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/session-0909/评价结果-session-0909-2026-09-10.json

# 3) 只上传轨迹并回填远端 path（提交 URL 未到位时也能先做）
python scripts/cc-solo/submit_eval_result.py --result <json> --upload-only --commit --write-back

# 4) 正式提交（URL 到位后）
python scripts/cc-solo/submit_eval_result.py --result <json> --commit            # 用 secrets.toml [submission].submit_url
python scripts/cc-solo/submit_eval_result.py --result <json> --url https://... --commit
```

## 执行流程

### 步骤 1：确认字段规范与范围

- 字段规范：`docs/submission/fields.json`（fingerprint 与 `submitfrom.js` 对应；表单更新后重跑 `extract_submit_fields.py`）。
- 范围：全部任务 / 指定任务 / 指定 record_key（`--record`）/ 只提交 `ready=true` 的（`--only-ready`）。
- 输出目录：`deliverables/cc-solo/{SESSION_NAME}/`。

### 步骤 2：生成评价结果（build）

取值来源固定，不要手改产物（要改就改 records，再重新生成）：

| 字段 | 中文名 | 类型 | 取值来源 |
|---|---|---|---|
| `question_type` | 任务类型 | select(7) | `{任务}-R{NN}.md` → `## 任务类型` |
| `difficulty` | 任务难度 | select(4) | `## 任务难度` |
| `languages` | 语言/框架 | text | `## 语言/框架` |
| `harness` / `harness_version` | Harness / 版本 | select / text | `task-info.md` |
| `os_platform` | 操作系统 | select | `task-info.md` |
| `repro_level` | 环境可复现等级 | select | `task-info.md` |
| `env_snapshot` | 初始环境快照 | url | `task-info.md`（**须 GitHub 40 位 SHA permalink**） |
| `user_prompt` | User Prompt | textarea | `## User Prompt`（原文，不改写） |
| `session_id` / `turn_id` | SessionID / TurnID | text | `task-info.md` / `## TurnID/PromptID` |
| `trace_file` | 轨迹文件 | **attachment** | **整份轨迹** `{任务}-trajectory.jsonl`（= 容器 `/home/node/.claude/projects/-workspace/<SessionID>.jsonl` 导出的原始会话文件；平台 `help_text` 明确指向 `~/.codex/sessions/` 或 `~/.claude/projects/`，配 SessionID + TurnID 定位到某一轮）。整份缺失时才回退本轮切片 `{任务}-R{NN}-trajectory.jsonl`（切片仅用于打分阶段定位单轮）→ 提交前需上传换远端 path |
| `score_delivery/instruction/planning/reasoning/execution` | 五维分数 | number 1-5 | `## 交付完整性` 等 |
| `desc_*` | 五维描述 | textarea | `## 交付完整性-描述` 等 |
| `other_issues` | 其他问题 | textarea（选填） | `## 其他问题` |
| `x_iteration` | 当前对话轮次排序 | number | 轮次序号（R01 → 1） |

> ⚠️ **多轮任务的轨迹附件口径（重要）**：同一任务（同一 `SessionID`）的各轮记录，`trace_file` **都指向同一份「最终完整轨迹」** `{任务}-trajectory.jsonl`（含该会话全部轮次），各轮靠 `SessionID` + `turn_id` 定位。
> 因此**导出与提交必须在该任务会话结束之后执行**——否则整份轨迹只含到当时为止的轮次，后面几轮的记录就会挂着一份不完整的轨迹。
> 每轮的 `{任务}-R{NN}-trajectory.jsonl` 切片只是打分阶段定位单轮用的中间产物，**不作提交附件**。

### 步骤 3：质检（脚本内嵌，两层）

① **表单规范层**（`fields.json` 驱动）：必填非空、select 取值在 options 内、number 为 1-5 整数、text/textarea 长度上限、`env_snapshot` 匹配 `^https://github\.com/…/commit/[0-9a-f]{40}/?$`。

② **项目规则层**：首轮难度 ≠「简单」；`x_iteration` 与轮次一致；同任务 `SessionID` 一致、`TurnID` 不重复；轮次 ≤ 10；轨迹文件存在（附件 ≤ 20 MB）；分数与描述方向一致（高分不得写「未完成」，低分须有负面证据）；描述过短/疑似 AI 痕迹（`——`、综上所述等）→ warn。

> error 会阻塞该条（`ready=false`）；warn 只提示，需人工复核后决定。

### 步骤 4：上传轨迹附件 + 提交（submit）

- 轨迹是**附件**字段，不能直接写文本路径：先 `POST {upload_url}`（`multipart/form-data`，表单字段 `file`）拿返回的 `path`，再把该 `path` 写进 `trace_file` 提交。
- 认证：`secrets.toml [submission].cookie`（浏览器里复制的整条 cookie，含 `solo_qa_session` / `solo_qa_csrf`）；若接口要求 `X-CSRF-Token`，填 `csrf_header`。
- **cookie 会过期**：401/403 时重新复制 cookie。
- **提交接口 URL 待管理员提供**，写进 `secrets.toml [submission].submit_url`（或 `--url` 传入）；未配置时脚本只上传轨迹并给出提示。
- 请求体：一条记录一个 JSON 对象，字段名 = `field_key`（24 个），顺序见产物里的 `field_order`。**接口格式拿到后如需调整，改 `submit_eval_result.py` 的 `build_payload`。**

### 步骤 5：交付核对

- 先 `--upload-only --commit --write-back` 验证 cookie / 上传链路，再正式提交。
- 提交后核对接口返回（`record_id` / 错误码）；失败条目修正后重试，避免重复提交（同一 `SessionID + TurnID` 为同一条数据）。
- 时限沿用约定：当天 20:00 前产生的数据当天提交，20:00 之后的次日 14:00 前提交。

## 注意事项

1. 机械校验只保证**格式层**；描述是否到位、是否真看过轨迹仍须人工复核。
2. **交付物无 AI 痕迹**：AI 起草的提示词/打分依据须已在 score 阶段去 AI 化；导出阶段发现疑似痕迹只提示，不代改。
3. 数据不允许返修：提交前完成自查；被抽检不合格的整批可能被拒收。
4. `build_eval_result.py` 只读记录、只写 deliverables；`submit_eval_result.py` 不加 `--commit` 不发任何请求。
5. 中文文件一律 UTF-8（CSV 用 UTF-8 BOM，便于 Excel 打开）。
6. 附件上限 20 MB（表单定义 `attachment_max_mb`）；整份轨迹通常远小于此（单题量级几百 KB），若超限先排查是否误传了整目录或依赖包。
7. 旧产物口径（`正式提交表-*.csv`、飞书表 `Lg0mbjRpPaxjhmsj27MckrJLnec/tble0z2KnzCfjJmZ`）仅作历史留存，不再使用。
