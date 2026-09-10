---
name: cc-solo-export-submit
description: "cc-solo 生成评价结果：按平台提交表单的字段规范（24 字段，含五维分数与描述、会话轨迹定位），把全部任务/轮次合成「一轮 = 一条」的评价结果 JSON（附人工核对 CSV + 质检报告）。用户只发指令（如 cc-solo export），Python 脚本由 agent 执行。提交接口已就位，但本阶段先不提交。Use when: cc-solo 生成评价结果, 评价结果文件, 质检, 提交接口, 轨迹上传。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取（`[submission]` 段），敏感信息在 `secrets.toml [submission]`（gitignore）。
> 依赖脚本：
> - `scripts/cc-solo/check_form_schema.py` —— **表单规范预检**：GET 平台 form-schema，比对 fingerprint 与字段集合（生成/提交前自动执行）
> - `scripts/cc-solo/extract_submit_fields.py` —— 抽取字段规范（**默认直接拉平台 form-schema 实时接口**；`--source js` 走本地 `submitfrom.js` 快照离线兜底）
> - `scripts/cc-solo/build_eval_result.py` —— 生成评价结果 + 质检
> - `scripts/cc-solo/submit_eval_result.py` —— 上传轨迹 + 提交（默认 dry-run；逐条提交，每条间隔 5s）
> - 旧流程脚本 `export_submit.py`（CSV 提交表）/ `append_delivery_feishu.py`（飞书投递）**已退役**，勿再用。

# cc-solo 生成评价结果 · 提交接口

> **2026-09-10 起：不再导出「正式提交表 CSV」也不投递飞书多维表格**，改为按平台提交表单的字段规范生成评价结果文件，再通过提交接口提交。

## ⛔ 本阶段：只生成、先不提交（用户决定）

- **提交接口已就位**：`POST https://solo2.jzxhnh.com/api/v1/submissions`，已写在 `config.toml [submission].submit_url`（`secrets.toml [submission].submit_url` 若填写则优先），`docs/submission/fields.json` 的 `submit_api.url` 也已同步。
- 但**本阶段先不提交数据**：只做**生成评价结果 JSON + 人工核对 CSV + 质检报告**，**不上传轨迹附件、不调提交接口**。
- 「步骤 4 上传轨迹附件 + 提交」与「步骤 5 交付核对」暂时**不执行**；需要提交时用户说一声，由 agent 执行。

## 分工：你只发指令，脚本由 agent 跑

- 你**只发自然语言指令**（如 `cc-solo export`），**不需要自己运行任何 Python 命令**。
- 下文中出现的所有 `python scripts/cc-solo/…` 都是 **agent 在宿主机执行的内部步骤**，列出来只为说明 agent 会做什么。

## 功能概述

按 `projects/cc-solo/docs/submission/fields.json`（从 `docs/submission/submitfrom.js` 抽取的表单字段规范）把
`{RECORD_DIR}/` 下每个任务的共享字段（`task-info.md`）与每轮数据（`{任务}-R{NN}.md`）合成**一轮 = 一条**的评价结果：

| 产物 | 用途 |
|---|---|
| `deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json` | **主产物**：提交接口的载荷来源（24 字段 / 条 + 轨迹附件路径） |
| `…-{date}.csv` | 人工核对（中文表头，字段顺序与表单一致） |
| `…-{date}-质检报告.md` | 逐条 error / warn 明细 |

## 指令 ↔ agent 动作对照

**你只发左边这列指令**，脚本由 agent 执行：

| 你发的指令 | agent 执行 | 说明 |
|------|------|------|
| `cc-solo export` | `python scripts/cc-solo/build_eval_result.py` | 扫描全部任务 → 评价结果 JSON + CSV + 质检报告（**内部第一步会自动先请求表单定义接口**） |
| `cc-solo export <任务名>` | `python scripts/cc-solo/build_eval_result.py --task <任务名>` | 只生成指定任务 |
| `cc-solo export fields` | `python scripts/cc-solo/extract_submit_fields.py` | 抽取/更新字段规范（**默认拉平台实时接口**；`--source js` 走本地快照离线兜底） |
| `cc-solo export submit` | `python scripts/cc-solo/submit_eval_result.py …` | ⛔ **本阶段先不执行**（接口已就位，等用户确认后再提交） |

> 以下命令**仅供 agent 查阅与执行，你不需要手敲**（`--session` 缺省取 `config.toml [sessions].active`）：

