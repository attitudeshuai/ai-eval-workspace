---
name: webdev-sota-runner
description: 'Run SOTA agent (codex / claude-code / kimi-coding) against webdev-long-horizon tasks. Use when running SOTA, testing task solvability, generating SOTA artifacts, running agent on webdev tasks, 运行 SOTA, 测试任务可解性, 生成 SOTA 产物.'
---

# Web Dev SOTA Runner

为 `projects/webdev-long-horizon` 中的任务运行 SOTA Agent，收集轨迹、截图与运行产物。

## When to Use

- 用户在 `webdev-long-horizon` 项目中要求运行 SOTA
- 需要测试任务是否可被 agent 解出
- 需要生成 SOTA 基线产物用于后续评估

## 前置确认

调用前需确认以下信息：

- **任务 ID**（如 `{prefix}-01.01`，其中 `{prefix}` 为 `config.toml` 中 `task_prefix` 的值）
- **Agent 名称**（`codex` / `claude-code` / `kimi-coding`）
- **Session 名称**（如 `session-sota-2026-07-01.01-codex`）
- **运行模式**：本地（`run_sota.py`）或远程（配合 `webdev-task-packer` skill）

## 目录结构约定

任务按家族分组存放：

```text
projects/webdev-long-horizon/
├── tasks/{prefix}-01/
│   ├── {prefix}-01/          # 顶层基础任务
│   └── {prefix}-01.01/       # 增量任务
└── sources/{prefix}-01/
    ├── {prefix}-01/          # 顶层任务源码
    └── {prefix}-01.01/       # 增量任务源码
```

> `{prefix}` 为 `config.toml` 中 `task_prefix` 的值（默认 `webdev-task-sxw`），下同。

## Procedure

### 1. 读取任务信息

读取 `projects/webdev-long-horizon/tasks/<family>/<task-id>/task.md` 与 `metadata.json`，确认任务内容与元信息。

### 2. 确定源码目录

按以下优先级查找：
1. `projects/webdev-long-horizon/sources/<family>/<task-id>/`
2. `projects/webdev-long-horizon/tasks/<family>/<task-id>/starter/`

### 3. 选择运行模式

#### 模式一：本地运行（推荐用于自动化评估）

```bash
python scripts/webdev-long-horizon/run_sota.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task <task-id> \
  --agent <agent>
```

如需显式指定源码目录：

```bash
python scripts/webdev-long-horizon/run_sota.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task <task-id> \
  --agent <agent> \
  --source-dir <path>
```

此命令会自动：
- 创建隔离会话目录 `sessions/<session-name>/`
- 复制源码到 `sessions/.../submissions/<task-id>/<agent>/source/`
- 基于 `task.md` 生成标准 PROMPT.md
- 调用指定 agent 运行任务

#### 模式二：远程运行（推荐用于 codex-cli）

将任务资产和源码上传到远程机器，直接运行 codex cli。需配合 `webdev-task-packer` skill 完成打包上传。

远程机器操作示例（`<remote_dir>` 来自 `projects/webdev-long-horizon/config.toml` 中 `[remote].remote_dir`）：

```bash
ssh <host> -p <port>
cd <remote_dir>/<task-id>/source

codex exec -m gpt-5.6-sol \
  --dangerously-bypass-approvals-and-sandbox \
  < <remote_dir>/<task-id>/PROMPT.md \
  > <remote_dir>/<task-id>/sota.log 2>&1
```

### 4. 收集产物

运行结束后收集：
- 代码变更（修改后的完整源码）
- 截图（关键状态截图保存到 `./screenshots/`）
- Console 日志
- 网络日志
- 运行轨迹 transcript

### 5. 更新运行记录

更新 `projects/webdev-long-horizon/tasks/<family>/<task-id>/sota-run.md`，记录运行时长、agent 版本与消耗估算。

### 6. （远程模式）回收产物

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task <task-id> \
  --agent <agent> \
  --session <session-name>
```

## 产物位置

**本地模式**：

```text
sessions/webdev-long-horizon/<session-name>/
  submissions/<task-id>/<task-id>/
    PROMPT.md             # 由 run_sota.py 基于 task.md 生成
    run.sh
```

**远程模式**（默认在远程 `<remote_dir>/`）：

```text
<remote_dir>/<task-id>/
  source/                   # codex 修改后的源码
  screenshots/              # 关键状态截图
  sota.log                  # 运行日志
```

## 最终交付打包

SOTA 运行完成并生成评估报告后，打包最终交付资产：

```bash
python scripts/webdev-long-horizon/package_deliverable.py \
  --task <task-id> \
  --session <session-name> \
  --agent <agent>
```

交付包结构（tar.gz 解压后）：

```text
<task-id>/
├── task.md
├── metadata.json
├── README.md
├── rubric.json
├── target_states.md
├── sota-run.md
├── starter/               # 初始项目代码
├── assets/                # 任务素材
├── mock-data/
├── tests/
└── screenshots/           # 关键状态截图
```

打包结果：`deliverables/webdev-long-horizon/<task-id>.tar.gz`

## 注意事项

- 推荐将源码放到 `sources/<family>/<task-id>/`，目录名与任务 ID 一致，无需传 `--source-dir`
- 记录运行时长与估算消耗
- 若 agent 失败，记录失败模式
- 不修改原任务目录中的文件
- 最终交付包只包含任务资产、`starter/` 和 SOTA 最终截图

## 与其他 Skill 的关系

- 远程运行前先使用 `webdev-task-packer` skill 打包上传
- 运行结束后使用 `evaluator` skill 对产物进行评估
- 本项目 SOTA 运行优先使用本 skill；非 webdev 项目使用 `sota-runner` skill
