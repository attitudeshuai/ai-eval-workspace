---
name: task-creator
description: Create a high-quality long-horizon task in a specified project.
---

# Task Creator

在指定项目中创建符合规范的高难度长程任务。

## 触发条件

当用户要求创建新任务、设计任务需求、或生成任务骨架时调用本技能。

## 工作流程

1. 确认目标项目 ID（如未指定，询问用户）。
2. 若项目定义了分类体系，读取 `projects/<id>/categories.json` 确认可选标签。
3. 读取项目级文档确认源码存放约定：
   - `projects/<id>/AGENTS.md`
   - `projects/<id>/OPERATIONAL_WORKFLOW.md`
   - `projects/<id>/README.md`
   - `projects/<id>/config.toml`
4. 使用 `python scripts/webdev-long-horizon/create_task.py --project <id>` 生成任务骨架。
   - 若项目是层级结构（如 webdev-long-horizon），增量任务需传 `--parent <task-id>`。
5. 填充 `task.md`：背景、目标、功能、交互、视觉、约束、交付标准。
6. 按项目约定准备源码（如 `starter/`、`sources/<family>/<task-id>/` 等）、`assets/` 参考截图、`mock-data/` 数据。
7. 设计 `rubric.json`（10-20 个叶节点，覆盖六维度）。
8. 填写 `target_states.md` 与 `README.md`。
9. 如项目约定需要 `PROMPT.md`（例如 webdev-long-horizon），按项目模板生成。
10. 按项目约定运行校验脚本自检。

## 输出规范

- 任务必须迫使 agent 进入“实现 → 运行 → 观察 → 修复”闭环。
- 必须包含视觉参考截图（如项目需要）。
- 必须覆盖至少 4 类关键状态。
- 源码必须能本地启动。

## 禁止事项

- 不得在 task.md 或源码中泄露答案。
- 不得依赖外部登录、付费 API、不可控实时数据。
- 不得使用模糊视觉描述（如“高级、现代、美观”）。

## 项目特定说明

- 对于 `webdev-long-horizon` 项目，优先使用专门的 `webdev-incremental-task-creator` 或 `webdev-greenfield-task-creator` skill。
