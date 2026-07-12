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

- 任务 ID（如 `{prefix}-01.01`，其中 `{prefix}` 为 `config.toml` 中 `task_prefix` 的值）
- Agent 名称（`codex` / `claude-code` / `kimi-coding`）
- Session 名称
- 运行模式：本地（`run_sota.py`）或远程（`codex`）
- 是否需要显式指定源码目录（可选，通常不需要）

## 目录结构说明

任务按家族分组存放：

```text
projects/webdev-long-horizon/
├── tasks/{prefix}-01/
│   ├── {prefix}-01/
│   └── {prefix}-01.01/
└── sources/{prefix}-01/
    ├── {prefix}-01/
    └── {prefix}-01.01/
```

> `{prefix}` 为 `config.toml` 中 `task_prefix` 的值（默认 `webdev-task-sxw`）。

## 两种运行模式

### 模式一：本地运行（推荐用于自动化评估）

使用 `scripts/run_sota.py` 创建隔离会话并调用本地 agent。

```bash
python scripts/webdev-long-horizon/run_sota.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task {prefix}-01.01 \
  --agent <agent>
```

如需显式指定源码：

```bash
python scripts/webdev-long-horizon/run_sota.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task {prefix}-01.01 \
  --agent <agent> \
  --source-dir <path>
```

### 模式二：远程运行（推荐用于 codex-cli）

将任务资产和源码上传到远程机器，直接运行 codex cli。此模式需配合 `webdev-task-packer` skill。

远程机器示例（`<remote_dir>` 来自 `projects/webdev-long-horizon/config.toml` 中 `[remote].remote_dir`；ssh 连接信息来自 `secrets.toml`）：

```bash
ssh root@59.49.28.154 -p 7826
cd <remote_dir>/{prefix}-01.01/{prefix}-01.01

# 自动化运行需要 --dangerously-bypass-approvals-and-sandbox
codex exec -m gpt-5.6-sol \
  --dangerously-bypass-approvals-and-sandbox \
  < <remote_dir>/{prefix}-01.01/PROMPT.md \
  > <remote_dir>/{prefix}-01.01/sota-run.md 2>&1
```

> 源码目录为 `<remote_dir>/{prefix}-01.01/{prefix}-01.01/`，提示词文件在 `<remote_dir>/{prefix}-01.01/PROMPT.md`，运行日志保存到 `<remote_dir>/{prefix}-01.01/sota-run.md`。

## 工作流程

1. 读取 `projects/webdev-long-horizon/tasks/<family>/<task-id>/task.md` 与 `metadata.json`。
2. 按项目约定找到任务源码目录：
   - `projects/webdev-long-horizon/sources/<family>/<task-id>/`
   - `projects/webdev-long-horizon/tasks/<family>/<task-id>/starter/`
3. 创建会话目录：`sessions/<session-name>/`。
4. 将源码复制到 `sessions/webdev-long-horizon/<session>/submissions/<task-id>/<task-id>/`。
5. 运行 agent：
   - 本地模式：由 `run_sota.py` 自动调用 agent。
   - 远程模式：提示用户参考 `webdev-task-packer` skill 上传后执行 codex。
6. 收集产物：代码变更、截图、console 日志、运行轨迹。
7. 更新 `projects/webdev-long-horizon/tasks/<family>/<task-id>/sota-run.md`。

## 产物位置

本地模式产物：

```text
sessions/webdev-long-horizon/<session-name>/
  submissions/<task-id>/<task-id>/
    PROMPT.md           # 由 run_sota.py 基于 task.md 生成
    run.sh
```

远程模式产物（默认在远程 `<remote_dir>/`）：

```text
<remote_dir>/{prefix}-01.01/
  {prefix}-01.01/       # codex 修改后的源码
  PROMPT.md             # 提示词
  assets/               # 任务素材
  tests/                # 测试骨架
  mock-data/            # mock 数据
  sota-run.md          # 运行记录（含完整日志）
```

## 最终交付

SOTA 运行、回收产物并生成评估报告后，使用 `package_deliverable.py` 生成交付文件夹：

```bash
python scripts/webdev-long-horizon/package_deliverable.py \
  --task {prefix}-01.01 \
  --session session-sota-2026-07-01.01-codex \
  --agent codex
```

交付前需更新 README.md 添加「启动方式、测试方式、目录结构、已知限制」章节。输出为文件夹 `deliverables/webdev-long-horizon/{prefix}-01.01/`。

## 发布到 GitHub

将交付文件夹发布为 GitHub 公开仓库：

```bash
python scripts/webdev-long-horizon/publish_to_github.py \
  --task {prefix}-01.01 \
  --deliverable deliverables/webdev-long-horizon/{prefix}-01.01
```

GitHub 凭据配置在 `projects/webdev-long-horizon/secrets.toml` 的 `[github]` 段（`username` 和 `token`）。

## 注意事项

- 推荐将源码放到 `sources/<family>/<task-id>/`，目录名与任务 ID 一致。
- 记录运行时长与估算消耗。
- 若 agent 失败，记录失败模式。
- 不修改原任务目录中的文件。
- 交付前需更新 README.md 添加「启动方式、测试方式、目录结构、已知限制」章节，输出为文件夹。
- 交付完成后使用 `publish_to_github.py` 发布为 GitHub 公开仓库。
