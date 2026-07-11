---
name: webdev-sota-runner
description: Run SOTA for a task in the webdev-long-horizon project. Trigger when the user wants to run an agent (codex / claude-code / kimi-coding) against a webdev-long-horizon task.
---

# Web Dev SOTA Runner

为 `projects/webdev-long-horizon` 中的任务运行 SOTA Agent。

## 触发条件

当用户在 `webdev-long-horizon` 项目中要求运行 SOTA、测试任务可解性、或生成 SOTA 产物时调用本技能。

## 输入信息

调用前需要确认：

- 任务 ID（如 `webdev-task-01.01`）
- Agent 名称（`codex` / `claude-code` / `kimi-coding`）
- Session 名称
- 运行模式：本地（`run_sota.py`）或远程（`codex`）
- 是否需要显式指定源码目录（可选，通常不需要）

## 目录结构说明

任务按家族分组存放：

```text
projects/webdev-long-horizon/
├── tasks/webdev-task-01/
│   ├── webdev-task-01/
│   └── webdev-task-01.01/
└── sources/webdev-task-01/
    ├── webdev-task-01/
    └── webdev-task-01.01/
```

`run_sota.py` 会根据 task_id 自动在层级目录中查找任务目录和源码目录。

## 两种运行模式

### 模式一：本地运行（推荐用于自动化评估）

使用 `scripts/run_sota.py` 创建隔离会话并调用本地 agent。

```bash
python scripts/webdev-long-horizon/run_sota.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task webdev-task-01.01 \
  --agent <agent>
```

如需显式指定源码：

```bash
python scripts/webdev-long-horizon/run_sota.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task webdev-task-01.01 \
  --agent <agent> \
  --source-dir <path>
```

### 模式二：远程运行（推荐用于 codex-cli）

将任务资产和源码上传到远程机器，直接运行 codex cli。此模式需配合 `webdev-task-packer` skill。

远程机器示例（`<remote_dir>` 来自 `projects/webdev-long-horizon/config.toml` 中 `[remote].remote_dir`；ssh 连接信息来自 `secrets.toml`）：

```bash
ssh root@59.49.28.154 -p 7826
cd <remote_dir>/webdev-task-01.01/source

# 自动化运行需要 --dangerously-bypass-approvals-and-sandbox
# 若手动交互运行，可去掉该参数
codex exec -m gpt-5.6-sol \
  --dangerously-bypass-approvals-and-sandbox \
  < <remote_dir>/webdev-task-01.01/PROMPT.md
```

> 如果元数据和源码是分开上传的，源码目录通常是 `<remote_dir>/webdev-task-01.01/source/`。

## 工作流程

1. 读取 `projects/webdev-long-horizon/tasks/<family>/<task-id>/task.md`、`metadata.json`、`PROMPT.md`。
2. 按项目约定找到任务源码目录：
   - `projects/webdev-long-horizon/sources/<family>/<task-id>/`
   - `projects/webdev-long-horizon/tasks/<family>/<task-id>/starter/`
3. 创建会话目录：`sessions/<session-name>/`。
4. 将源码复制到 `sessions/.../projects/webdev-long-horizon/submissions/<task-id>/<agent>/source/`。
5. 运行 agent：
   - 本地模式：由 `run_sota.py` 自动调用 agent。
   - 远程模式：提示用户参考 `webdev-task-packer` skill 上传后执行 codex。
6. 收集产物：代码变更、截图、console 日志、运行轨迹。
7. 更新 `projects/webdev-long-horizon/tasks/<family>/<task-id>/sota-run.md`。

## 产物位置

本地模式产物：

```text
sessions/<session-name>/
  projects/webdev-long-horizon/
    submissions/<task-id>/<agent>/
      source/
      screenshots/
      PROMPT.md
      run.sh
```

远程模式产物（默认在远程 `<remote_dir>/`）：

```text
<remote_dir>/webdev-task-01.01/
  source/               # codex 修改后的源码
  screenshots/          # 关键状态截图
  sota.log              # 运行日志（如果已保存）
```

## 最终交付打包

SOTA 运行、回收产物并生成评估报告后，使用 `package_deliverable.py` 一键打包最终交付资产：

```bash
python scripts/webdev-long-horizon/package_deliverable.py \
  --task webdev-task-01.01 \
  --session session-sota-2026-07-01.01-codex \
  --agent codex
```

交付包结构（tar.gz 解压后）：

```text
webdev-task-01.01/
├── task.md
├── metadata.json
├── README.md
├── rubric.json
├── target_states.md
├── sota-run.md
├── assets/
├── mock-data/
├── tests/
└── sota/
    ├── source/          # 从远端拉下来的 agent 修改后源码
    ├── screenshots/
    ├── sota.log
    ├── PROMPT.md
    └── report/
        ├── report.json
        └── report.md
```

打包结果：`deliverables/webdev-long-horizon/webdev-task-01.01.tar.gz`

## 注意事项

- 推荐将源码放到 `sources/<family>/<task-id>/`，目录名与任务 ID 一致，这样无需传 `--source-dir`。
- 记录运行时长与估算消耗。
- 若 agent 失败，记录失败模式。
- 不修改原任务目录中的文件。
- 最终交付包中的源码应使用从远端拉下来的 `sota/source/`，而不是初始 baseline。
