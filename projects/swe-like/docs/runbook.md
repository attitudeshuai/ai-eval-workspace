# SWE-like 长程代码任务 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于一步一步完成 SWE-like 任务的全流程：出题 → 运行 → 验收 → 交付。

配置统一读取 `projects/swe-like/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 出题规范详见 `docs/SWE-like Repo-v2.md`（现行版）；内部规范见 `docs/内部规范.md`（账号积分/步数统计/表单填写/省积分）；步数口径见 `docs/步数统计.md`；对应技术细节见 `skills/01-task-create.md` ~ `skills/04-export-delivery.md`。

---

## 通用启动语

```text
swe {项目名/分支名} {操作}
```

> - `create`：填**项目名**（repo 名），一次创建 3 道题 + 3 个分支。如 `swe restic create`
> - `record` / `review` / `export`：填**分支名**（`{repo}-01` / `{repo}-02` / `{repo}-03`），逐题操作。如 `swe restic-01 record`

如：`swe restic create`、`swe restic-01 record`、`swe restic-01 review`、`swe restic-01 export`

---

## 前置准备

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

### 配置本地环境

```toml
work_root = "sessions/swe-like"
active_session = "session-0001"
```

### 飞书配置

```toml
[feishu]
app_id = ""      # secrets.toml
app_secret = ""  # secrets.toml
```

### 账号积分（TRAE CN Pro）

- 使用 Seed Evolving 需开通 Pro 会员：首月 59 元订阅付费，付款后在微信/支付宝取消订阅、发票先不开。
- 用完 Pro 4000 积分 + 新账号赠送 2500 积分后，换新手机号注册再购会员。
- 同一台电脑登录多个账号有风控风险：用完后用 Codex 清除 TRAE CN 所有安装痕迹再重装。
- 详见 `docs/内部规范.md`。

---

## 第 1 步：题目创建

### 指令模板

```text
swe restic create
```

> **只提供项目名（repo 名）**，一次创建 3 道题 + 3 个分支（`{repo}-01/02/03`）——因为三者 Repo URL 和最新 commit 相同，仓库信息只需提供一次。
> 给出 Repo URL；**版本默认由 AI 自动获取最新 Commit ID** 并写入各题 `meta.json`（如需固定到某 commit/tag 可覆盖）。也可不指定仓库，让 AI 从 `repo-fetcher` 素材池选。
> **前置**：需已 fork 该 Repo，并把 fork clone 到 `repos/{repo}/origin/`（clone 由用户执行，AI 沙箱大传输会 reset）。

```text
swe restic create
仓库：https://github.com/restic/restic
```

### AI 会执行

1. 确认开源 Repo（URL）；版本默认获取最新 Commit ID（如需固定到某 commit/tag 可覆盖）
2. 根据 Repo 主语言与需求性质确认任务类型与主要语言（本轮仅限 Go / Python）
3. 独立撰写 **3 份**需求 Prompt（不照抄 Issues，三道题各不同）
4. 各写真实性与难度说明、可能涉及模块、Verify Rubric（含反例自查）
5. 在 `repos/{repo}/origin` 里创建 3 个分支 `{repo}-01/02/03`，用 `git worktree add` 拉出 3 份工作目录
6. 生成 3 个任务目录 `tasks/{repo}/` 下的 `{repo}-01/`、`{repo}-02/`、`{repo}-03/`

### 产物

```text
{work_root}/{session}/tasks/restic/
├── restic-01/                 # 第 1 题
│   ├── task.md                 # 需求 Prompt（原文）
│   ├── meta.json               # Repo URL / Commit/版本 / 主要语言 / 任务类型 / Seed 模型/版本
│   ├── verify-rubric.md        # Verify Rubric（验收前固定）
│   └── session.md              # Trae 完整会话（出题阶段创建空文件，第 2 步粘贴，供步数统计）
├── restic-02/
│   └── ...（同上）
└── restic-03/
    └── ...（同上）

