---
name: cc-solo-export-submit
description: "cc-solo 生成评价结果：按平台提交表单的字段规范（24 字段，含五维分数与描述、会话轨迹定位），把全部任务/轮次合成「一轮 = 一条」的评价结果 JSON（附质检报告；不再产出人工核对 CSV）。用户只发指令（如 cc-solo export），Python 脚本由 agent 执行。提交接口已就位，但本阶段先不提交。Use when: cc-solo 生成评价结果, 评价结果文件, 质检, 提交接口, 轨迹上传。"
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

## 状态：生成 + 提交 + 返修（均已启用）

- **提交接口**：`POST https://solo2.jzxhnh.com/api/v1/submissions`，已写在 `config.toml [submission].submit_url`（`secrets.toml [submission].submit_url` 若填写则优先），`docs/submission/fields.json` 的 `submit_api.url` 也已同步。**2026-09-12 起已实际提交**（app-001-codegen-03~10 共 10 条，全部 `QC_PASSED`）。
- **详情接口**：`GET {提交接口}/{id}` —— 查一条提交的状态与打回原因（返修用）。
- **更新接口**：`PUT {提交接口}/{id}` —— 整改后升版本更新（返修用；body 与提交同形，另带 `comment`）。
- 生成、提交、核对、返修四段都由 agent 执行，用户只发下面那几行指令。

## 分工：你只发指令，脚本由 agent 跑

- 你**只发自然语言指令**（如 `cc-solo export`），**不需要自己运行任何 Python 命令**。
- 下文中出现的所有 `python scripts/cc-solo/…` 都是 **agent 在宿主机执行的内部步骤**，列出来只为说明 agent 会做什么。

## 功能概述

按 `projects/cc-solo/docs/submission/fields.json`（从 `docs/submission/submitfrom.js` 抽取的表单字段规范）把
`{RECORD_DIR}/` 下每个任务的共享字段（`task-info.md`）与每轮数据（`{任务}-R{NN}.md`）合成**一轮 = 一条**的评价结果：

| 产物 | 用途 |
|---|---|
| `deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json` | **主产物**：提交接口的载荷来源（24 字段 / 条 + 轨迹附件路径） |
| `…-{date}-质检报告.md` | 逐条 error / warn 明细 |

## 指令 ↔ agent 动作对照

**你只发左边这列指令**，脚本由 agent 执行：

| 你发的指令 | agent 执行 | 说明 |
|------|------|------|
| `cc-solo export` | `python scripts/cc-solo/build_eval_result.py` | 扫描全部任务 → 评价结果 JSON + 质检报告（**内部第一步会自动先请求表单定义接口**）。扫描时按 `config.toml [exclude].projects` **跳过样例项目**（`h5-demo` 只作样例，不导出不提交），并在输出里打印跳过了哪几条 |
| `cc-solo export <任务名>` | `python scripts/cc-solo/build_eval_result.py --task <任务名>` | 只生成指定任务 |
| `cc-solo export fields` | `python scripts/cc-solo/extract_submit_fields.py` | 抽取/更新字段规范（**默认拉平台实时接口**；`--source js` 走本地快照离线兜底） |
| `cc-solo export submit` | `python scripts/cc-solo/submit_eval_result.py …` | 上传轨迹附件 + 提交（先 dry-run，再 `--upload-only --commit --write-back`，最后 `--commit`） |
| `cc-solo 返修` | `python scripts/cc-solo/list_pending_fix.py --detail --scope auto` → 归类打回原因 → 整改 `records/` → `--update-id <ID> --commit --write-back` | **不带 ID**：先拉提交列表筛出**待返修**（`PENDING_FIX`），**排除 `config.toml [submission].fix_exclude_ids` 里的 ID**，**只留本机那一侧**（`win`／`mac`，默认按当前系统），归类原因后逐条整改更新，最后把新规则写回文档（步骤 6） |
| `cc-solo 返修 win` / `cc-solo 返修 mac` | 同上，`--scope win`／`--scope mac` | 直接点名机器范围：`win` = `cc-*`，`mac` = `app-*`；选中另一台机器那侧时只列清单并警告「只能看不要改」 |
| `cc-solo 返修 <提交ID>` | 同上（跳过发现步骤，直接整改这几条） | 已知 ID 时用这条；多个 ID 用空格或逗号分隔，ID 优先于范围参数 |

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

