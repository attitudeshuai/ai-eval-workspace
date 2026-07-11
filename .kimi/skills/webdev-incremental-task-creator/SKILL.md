---
name: webdev-incremental-task-creator
description: Create an incremental development task for the webdev-long-horizon project based on existing source code. Trigger when the user wants to create a new task that adds features to an existing web project in projects/webdev-long-horizon.
---

# Web Dev Incremental Task Creator

为 `projects/webdev-long-horizon` 创建基于现有源码的增量开发任务。

## 触发条件

当用户在 `webdev-long-horizon` 项目中要求创建新任务，且已有可运行源码、希望 agent 在其上新增功能时调用本技能。

## 输入信息

调用前需要确认：

- 任务标题
- 任务类别（参考 `projects/webdev-long-horizon/categories.json`）
- 难度（high / medium / low）
- Arena tags
- 源码目录路径
- 希望新增的功能描述（可选；如未提供，AI 可基于源码自动设计）

## 工作流程

1. 读取 `projects/webdev-long-horizon/categories.json` 确认类别与标签。
2. 读取用户提供的源码目录，分析现有功能、技术栈、项目结构。
3. 调用 `create_task.py --skip-starter` 生成任务骨架：
   ```bash
   python scripts/create_task.py \
     --project webdev-long-horizon \
     --title "<title>" \
     --category "<category>" \
     --difficulty "<difficulty>" \
     --arena-tags "<tags>" \
     --skip-starter
   ```
4. 将源码复制到 `projects/webdev-long-horizon/sources/<task-id>/`（目录名与任务 ID 一致）。
5. 生成 `task.md`：
   - 现有项目背景与已具备的功能
   - 需要新增的模块/页面/交互
   - 新增功能必须复用现有技术栈与数据约定
   - 约束、边界状态、交付标准
6. 生成 `rubric.json`（10-20 个叶节点，覆盖六维度）。
7. 生成 `target_states.md` 与 `README.md`。
8. 准备 `assets/` 参考截图、`mock-data/` 数据。
9. 运行校验：
   ```bash
   python scripts/validate_task.py \
     --allow-no-starter \
     projects/webdev-long-horizon/tasks/<task-id>
   ```

## 输出规范

- 任务必须迫使 agent 进入“实现 → 运行 → 观察 → 修复”闭环。
- 必须包含视觉参考截图。
- 必须覆盖至少 4 类关键状态。
- `sources/<task-id>/` 必须能本地启动。
- 不得在 `task.md` 或源码中泄露答案。
