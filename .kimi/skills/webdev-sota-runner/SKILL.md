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

- 任务 ID（如 `webdev-task-XXXX`）
- Agent 名称（codex / claude-code / kimi-coding）
- Session 名称
- 是否需要显式指定源码目录（可选，通常不需要）

## 工作流程

1. 读取 `projects/webdev-long-horizon/tasks/<task-id>/task.md` 与 `metadata.json`。
2. 创建会话目录：`sessions/<session-name>/`。
3. 确定源码来源（按以下优先级）：
   - `--source-dir` 显式指定目录
   - `projects/webdev-long-horizon/sources/<task-id>/`
   - `projects/webdev-long-horizon/tasks/<task-id>/starter/`
   复制到 `sessions/<session-name>/projects/webdev-long-horizon/submissions/<task-id>/<agent>/source/`。
4. 运行 SOTA：
   ```bash
   python scripts/run_sota.py \
     --session <session-name> \
     --project webdev-long-horizon \
     --task <task-id> \
     --agent <agent>
   ```
   如需显式指定源码：
   ```bash
   python scripts/run_sota.py \
     --session <session-name> \
     --project webdev-long-horizon \
     --task <task-id> \
     --agent <agent> \
     --source-dir <path>
   ```
5. 收集产物：代码变更、截图、console 日志、运行轨迹。
6. 更新 `projects/webdev-long-horizon/tasks/<task-id>/sota-run.md`。

## 产物位置

```text
sessions/<session-name>/
  projects/webdev-long-horizon/
    submissions/<task-id>/<agent>/
      source/
      screenshots/
      PROMPT.md
      run.sh
```

## 注意事项

- 推荐将源码放到 `sources/<task-id>/`，目录名与任务 ID 一致，这样无需传 `--source-dir`。
- 记录运行时长与估算消耗。
- 若 agent 失败，记录失败模式。
- 不修改原任务目录中的文件。