# 3.5) 只刷新 cookie（登录一次并写回 secrets.toml；cookie 约 2 天过期，平时不用手动跑）
python scripts/cc-solo/submit_eval_result.py --login-only --commit

# 3.6) 看 cookie 状态（来源 / 到期时间 / 剩余多久，不发请求）
python scripts/cc-solo/submit_eval_result.py --status
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
- 取不到（如 cookie 过期）时：**不需要手工复制** —— 脚本会用 `secrets.toml [submission].username / password` 自动登录刷新（见步骤 4）。

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
   - 机械兜底（脚本）：**符号类 → error 阻塞提交**（`——`、反引号、`「」`、箭头 `→ ⇒ => ->`、英文直引号）；**AI 套话词 → error 阻塞提交**（`落地`、`模型`、`赋能`、`助力`、`闭环`、`链路`、`复用`、`对齐`、`颗粒度`、`层面`、`体现` 等）；**长英文串的检查已于 2026-09-13 撤掉**（英文标识不再判红线）；**长英文串 → ≥16 字符 error 阻塞提交、12–15 字符 warn**（平台的 B-5「公共长片段」查重按连续字符比对，实测 `--break-system-packages` 被判套模板打回）；**AI 高频词 → warn**。完整口径见 `docs/annotate-guide.md` §9。
   - 扫描范围（脚本）：AI 起草的**五个 `desc_*`** 记 error 档；**`other_issues`（选填，提交时置空）、`user_prompt`（可能是人工原文，按「人工原文不改写」保持原样）、`languages`** 只提示不阻塞。
   - ⚠️ 脚本只是机械兜底，**替代不了 humanizer-zh**（要 LLM 判断）；「实际调用并执行该 skill」由 agent 在提交前完成。

> error 会阻塞该条（`ready=false`）；warn 只提示，需人工复核后决定。

④ **描述风险自查（提示级，2026-09-13 新增脚本）**：`check_round_files.py` 只查得到硬红线，平台 LLM 质检打回的另一类写法（次数无对象、空指代、环境原因挂扣分、主观形容词）要靠这个脚本兜：

```bash
python scripts/cc-solo/scan_desc_risks.py --project cc-002                 # 全部任务
python scripts/cc-solo/scan_desc_risks.py --project cc-002 --task cc-002-feature
python scripts/cc-solo/scan_desc_risks.py --project cc-002 --json out.json  # 机器可读
```

- 四条规则：**R1 次数统计无对象**、**R2 空指代**、**R3 环境原因挂扣分（只看「执行能力」）**、**R4 主观形容词**；命中只是提示，**需人工判断**（脚本已排除「没有 / 都正常 / 第 N 次」这类已定位或全通过的表述，仍有少量误报）。
- 命中的地方**不必逐条改**：逐条对照 `docs/annotate-guide.md` §9 判断该条是否真的缺位置或后果；缺就按 §9 改写，不缺就别动（避免为过自查把已经过关的描述改坏）。

### 步骤 4：上传轨迹附件 + 提交（submit）

> 指令：`cc-solo export submit`。先 dry-run 看计划，再上传轨迹验证链路，最后正式提交。