{work_root}/{session}/repos/restic/
├── origin/                     # 主分支基线
├── restic-01/                  # 分支 restic-01（worktree）
├── restic-02/                  # 分支 restic-02（worktree）
└── restic-03/                  # 分支 restic-03（worktree）
```

> 三个分支共用同一个 commit（都 checkout 到 `meta.json` 的 `commit`）。

---

## 第 2 步：在 Trae 中运行

### 指令模板

```text
swe restic-01 run
```

### AI 会执行（就绪检查 + 引导）

1. 检查任务就绪：`tasks/{repo}/{branch}/task.md` 与 `verify-rubric.md` 已存在且冻结；`repos/{repo}/{branch}/` worktree 存在，checkout 到 `meta.json` 的 `commit`
2. 输出运行指引：让用户打开 `repos/{repo}/{branch}/` 项目，按下方「用户在 Trae 中执行」单 Prompt 运行

> 分支与 worktree 在第 1 步 `create` 时已建好；`run` 不再重复创建，只做检查与引导。

### 用户在 Trae 中执行

1. 打开 `repos/{repo}/{branch}/`（{repo}-01 / {repo}-02 / {repo}-03 之一）项目，新建任务窗口（SOLO Agent 模式，关闭 Auto，选择内部策略模型）
2. 把对应题的 `task.md` Prompt **原文**提交，单 Prompt 运行
3. 运行过程中**不追加人工澄清、任务拆解或引导性提示**
4. 记录 Trae Session ID 与有效轮数（= 模型输出步数）
5. **省积分经验**（见 `docs/内部规范.md`）：执行超过一个半小时可停止，按「> 100 轮且效果差」提交；若模型正在跑测试/执行任务或马上结束，可再等等尽量提交完整数据；不要为省积分故意出难题

### 获取有效轮数（= 模型输出步数）

表单的「有效轮数」字段就是「模型输出步数」（有效 TC 次数）。跑完**尽快**执行——Trae 日志会动态清除：

1. 用户复制完整 Trae Session ID 发给 AI，并把 Trae 完整会话粘贴到任务目录的 `session.md`
2. AI 按 `docs/步数统计.md` 口径只读 Trae 日志统计文件操作 TC，从 `session.md` 统计终端命令 TC（= 有效轮数 = 模型输出步数）
3. AI 把该数字记入 `run-log.md`

> 有效轮数 = 模型输出步数 = 有效 TC（工具调用）次数，按 `toolCallId`/`serverCallId` 去重。口径详见 `docs/步数统计.md`。

### 提交 + 记录 Commit URL（导出飞书前）

模型改完代码后：AI 在对应 `repos/{repo}/{branch}/` 里 `git add` + `git commit`，push 到 fork，得到 commit URL 记入 `run-log.md`；导出飞书时填入 `Commit URL` 字段（与 gsb 类似）。**本地代码（含模型改动）先不要删除**，用于 commit 与后续复核。

> **push 走 HTTPS + PAT**（`secrets.toml` 的 `github_pat` / `github_username`），不用 SSH（AI 沙箱 SSH 与默认 schannel 会失败）。命令形如：`git -c http.sslBackend=openssl -c http.extraHeader="Authorization: Basic <base64(user:pat)>" push https://github.com/<user>/<repo>.git <branch>`

### 指令模板（运行完成后录入）

```text
swe restic-01 record TraeSessionID:xxxx
```

> 用户**只提供 Trae Session ID（原文复制）**；有效轮数与 Commit URL 由 AI 完成，不用你填。

### AI 会执行

1. 读取 `task.md` 确认 Prompt 就绪
2. 用 Session ID 读 Trae 日志统计文件操作 TC，从 `session.md` 统计终端命令 TC，得到「有效轮数」（= 模型输出步数，口径见 `docs/步数统计.md` 与 `skills/02-step-count.md`）
3. 在对应 `repos/{repo}/{branch}/` 里 `git add` + `git commit`，push 到 fork（HTTPS + PAT），得到 Commit URL
4. 把 Trae Session ID（原文复制）、有效轮数、Commit URL 写入 `run-log.md`
5. 录入产物结果与补充材料路径到 `result.md`（`model.patch`、verifier 日志、失败测试列表等）
6. 提示用户：本地代码先不要删除（用于 commit 与复核）

---

## 第 3 步：验收复盘

### 指令模板

```text
swe restic-01 review
```

### AI 会执行

1. 读取已冻结的 `verify-rubric.md`，逐条对照产物验收（证据驱动）
2. 调用 `implementation-reviewer` 辅助评审（可选）
3. 判定是否完成需求（完成 / 部分完成 / 未完成 / 无法判断）
4. 判定是否通过质检（通过 / 未通过）
5. 按收录标准做收录决策（有效轮数 > 100 → 长程题；≤ 100 且实现差 → 难题；≤ 100 且实现好 → 不收录）
6. 写入 `review.md`

### 产物

```text
{work_root}/{session}/tasks/restic/restic-01/review.md
```

评分判定字段中 `【待确认】`（Trae Session ID 2 / seed 轮次）默认留空；Reviewer 不再填写。

---

## 第 4 步：交付导出（追加到飞书多维表格）

`review.md` 定稿后执行：

### 指令模板

```text
swe restic-01 export
```

> 提交人**不填写**：飞书表格该字段有默认值，交付时脚本跳过不写入。

> **表单填写规范**（见 `docs/内部规范.md`）：任何字段不得含 Markdown 标签（标题/引用/代码块/加粗/斜体），去 AI 味；本轮语言仅限 Go / Python；一个 Repo 最多 3 条；Prompt 像真实 MR 需求，不扩展成「大而全」文档；题要和 Repo 匹配（管理员可能合并）。

### AI 会执行

1. 读取任务目录全部记录文件，检查无占位标记残留
2. 按交付表 24 字段生成记录 JSON（`需求 Prompt（原文）` / `Verify Rubric` / `Trae Session ID` 原文复制）
3. 调用 `scripts/swe-like/append_delivery_feishu.py` 先 `--dry-run` 校验，再正式追加
4. 输出追加的 record_id + 留空字段清单

### 产物

飞书多维表格「数据表」新增一条记录（24 字段）。脚本按 `题目名称` 查重，重复追加需人工确认后加 `--force`。单选字段只能写入已有选项，脚本会校验并列出合法选项。

> 技术细节见 `skills/04-export-delivery.md`。飞书凭证在 `secrets.toml [feishu]`；首次使用需在飞书开发者后台为应用开通 `bitable:app` 权限，并把应用添加为多维表格协作者。
