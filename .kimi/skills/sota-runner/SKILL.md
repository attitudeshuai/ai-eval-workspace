---
name: sota-runner
description: Run a SOTA Agent for a specified project task and collect artifacts.
---

# SOTA Runner

为指定项目的任务运行 SOTA Agent，收集轨迹、截图与运行产物。

## 触发条件

当用户要求运行 SOTA、测试任务可解性、或生成 SOTA 轨迹时调用本技能。

## 工作流程

1. 确认目标项目 ID 与任务 ID。
2. 读取项目级文档确认运行约定：
   - `projects/<id>/AGENTS.md`
   - `projects/<id>/OPERATIONAL_WORKFLOW.md`
   - `projects/<id>/README.md`
   - `projects/<id>/config.toml`
3. 读取 `projects/<id>/tasks/<task-dir>/task.md` 与 `metadata.json`。
   - 若项目使用层级目录结构，使用 `find_task_dir(project_id, task_id)` 自动查找。
4. 创建会话目录：`sessions/session-sota-YYYY-MM-NNN-<agent>/`。
5. 按项目约定找到任务源码目录（如 `starter/`、`sources/<family>/<task-id>/` 等），复制到 `sessions/<project-id>/<session>/submissions/<task-id>/<task-id>/`。
6. 生成标准 Prompt（基于 `task.md` + 项目上下文）。
7. 调用指定 agent（codex / claude-code / kimi-coding）运行任务。
8. 收集产物：代码变更、截图、console 日志、网络日志、运行轨迹。
9. 更新项目约定的运行记录文件（如 `projects/<id>/tasks/<family>/<task-id>/sota-run.md`）。

## Prompt 模板结构

```markdown
# 任务

[任务标题]

## 背景
...

## 要求
...

## 起始项目
项目已位于当前目录，请先阅读 README.md 和项目结构。

## 交付物
- 可运行的完整代码
- 关键状态截图保存到 ./screenshots/
- 测试运行记录
```

## 产物保存

```text
sessions/session-sota-YYYY-MM-NNN-<agent>/
  projects/<project-id>/
    submissions/<task-id>/<agent>/
      source/
      screenshots/
      console.log
      network.log
      transcript.md
```

## 注意事项

- 记录运行时长与估算消耗。
- 若 agent 失败，记录失败模式。
- 不修改原任务目录中的文件。

## 项目特定说明

- 对于 `webdev-long-horizon` 项目，优先使用专门的 `webdev-sota-runner` skill。
- 若用户希望将任务上传到远程机器用 codex 直接运行，使用 `webdev-task-packer` skill。