- 轨迹是**附件**字段，不能直接写文本路径：先 `POST {upload_url}`（`multipart/form-data`，表单字段 `file`）拿返回的 `path`，再把该 `path` 写进 `trace_file` 提交。
- 认证：`secrets.toml [submission].cookie`（含 `solo_qa_session` / `solo_qa_csrf`）。`csrf_header` 留空时自动取 cookie 里的 `solo_qa_csrf`，且 `X-CSRF-Token` / `X-CSRFToken` 两个头名都发。
- **cookie 会过期（服务端约 2 天）——脚本自动续，不用手工复制**：`secrets.toml [submission]` 里配好 `username` / `password`（`login_url` 默认 `https://solo2.jzxhnh.com/api/v1/auth/login`，非敏感项在 `config.toml [submission]`）。脚本在**没有 cookie、或请求返回 401/403** 时会自动登录一次、拿到新的 `solo_qa_session` / `solo_qa_csrf` 后**重试原请求**，并把新 cookie **就地回写 secrets.toml**；`--refresh-cookie` 可在处理前强制刷新，`--login-only --commit` 只刷新 cookie 不提交，`--no-auto-login` 可关掉自动登录；登录成功后，cookie **连同到期时间**存进 `projects/cc-solo/.solo_session.json`（已 gitignore）；**之后每次运行优先复用缓存，没过期就不会再登录**，只有「缓存缺失 / 已过期 / 请求 401、403」时才重新登录一次。`--status` 随时看来源与剩余有效期，`--no-cache` 可只用 secrets.toml。
- **提交接口（已确认）**：`POST https://solo2.jzxhnh.com/api/v1/submissions`（写在 `config.toml [submission].submit_url`；`secrets.toml [submission].submit_url` 优先，`--url` 可临时覆盖）。
- **请求体**：`{"data": {24 个字段}, "schema_fingerprint": "<fields.json 的 fingerprint>"}`；其中 `trace_file` 是**附件数组** `[{"name": "…-trajectory.jsonl", "path": "uploads/<id>.jsonl", "size": 321940}]`，由上传步骤回填。
- **响应**：`{"id":1196,"status":"SUBMITTED","status_label":"已提交","round_no":1,"schema_stale":false,"message":"…"}`；脚本按 `status==SUBMITTED` 或有 `id` 判成功，`schema_stale=true` 会告警（表单字段变了，需重跑 `extract_submit_fields.py` 并重新生成）。
- 字段顺序与取值见产物里的 `field_order` / `fields`；要调整请求体形状改 `submit_eval_result.py` 的 `build_payload()`。

### 步骤 5：交付核对

- 先 `--upload-only --commit --write-back` 验证 cookie / 上传链路，再正式提交。
- 提交后核对返回：`id`（记录号）、`status`（应为 `SUBMITTED`）、`round_no`（= `x_iteration`）、`schema_stale`（应为 `false`）、`message`；脚本已把这些打进日志，加 `--write-back` 会写回结果 JSON 的 `submit_response`。
- **不要对已提交的同一条再 POST**：平台按 `SessionID + TurnID` 判重，重复提交返回 `422 该 SessionID 下已存在 … 的数据`；要改内容走下面的返修（PUT）。
- 时限沿用约定：当天 20:00 前产生的数据当天提交，20:00 之后的次日 14:00 前提交。

### 步骤 6：返修（提交被打回后整改并更新）

> 指令：`cc-solo 返修`（**不带 ID**：先自己拉列表发现待返修）或 `cc-solo 返修 <提交ID>`（已知 ID，多个用空格或逗号）。平台质检结论为 **待返修**（`PENDING_FIX`）时才会用到。

**链路**：发现（列表）→ 归类打回原因 → 查详情 → 整改 `records/` 描述 → 过门禁 → 重新生成评价结果 → PUT 更新升版本 → **复盘：把新出现的规则写回本文档与 `docs/annotate-guide.md`**。

**6.0 发现 + 归类**（`cc-solo 返修` 不带 ID 时的第一步）

```bash
python scripts/cc-solo/list_pending_fix.py --detail                      # 清单 + 逐条打回原因
python scripts/cc-solo/list_pending_fix.py --detail --json <out.json>    # 机器可读清单（返修流水线用）
```

- 列表接口：`GET {提交接口}?page=1&page_size=20&stage=&keyword=&date_from=&date_to=&user_id=0`，返回 `items[]` 与 `meta{page,page_size,total,total_pages}`；脚本自动翻页，只看 `status == PENDING_FIX`。
- **只返修本机这一侧（红线）**：同一批提交来自**两台机器**，靠仓库前缀区分归属——**Windows 机 = `cc-solo-cc-*`（素材源 cc-001/cc-002…），Mac 机 = `cc-solo-app-*`（素材源 app-001…）**。另一侧的 `records/` 与轨迹根本不在本机，改了也没法按轨迹取证，因此**不属于本机前缀的条目一律不碰**。
  - **指令参数**：`cc-solo 返修 win` / `cc-solo 返修 mac` 直接点名机器；不写参数＝按当前系统（`auto`）。
  - **脚本参数**：`list_pending_fix.py --scope auto|win|mac|all|<前缀>`（`auto` 为默认，按当前系统只列本机那侧；`all` 只用于盘点）。表头打印「机器范围」与「另有 N 条属另一台机器，本机不动」；看了另一台机器那侧会额外警告「只能看，不要改」。
  - 前缀表在 `config.toml [submission].machine_scope`（`Windows = "cc-"`、`Darwin/Linux = "app-"`）。判定某条归谁看详情的 `repo_id` + `os_platform`。