```bash
# 1) 生成评价结果（只读记录、只写 deliverables，不改数据）
python scripts/cc-solo/build_eval_result.py
python scripts/cc-solo/build_eval_result.py --session session-0909 --task h5-demo-feature-01

# 2) 表单字段有变化时：重新抽取规范
python scripts/cc-solo/extract_submit_fields.py

# —— 以下命令本阶段先不执行（提交接口已就位，等用户确认后再提交）——
# 先看提交计划（不发请求）
python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/session-0909/评价结果-session-0909-2026-09-10.json
# 只上传轨迹并回填附件信息（验凭据与上传链路，不提交）
python scripts/cc-solo/submit_eval_result.py --result <json> --upload-only --commit --write-back
# 正式提交
python scripts/cc-solo/submit_eval_result.py --result <json> --commit --write-back
python scripts/cc-solo/submit_eval_result.py --result <json> --record h5-demo-feature-01#R02 --commit
python scripts/cc-solo/submit_eval_result.py --result <json> --show-payload
```

## 执行流程

### 步骤 0：先请求平台表单定义接口（每次都要，防止表单变了）

```
GET https://solo2.jzxhnh.com/api/v1/submissions/form-schema
```

- 目的：拿平台**当前**的字段规范，与本地 `docs/submission/fields.json` 比对（fingerprint + 字段集合 + 各字段选项/必填）。
- 实现：`scripts/cc-solo/check_form_schema.py`。退出码：`0` 一致 / `3` 不一致 / `4` 取不到。
- 平台返回结构：`{fingerprint, groups, fields[24], teams, attachment_max_mb}`（与 `submitfrom.js` 里那份 `submitFields` 同形）。
- ⚠️ **该接口对请求头敏感**：只带 Cookie 会 **401**，必须配齐浏览器那套头（`Referer`、`Accept`、`Accept-Language`、`Cache-Control/Pragma`、`Sec-Ch-Ua*`、`Sec-Fetch-*`、浏览器 UA）。已内置在 `submit_eval_result.py` 的 `browser_headers()`，`check_form_schema.py` 直接复用。
- **自动执行，不用单独发指令**：
  - `build_eval_result.py` 第一步就会请求；不一致只在日志与质检报告里告警；
  - `submit_eval_result.py --commit` 提交前也会请求；**不一致直接中止（退出码 3），一条请求都不发**。
- 不一致时的处理：重跑 `python scripts/cc-solo/extract_submit_fields.py`（**默认就拉这个实时接口**，fingerprint 随平台更新；如需离线可用 `--source js` 走本地快照），再重新生成评价结果。
- 取不到（如 cookie 过期）时：脚本会提示「凭据可能已过期」，从浏览器重新复制整条 cookie 填进 `secrets.toml [submission].cookie`。

### 步骤 1：确认字段规范与范围

- 字段规范：`docs/submission/fields.json`（fingerprint 由平台接口给出；**每次生成前都会先请求 `form-schema` 校验，见步骤 0**；不一致时重跑 `extract_submit_fields.py`，它默认就从该接口实时拉取）。
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

② **项目规则层**：首轮难度 ≠「简单」；`x_iteration` 与轮次一致；同任务 `SessionID` 一致、`TurnID` 不重复；轮次 ≤ 10；轨迹文件存在（附件 ≤ 20 MB）；分数与描述方向一致（高分不得写「未完成」，低分须有负面证据）。

③ **去 AI 化层（红线）**：**提交 body 里的所有字段在提交前须已过 `skills/humanizer-zh` 完整流程（28 条规则全查）**，不只是五维描述。
   - 机械兜底（脚本）：**符号类 → error 阻塞提交**（`——`、反引号、`「」`、箭头 `→ ⇒ => ->`、英文直引号）；**AI 套话词 → error 阻塞提交**（`落地`、`模型`、`赋能`、`助力`、`闭环`、`链路`、`复用`、`对齐`、`颗粒度`、`层面`、`体现` 等）；**长英文串 → ≥16 字符 error 阻塞提交、12–15 字符 warn**（平台的 B-5「公共长片段」查重按连续字符比对，实测 `--break-system-packages` 被判套模板打回）；**AI 高频词 → warn**。完整口径见 `docs/annotate-guide.md` §9。
   - 扫描范围（脚本）：AI 起草的**五个 `desc_*`** 记 error 档；**`other_issues`（选填，提交时置空）、`user_prompt`（可能是人工原文，按「人工原文不改写」保持原样）、`languages`** 只提示不阻塞。
   - ⚠️ 脚本只是机械兜底，**替代不了 humanizer-zh**（要 LLM 判断）；「实际调用并执行该 skill」由 agent 在提交前完成。

