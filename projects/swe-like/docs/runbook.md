# SWE-like 长程代码任务 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于完成 SWE-like 任务全流程：出题 → 运行取证 → 验收 → 回填底稿。

配置统一读取 `projects/swe-like/config.toml`。

> 出题规范见 `docs/SWE-like Repo-v3.md`（现行版）；内部规范见 `docs/内部规范-v1.md`（Commit URL / 积分 / 步数统计 / 表单 / 省积分）；常见问题见 `docs/常见问题.md`；技术细节见 `skills/01-task-create.md` ~ `skills/04-export-delivery.md`。

---

## 通用启动语

```text
swe {项目名/分支名} {操作}
```

> - `create`：填**项目名**（repo 名），分两小步：先生成候选池（10 个/repo）；用户预检后带结果再执行一次，落地成题。如 `swe restic create` → `swe restic create 通过：候选 1、2`
> - `run` / `record` / `review` / `export`：填**题目名/分支名**，逐题操作。如 `swe restic-01 record`
>   - `run`：运行指引（就绪检查 + 提示到 Trae/TraeX/miniswe 执行）；运行完成后用 `record` 录入
>   - `record`：只做录入（Session ID / 取证 / 轮数 / 验证截图 / commit URL）

如：`swe restic create`、`swe restic create 通过：候选 1、2`、`swe restic-01 record`、`swe restic-01 review`、`swe restic-01 export`

---

## 第 1 步：题目创建（候选池 → 预检 → 生成交付包）

### 1a. 生成候选池

```text
swe restic create
仓库：https://github.com/restic/restic
```

#### AI 会执行

1. 确认开源 Repo，锁 `base_commit`（40 位完整 SHA）
2. 对该 repo 出 10 个候选提示词，写入 `tasks/{repo}/prompt-candidates.md`（一个 repo 一个文件）——先本地代码验证功能不存在，再做公开 Issues 相似查重（open + closed，防「同一诉求内置化改写」），按难度门槛自检，独立写需求（不照抄 Issues）
3. 被击毙的方向记入该文件末尾「调研阵亡名单」

### 1b. 预检通过后落地

用户把候选池拿去需求预检，将结果发给 AI：

```text
swe restic create 通过：候选 1、2、3
```

#### AI 会执行（对每个通过的候选）

1. 正文落到任务目录，生成 `instruction.md`
2. 写 `tests/nl_rubric.yaml`（≥5 条，含 f2p / p2p）
3. 写 `environment/Dockerfile`（ARG BASE_SHA = base_commit）
4. 写 `task.toml`（16 键）
5. 检查对应分支与 worktree 是否就位（缺则在 base_commit 上创建）
6. `preflight_check.py --stage create` 自检

> 未通过的候选留在池中标注即可，不删；池子不足 10 个或全军覆没时，让 AI 补齐（如 `swe restic create 补齐`）。

### 产物（伪 Harbor 目录）

```text
<题目名称>/
├── task.toml                 # 16 键底稿字段
├── instruction.md            # 需求 Prompt 原文
├── environment/Dockerfile    # 基线 mars-base + BASE_SHA
├── tests/nl_rubric.yaml      # 自然语言判分标准
├── solution/                 # 留空
└── evidence/                 # 第 2 步取证填充
```

> 骨架见 `templates/harbor/`。题目名 = zip 目录名。

---

## 第 2 步：运行 + 取证 + 验证截图

### 指令模板

```text
swe restic-01 run
```

### 用户在 Trae/TraeX/miniswe 执行

1. 打开 fork 的 repo，把 `instruction.md` Prompt **原文**提交，**单 Prompt 单轮**运行
2. 运行过程中**不追加人工澄清、任务拆解或引导性提示**
3. 记录 `trae_session_id`（miniswe 留空）与 `harness`（Trae / TraeX / miniswe）

### AI 会执行（用户粘贴对话后）

1. **取证**：trajectory（`.trae/cli/sessions/` → `evidence/trajectory.jsonl` 等）+ `evidence/model.patch`（diff 基准 = base_commit）+ `evidence/screenshots/`
2. **验证 + 截图**：在 worktree 里复跑验证（pytest / go test，复用会话里命令与 PYTHONPATH/GOPROXY），确认成功与回归；把验证结果渲染成 PNG 存 `evidence/screenshots/`（至少 1 张）
3. **算有效轮数**：agent step 口径（一次模型调用 = 1 步），TraeX 用 `count_steps.py`、miniswe 取 `api_calls`（见 `skills/02-step-count.md`）
4. **填 task.toml**：`trae_session_id`、`effective_turns`、`harness`、`seed_model`
5. **commit 到 fork**：只含模型改动的单独 commit，push 后记 commit URL（见 `docs/内部规范-v1.md`）

### 指令模板（运行完成后录入）

```text
swe restic-01 record TraeSessionID:xxxx
```

> 用户只提供 Trae Session ID 原文 + 对话轨迹；有效轮数、验证、截图、commit URL 由 AI 完成。

---

## 第 3 步：验收复盘

### 指令模板

```text
swe restic-01 review
```

### AI 会执行

1. 读冻结的 `tests/nl_rubric.yaml`，逐条验收（证据驱动，可运行验证优先）
2. 判定 `requirement_met`（完成 / 部分完成 / 未完成 / 无法判断）
3. 收录决策（只看「有效轮数 + requirement_met」两列）：

   | 有效轮数 | requirement_met | 收录 |
   |------|------|------|
   | > 100 | 任意 | 长程题 |
   | ≤ 100 | 完成 | 不收录（不计酬） |
   | ≤ 100 | 部分完成 / 未完成 / 无法判断 | 难题 |

4. 写 `run_result`（逐条对应 rubric：id + 通过/未通过 + 原因）回填 `task.toml`

---

## 第 4 步：交付导出（回填底稿网站）

### 指令模板

```text
swe restic-01 export
```

### AI 会执行

1. 组装交付包：`<题目名称>/`（task.toml + instruction.md + Dockerfile + nl_rubric.yaml + evidence/）
2. 体检：`python3 toml2base.py --dry-run <题目目录>`（不写库）
3. 回填：`python3 toml2base.py <题目目录>`（整包 zip 上传「交付包」列）

### 退回红线（提交前自查）

必需文件缺失/空、无 trajectory、harness 填 Trae/TraeX 却没 session id、screenshots 空、title ≠ 目录名、base_commit ≠ BASE_SHA、rubric <5 或 type/id 非法、run_result 未逐条对应或与 requirement_met 矛盾、残留占位符。

> 技术细节见 `skills/04-export-delivery.md`。