- **排除名单（红线）**：`config.toml [submission].fix_exclude_ids`（当前 `4142, 4143, 4144`）里的提交**一律不整改、不更新**——这几条规则的最终判定还没定，动了会与别人正在对齐的口径冲突。脚本会把它们从待处理清单里剔除并打印「另排除 N 条」；临时覆盖用 `--exclude id1,id2`。
- **先归类再动手**：把失败项按「维度 · 规则」统计（`--detail` 的输出就是这个结构），先看清本批是**哪几条规则**在打回、各占多少条，再决定改法。同类规则要**批量改**，不要逐条凭感觉改字。
- **待处理条数是滚动的**：刚推送的返修条目会先后回到「待质检 → 通过 / 再次打回」，所以清单会随平台复检持续变化（实测 4 条刚清完，下一轮拉取就涨到 18 条）。**每轮开工前重新拉一次**，别拿上一轮的清单收工。

**6.1 查详情**（只读，`list_pending_fix.py --detail` 已包含；也可单条查）：
   ```bash
   python scripts/cc-solo/submit_eval_result.py --detail-id 3347
   ```
   打印并落盘：`status` / `status_label`、`current_version`、`editable`、`qc_hit_rule_label`（命中规则）、`qc_summary`（打回原因）、`dedup_hits[]`（命中字段、相似度、对比来源 peer、历史侧与本次侧摘要）、`locked_fields`；原始详情存 `deliverables/cc-solo/{SESSION}/submission-{ID}-detail.json`。
   **`list_pending_fix.py --detail` 直接把每条拆成「缺失要素 + 原文依据 + 修改建议」三行**（例：`· [执行能力] 把环境或界面问题当评价依据` / `原文依据：「有一次是环境里没装数据库访问依赖」` / `修改建议：扣分只保留模型自身造成的失败调用…`）——整改时**逐条对着这三行改**，不要只看 `qc_summary` 那段总述；平台给的建议句可以直接当改写目标，但**不要照抄它的示例句原文**（会把它的措辞带进评价结果）。
   - 注意：`--detail` 输出较长，用 PowerShell 管道接 `Select-Object -First N` 会提前掐断管道并让进程以非零码退出，那不是脚本故障；要看全就整段输出或落盘后再看。
   - 推送完不等于过关：平台重新质检后**同一条可能带着新打回原因再次退回**（实测 v2 整改推送后又有 2 条以新原因回到 `PENDING_FIX`，版本号升到 v3）。所以每次返修都要**重新拉一遍待处理清单**，别按旧清单收工。

