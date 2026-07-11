---
name: webdev-greenfield-task-creator
description: Create a greenfield development task for the webdev-long-horizon project from a natural language requirement. Trigger when the user wants to create a new task that requires building a complete web project from scratch in projects/webdev-long-horizon.
---

# Web Dev Greenfield Task Creator

为 `projects/webdev-long-horizon` 创建从零开发的完整项目任务。

## 触发条件

当用户在 `webdev-long-horizon` 项目中要求创建新任务，且只有自然语言需求、需要 agent 从零实现完整项目时调用本技能。

## 输入信息

调用前需要确认：

- 任务标题
- 任务类别（参考 `projects/webdev-long-horizon/categories.json`）
- 难度（high / medium / low）
- Arena tags
- 详细需求描述
- 源码提供方式（用户提供 / AI 生成 starter）

## 工作流程

1. 读取 `projects/webdev-long-horizon/categories.json` 确认类别与标签。
2. 调用 `create_task.py --skip-starter` 生成任务骨架：
   ```bash
   python scripts/create_task.py \
     --project webdev-long-horizon \
     --title "<title>" \
     --category "<category>" \
     --difficulty "<difficulty>" \
     --arena-tags "<tags>" \
     --skip-starter
   ```
3. 生成完整项目需求的 `task.md`：背景、目标、功能、交互、视觉、约束、交付标准。
4. 生成 `rubric.json`（10-20 个叶节点，覆盖六维度）。
5. 生成 `target_states.md` 与 `README.md`。
6. 准备 `assets/` 参考截图、`mock-data/` 数据。
7. 处理源码：
   - 用户提供：放到 `projects/webdev-long-horizon/sources/<task-id>/`
   - AI 生成：放到 `projects/webdev-long-horizon/tasks/<task-id>/starter/`
8. 运行校验：
   - 外部 source：
     ```bash
     python scripts/validate_task.py \
       --allow-no-starter \
       projects/webdev-long-horizon/tasks/<task-id>
     ```
   - 内置 starter：
     ```bash
     python scripts/validate_task.py \
       projects/webdev-long-horizon/tasks/<task-id>
     ```

## 输出规范

- 任务必须迫使 agent 进入“实现 → 运行 → 观察 → 修复”闭环。
- 必须包含视觉参考截图。
- 必须覆盖至少 4 类关键状态。
- 源码必须能本地启动。
- 不得在 `task.md` 或源码中泄露答案。
