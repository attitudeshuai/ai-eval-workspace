# SOTA Runner

为指定项目的任务运行 SOTA Agent，收集轨迹、截图与运行产物。

## 触发条件

当用户要求运行 SOTA、测试任务可解性、或生成 SOTA 轨迹时调用本技能。

## 工作流程

1. 确认目标项目 ID 与任务 ID。
2. 读取 `projects/<id>/tasks/webdev-task-XXXX/task.md` 与 `metadata.json`。
3. 创建会话目录：`sessions/session-sota-YYYY-MM-NNN-<agent>/`。
4. 将任务 `starter/` 复制到 `sessions/.../projects/<id>/submissions/<task-id>/<agent>/source/`。
5. 生成标准 Prompt（基于 `task.md` + 项目上下文）。
6. 调用指定 agent（codex / claude-code / kimi-coding）运行任务。
7. 收集产物：代码变更、截图、console 日志、网络日志、运行轨迹。
8. 更新 `projects/<id>/tasks/webdev-task-XXXX/sota-run.md`。

## Prompt 模板结构

```markdown
# 任务

[任务标题]

## 背景
...

## 要求
...

## 起始项目
项目已位于 ./source，请先阅读 README.md 和项目结构。

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