**6.2 整改（agent 做，改的是 `records/`，不是平台字、也不是产物 JSON）**：

   - **B-7 分段复读 / B 长片段**：**针对本轮实际轨迹重写该字段** —— 换掉与历史池重合的句式（如「在思考里先拆几步再动手…没给到 N 分是因为只有思考里的分步」这类通用句式），写进本轮独有的证据（读了哪些文件、依赖顺序、中途换过什么方案、哪一处没核实）；依据一件不减、不添新说法。
   - **A 表套话词 / 符号**：按 `docs/annotate-guide.md` §9 改写；定位信息可以带文件名与方法名（2026-09-13 起英文不再受限）。
   - **跨轮次 / 前后对比**：去掉「上一轮／原来／原先／本来／此前」，改成直接陈述现象与现状。
   - **非满分描述三要素（2026-09-12 实测打回，一批 22 条里 55 处栽在下面前四条）**：
     1. 任何 **< 5 分**的维度，描述必须同时写清 ①**具体位置**（第几步 / 哪次工具调用 / 哪个页面或接口 / 哪个文件或函数 / 哪条命令或报错原文）②**该维度的负面判断**（这一维到底哪里不足）③**具体行为与客观后果**（返工、遗漏、用户看到什么、多花了哪些步骤、功能不可用）。只写「没有做／不够远／有问题」这类结论，必被打回。
     2. **禁主观形容词**：不写「不可追踪」「轻微反复」「明显的猜测式推理」这类评价词，换成客观事实（几次调用、哪几步、哪个页面、哪条命令、具体少了哪一项）。
     3. **必须成完整句**：每个分句都有主谓，不能名词短语堆砌（「十六次改动只读过一次文件，其余依赖对文件的印象」这种电报式短语被打回）。
     4. **4 分档也要写扣分点**：整段只肯定、一句不足都没有，会被判「打分与描述极端背离」。
     定位信息可以写中文业务语义，也可以点名具体文件、函数、命令——平台自 2026-09-13 起不再把英文技术标识判为红线，LLM 质检反而要求位置具体。
    - **第二轮打回实测（2026-09-13，一批 29 条里 7 条二轮被打回，全部栽在「位置不够具体 + 没有后果」）**：
      5. **次数统计 ≠ 具体位置**：「四十次调用里只有一次被拒」「三次没成功」「两次试探略冗余」这类**没有对象的次数**一律被打回，要求落到「第几次工具调用 + 文件名/函数名 + 命令原文/报错原文」。改法：把每次失误**逐条摊开**——`第 12 次调用改 backend/src/models/post.js 时把计数字符串当数字传入，接口回了参数类型不合法`，比「有一次因参数类型写错被拒」强得多。
      6. **指代不能空**：`查不清的那条`、`同一条现象`、`这一步`、`那处判断` 这类没有具体指向的说法会被判「读者无法定位」，必须直接点名**哪一组现象 / 哪个页面 / 哪个文件 / 哪个函数 / 第几次调用**。
      7. **环境原因不算能力扣分**：容器或环境缺依赖（没装数据库访问组件、基础镜像没编译工具链等）造成的调用失败，**不得作为「执行能力」的扣分依据**——平台明确判定「这不是模型自身能力造成的」。要换成**模型自己写错断言/桩、命令参数写错、同段逻辑换三版**这类自身失误来支撑扣分，分数档位不变。
      8. **批量改会撞 B-6 骨架累加雷同**：同批多条用**同一套骨架句**改写（实测「用户报的 N 条逐条能对上…改动没有越出…偏差是…这个取舍它自己定了没有向用户求证」被判定与同批已交付数据骨架重合，相似度 47.7%）会被判重。**每条描述都要换结构**，别让同批文本读出同一个模板。
      9. **改完必须重跑门禁 + 全字段红线扫描**：改写过程本身会引入新红线（实测一轮改写新引入 A 表词 `收尾` 1 处、humanizer 符号 `「」` 1 处）。门禁过后再扫一遍全字段，两个都干净才推平台。

   改完跑门禁，要 `error 0`：`python scripts/cc-solo/check_round_files.py --task {任务}`。
   再跑一次描述风险自查看有没有新引入的问题写法：`python scripts/cc-solo/scan_desc_risks.py --project {PROJECT} --task {任务}`（提示级，命中需人工判断）。
   需要重新生成评价结果时：`python scripts/cc-solo/build_eval_result.py --task <任务1,任务2,…>`（只重生成指定任务，避免把别的任务一起刷新）。

**6.3 更新到平台**（PUT）：
   > ⚠️ **body 必须字段齐全**：PUT 只带改动字段会被平台按 `422 提交数据校验未通过` 拒掉（逐项提示「XX 为必填项」）；**真正的部分更新不存在**。想名义上只改一个字段（如只更正 `question_type`）用 `--only-fields`：它照发完整 body，但先逐字段比对本地与平台现值，指定字段之外一旦还有差异就跳过该条并列出差异字段。
   ```bash
   # 预览（不发请求）：逐字段与平台现值比对，打印「将更新 N 个字段」
   python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json --update-id 3347
   # 只更正任务类型（拦截式：其它字段有差异就不推）
   python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json \
     --only-fields question_type --update-id 4132 --update-id 4133 --commit --write-back
   # 执行（加 --commit；--comment 自定义备注，--record 显式指定记录）
   python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json \
     --update-id 3347 --comment "按质检打回意见整改后更新" --commit --write-back
   ```
   > **任务类型打回**（`整体 · 任务类型与 Prompt 意图错配`）整改时：改的是 `records/` 里该轮的「任务类型」，改完重建结果再 PUT；**只改这一个字段**，描述与分数先不动。判定口径见 `docs/annotate-guide.md` §2.1。
   - 记录定位：优先用 `--record <任务#轮次>`，否则按详情里的 `session_id` + `turn_id` 在结果文件里匹配。
   - `--update-id` 必须配 `--result <评价结果.json>`（只给 `--update-id` 会报「必须提供 --result」）；`--interval` 是**纯数字秒**（`--interval 5`，写 `5s` 会解析失败）。
   - **轨迹附件沿用平台上已有的那份**（`trace_file` 取详情返回值，url 形式），不重新上传。
   - 响应含 `current_version`（新版本号）与 `status`，加 `--write-back` 写回结果 JSON 的 `update_response`。

