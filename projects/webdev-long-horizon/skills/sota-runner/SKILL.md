---
name: sota-runner
description: 'Run a SOTA agent for any project task and collect artifacts. Use when running SOTA, testing task solvability, generating SOTA trajectories, 运行 SOTA, 测试可解性, 生成 SOTA 基线. For webdev-long-horizon, prefer webdev-sota-runner.'
---

# SOTA Runner

为指定项目的任务运行 SOTA Agent，收集轨迹、截图与运行产物。

## When to Use

- 用户要求运行 SOTA
- 需要测试任务是否可被 agent 解出
- 需要生成 SOTA 基线轨迹

> 对于 `webdev-long-horizon` 项目，优先使用 `webdev-sota-runner` skill。

## 前置确认

调用前需确认：
- **项目 ID** 与 **任务 ID**
- **Agent 名称**（如 `codex`、`claude-code`、`kimi-coding`）
- **Session 名称**

## Procedure

### 1. 读取项目约定

读取项目级文档确认运行约定：
- `projects/<project-id>/AGENTS.md`
- `projects/<project-id>/SKILL.md`
- `projects/<project-id>/README.md`
- `projects/<project-id>/config.toml`

### 2. 读取任务信息

读取 `projects/<project-id>/tasks/<task-dir>/task.md` 与 `metadata.json`。

若项目使用层级目录结构，使用 `find_task_dir(project_id, task_id)` 自动查找。

### 3. 创建会话目录

```text
sessions/session-sota-YYYY-MM-NNN-<agent>/
```

### 4. 准备源码

按项目约定找到任务源码目录（如 `starter/`、`sources/<family>/<task-id>/` 等），复制到：
`sessions/.../<project-id>/<session>/submissions/<task-id>/<task-id>/`

### 5. 生成 Prompt

基于 `task.md` + 项目上下文生成标准 Prompt：

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

### 6. 运行 Agent

调用指定 agent 运行任务。

### 7. 收集产物

- 代码变更
- 截图
- Console 日志
- 网络日志
- 运行轨迹 transcript

### 8. 更新运行记录

更新项目约定的运行记录文件（如 `projects/<project-id>/tasks/<family>/<task-id>/sota-run.md`）。

## 产物位置

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

- 记录运行时长与估算消耗
- 若 agent 失败，记录失败模式
- 不修改原任务目录中的文件

## 与其他 Skill 的关系

- webdev-long-horizon 项目使用专用的 `webdev-sota-runner` skill
- 远程运行模式使用 `webdev-task-packer` skill 打包上传
- 运行结束后使用 `evaluator` skill 进行评估