> error 会阻塞该条（`ready=false`）；warn 只提示，需人工复核后决定。

### 步骤 4：上传轨迹附件 + 提交（submit）—— ⛔ 本阶段先不执行

> 本节先留着，等用户确认要提交时再执行。

- 轨迹是**附件**字段，不能直接写文本路径：先 `POST {upload_url}`（`multipart/form-data`，表单字段 `file`）拿返回的 `path`，再把该 `path` 写进 `trace_file` 提交。
- 认证：`secrets.toml [submission].cookie`（浏览器里复制的整条 cookie，含 `solo_qa_session` / `solo_qa_csrf`）；若接口要求 `X-CSRF-Token`，填 `csrf_header`。
- **cookie 会过期**：401/403 时重新复制 cookie。
- **提交接口（已确认）**：`POST https://solo2.jzxhnh.com/api/v1/submissions`（写在 `config.toml [submission].submit_url`；`secrets.toml [submission].submit_url` 优先，`--url` 可临时覆盖）。
- **请求体**：`{"data": {24 个字段}, "schema_fingerprint": "<fields.json 的 fingerprint>"}`；其中 `trace_file` 是**附件数组** `[{"name": "…-trajectory.jsonl", "path": "uploads/<id>.jsonl", "size": 321940}]`，由上传步骤回填。
- **响应**：`{"id":1196,"status":"SUBMITTED","status_label":"已提交","round_no":1,"schema_stale":false,"message":"…"}`；脚本按 `status==SUBMITTED` 或有 `id` 判成功，`schema_stale=true` 会告警（表单字段变了，需重跑 `extract_submit_fields.py` 并重新生成）。
- 字段顺序与取值见产物里的 `field_order` / `fields`；要调整请求体形状改 `submit_eval_result.py` 的 `build_payload()`。

### 步骤 5：交付核对 —— ⛔ 本阶段先不执行

- 先 `--upload-only --commit --write-back` 验证 cookie / 上传链路，再正式提交。
- 提交后核对返回：`id`（记录号）、`status`（应为 `SUBMITTED`）、`round_no`（= `x_iteration`）、`schema_stale`（应为 `false`）、`message`；脚本已把这些打进日志，加 `--write-back` 会写回结果 JSON 的 `submit_response`。失败条目修正后重试，避免重复提交（同一 `SessionID + TurnID` 为同一条数据）。
- 时限沿用约定：当天 20:00 前产生的数据当天提交，20:00 之后的次日 14:00 前提交。

## 注意事项

1. 机械校验只保证**格式层**；描述是否到位、是否真看过轨迹仍须人工复核。
2. **交付物无 AI 痕迹（红线）**：**提交 body 的所有字段**须已在 score 阶段去 AI 化。导出阶段的机械兜底只做符号类 error 与高频词类 warn，**不代改**；命中 error 的条目必须先回 `records/` 重新去 AI 化，再重新生成。
3. **选填字段一律置空字符串**：提交 body 仍保持 24 字段的完整结构，但**所有选填字段（`is_required=false`）的值提交为空串**——本规范里只有 `other_issues`（其他问题）。内容仍留在 `records/` 与质检报告里备查，但**不提交内容**。
4. **不提交到 API 的内部字段**：`备注（内部）`、`截图附件（内部）`、质检报告里的「去 AI 化字段清单」——这些只在 `records/` 与质检报告里留档，**不进提交 body**。
3. 数据不允许返修：提交前完成自查；被抽检不合格的整批可能被拒收。
4. `build_eval_result.py` 只读记录、只写 deliverables；`submit_eval_result.py` 不加 `--commit` 不发任何请求。**本阶段先不执行 `submit_eval_result.py`**（用户决定先不提交）。
5. 中文文件一律 UTF-8（CSV 用 UTF-8 BOM，便于 Excel 打开）。
6. 附件上限 20 MB（表单定义 `attachment_max_mb`）；整份轨迹通常远小于此（单题量级几百 KB），若超限先排查是否误传了整目录或依赖包。
7. 旧产物口径（`正式提交表-*.csv`、飞书表 `Lg0mbjRpPaxjhmsj27MckrJLnec/tble0z2KnzCfjJmZ`）仅作历史留存，不再使用。