**6.4 回报 + 复盘（自我学习，必做）**：

   - 回报：新版本号、新状态、改了哪个字段（改前改后字数）；平台随后重新质检，可再 `--detail-id` 看新结论。
   - **复盘**：把这一轮**新出现的打回规则**补进本文档步骤 6、`docs/annotate-guide.md` §9、`skills/03-score-annotate.md` 的硬性要求。
   - 规则要写成**可执行的自查项**（带反例与改写示例），不要只记一句结论；同一条规则再次打回，说明自查项没落地，**优先改自查项**而不是只改这一条数据。

**硬性注意**：

- `editable=false`（质检中 / 已通过 / 已裁决）**不能改**，脚本会跳过并说明当前状态；只有 `PENDING_FIX` 可更新。
- **锁定字段不可改**：`env_snapshot`、`harness`、`repro_level`（详情里的 `locked_fields`）。
- **排除名单里的 ID 一律不动**（`config.toml [submission].fix_exclude_ids`）。
- **只改本机前缀那一侧**：本机是 Windows 就只改 `cc-solo-cc-*`，是 Mac 就只改 `cc-solo-app-*`；另一侧交给另一台机器（脚本 `--scope auto` 已按此过滤）。
- 返修**只升版本、不新增记录**；反复被打回时每次都要按**新的打回原因**重新整改，别只改一处字就重提。
- 更新前必须先把 `records/` 改好并过门禁——脚本只负责把本地现状推上去，不代改文案。
- 返修不是「改字过关」：先归类、后批量改、最后复盘，才算走完一步。

## 注意事项

1. 机械校验只保证**格式层**；描述是否到位、是否真看过轨迹仍须人工复核。
2. **交付物无 AI 痕迹（红线）**：**提交 body 的所有字段**须已在 score 阶段去 AI 化。导出阶段的机械兜底只做符号类 error 与高频词类 warn，**不代改**；命中 error 的条目必须先回 `records/` 重新去 AI 化，再重新生成。
3. **选填字段一律置空字符串**：提交 body 仍保持 24 字段的完整结构，但**所有选填字段（`is_required=false`）的值提交为空串**——本规范里只有 `other_issues`（其他问题）。内容仍留在 `records/` 与质检报告里备查，但**不提交内容**。
4. **不提交到 API 的内部字段**：`备注（内部）`、`截图附件（内部）`、质检报告里的「去 AI 化字段清单」——这些只在 `records/` 与质检报告里留档，**不进提交 body**。
5. 数据不允许返修：提交前完成自查；被抽检不合格的整批可能被拒收。
6. `build_eval_result.py` 只读记录、只写 deliverables；`submit_eval_result.py` 不加 `--commit` 不发任何请求。**本阶段先不执行 `submit_eval_result.py`**（用户决定先不提交）。
7. 中文文件一律 UTF-8（JSON 与质检报告均为 UTF-8 无 BOM 文本）。
8. 附件上限 20 MB（表单定义 `attachment_max_mb`）；整份轨迹通常远小于此（单题量级几百 KB），若超限先排查是否误传了整目录或依赖包。
9. 旧产物口径（`正式提交表-*.csv`、飞书表 `Lg0mbjRpPaxjhmsj27MckrJLnec/tble0z2KnzCfjJmZ`）仅作历史留存，不再使用。
10. **不产出人工核对 CSV**（2026-09-12 起）：产物只有评价结果 JSON + 质检报告；早期版本生成的 CSV 已作废，不作为交付物。
