---
name: webdev-greenfield-task-creator
description: Create a greenfield development task for the webdev-long-horizon project from a natural language requirement. Trigger when the user wants to create a new task that requires building a complete web project from scratch in projects/webdev-long-horizon.
---
# Web Dev Greenfield Task Creator

为 `projects/webdev-long-horizon` 创建从零开发的完整项目任务。

## 触发条件

当用户在 `webdev-long-horizon` 项目中要求创建新任务，且用户已提供 README.md 和 assets/ 材料时调用本技能。

## 用户提供的材料

对于 0→1（greenfield）项目，用户会在任务目录中提前放置：

```
tasks/{prefix}-XX/{prefix}-XX/
├── README.md      # 项目说明（技术栈、启动方式、功能列表、项目结构）
└── assets/        # 任务素材（reference/、screenshots/、icons/ 等）
```

`README.md` 包含技术栈、启动命令、测试账号、功能列表、项目结构。AI 基于此生成完整任务资产。

## 输入信息

调用前需要确认：

- 任务类别（参考 `projects/webdev-long-horizon/categories.json` 中的 `label`）
- 难度（high / medium / low）
- Arena tags（参考 `categories.json` 中的 `arena_tags`）

## 工作流程

1. 确认用户已在 `tasks/{prefix}-XX/{prefix}-XX/` 下放置 `README.md` 和 `assets/`。
2. 读取 `README.md`，提取技术栈、功能列表、启动方式、项目结构。
3. 读取 `categories.json` 确认类别 label 与 arena tags。
4. 任务目录名即为 task_id（如 `{prefix}-02`），无需运行 `create_task.py`。
5. 生成 `metadata.json`（task_id、title、category_tags、difficulty 等）。
6. 生成 `task.md`（基于 README 扩展为完整 SOTA 提示词，含起始项目、功能模块、交互视觉要求、约束、交付标准）。
7. 生成 `rubric.json`（10-20 个叶节点，覆盖六维度）。
8. 生成 `target_states.md`（至少 4 类关键状态，与 assets/reference/ 截图对应）。
9. 在用户提供的 README.md 基础上补充快速导航和验收标准引用。
10. 源码处理：
    - **用户提供源码**：放到 `sources/<task-id>/<task-id>/`
    - **AI 生成 starter**：基于 README 技术栈描述生成初始项目
11. 校验：
    ```bash
    python scripts/webdev-long-horizon/validate_task.py --allow-no-starter {prefix}-02
    ```
12. 按 README 启动命令验证项目可运行。

## 输出规范

- 任务必须迫使 agent 进入“实现 → 运行 → 观察 → 修复”闭环。
- 必须包含视觉参考截图。
- 必须覆盖至少 4 类关键状态。
- 源码必须能本地启动。
- `task.md` 必须明确源码位置、启动命令、交付要求。
- 不得在 `task.md`、源码或提示词中泄露答案。

## 与远程运行的关系

本技能只负责生成任务资产。若用户要将提示词和源码上传到 remote 用 codex 直接运行，后续由 `webdev-task-packer` skill 处理打包与上传。
