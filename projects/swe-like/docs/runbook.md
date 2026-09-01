# SWE-like 长程代码任务 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于一步一步完成 SWE-like 任务的全流程：出题 → 运行 → 验收 → 交付。

配置统一读取 `projects/swe-like/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 出题规范详见 `docs/SWE-like Repo-v1.md`；对应技术细节见 `skills/01-task-create.md` ~ `skills/04-export-delivery.md`。

---

## 通用启动语

```text
swe {任务ID} {操作}
```

如：`swe swe-fastapi-001 create`、`swe swe-fastapi-001 record`、`swe swe-fastapi-001 review`、`swe swe-fastapi-001 export Reviewer:张三`

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

---

## 第 1 步：题目创建

### 指令模板

```text
swe swe-fastapi-001 create
```

### AI 会执行

1. 确认用户选择的开源 Repo（URL）+ 固定版本（Commit/Tag）
2. 根据 Repo 主语言与需求性质确认任务类型与主要语言
3. 独立撰写需求 Prompt（不照抄 Issues）
4. 撰写真实性与难度说明、可能涉及模块、Verify Rubric（含反例自查）
5. 生成任务目录 `tasks/{task-id}/`：`task.md` / `meta.json` / `verify-rubric.md`

### 产物

```text
{work_root}/{session}/tasks/swe-fastapi-001/
├── task.md           # 需求 Prompt（原文）
├── meta.json         # Repo URL / Commit/版本 / 主要语言 / 任务类型 / Seed 模型/版本
└── verify-rubric.md  # Verify Rubric（验收前固定）
```

---

## 第 2 步：在 Trae 中运行

用户在 Trae CN + Seed Evolving 中执行：

1. 打开新任务窗口（SOLO Agent 模式，关闭 Auto，选择内部策略模型）
2. 把 `task.md` 的 Prompt **原文**提交，单 Prompt 运行
3. 运行过程中**不追加人工澄清、任务拆解或引导性提示**
4. 记录 Trae Session ID 与有效轮数

### 指令模板（运行完成后录入）

```text
swe swe-fastapi-001 record TraeSessionID:xxxx 有效轮数:135
```

### AI 会执行

1. 读取 `task.md` 确认 Prompt 就绪
2. 录入 Trae Session ID（原文复制）与有效轮数到 `run-log.md`
3. 录入产物结果与补充材料路径到 `result.md`（`model.patch`、verifier 日志、失败测试列表等）

---

## 第 3 步：验收复盘

### 指令模板

```text
swe swe-fastapi-001 review Reviewer:张三
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
{work_root}/{session}/tasks/swe-fastapi-001/review.md
```

评分判定字段中 `【待确认】` / `【待用户填写】` 需人工核对后提交。

---

## 第 4 步：交付导出（追加到飞书多维表格）

`review.md` 人工核对定稿后执行：

### 指令模板

```text
swe swe-fastapi-001 export Reviewer:张三
```

> 提交人**不填写**：飞书表格该字段有默认值，交付时脚本跳过不写入。

### AI 会执行

1. 读取任务目录全部记录文件，检查无占位标记残留
2. 按交付表 20 字段生成记录 JSON（`需求 Prompt（原文）` / `Verify Rubric` / `Trae Session ID` 原文复制）
3. 调用 `scripts/swe-like/append_delivery_feishu.py` 先 `--dry-run` 校验，再正式追加
4. 输出追加的 record_id + 留空字段清单

### 产物

飞书多维表格「数据表」新增一条记录（20 字段）。脚本按 `题目名称` 查重，重复追加需人工确认后加 `--force`。单选字段只能写入已有选项，脚本会校验并列出合法选项。

> 技术细节见 `skills/04-export-delivery.md`。飞书凭证在 `secrets.toml [feishu]`；首次使用需在飞书开发者后台为应用开通 `bitable:app` 权限，并把应用添加为多维表格协作者。
