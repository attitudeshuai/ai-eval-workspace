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
- 任务类别（参考 `projects/webdev-long-horizon/categories.json` 中的 `label`）
- 难度（high / medium / low）
- Arena tags（参考 `projects/webdev-long-horizon/categories.json` 中的 `arena_tags`）
- 详细需求描述
- 源码提供方式（用户提供 / AI 生成 starter）

## 目录结构约定

本项目采用层级目录结构：

```text
projects/webdev-long-horizon/
├── tasks/
│   └── webdev-task-02/
│       └── webdev-task-02/          # 顶层从零开发任务
└── sources/
    └── webdev-task-02/
        └── webdev-task-02/          # 顶层任务源码
```

顶层任务 ID：`webdev-task-01`, `webdev-task-02`, ...

## 工作流程

1. 读取 `projects/webdev-long-horizon/categories.json` 确认类别 label 与 arena tags。
2. 调用 `create_task.py --skip-starter` 生成顶层任务骨架：
   ```bash
   python scripts/webdev-long-horizon/create_task.py \
     --project webdev-long-horizon \
     --title "<title>" \
     --category "<category-label>" \
     --difficulty "<difficulty>" \
     --arena-tags "<tags>" \
     --prompt-type "前端" \
     --skip-starter
   ```
   > `--category` 请使用 `categories.json` 中的中文 `label`。
   > 不传 `--parent` 时，会生成顶层任务 ID，例如 `webdev-task-02`。
3. 生成完整项目需求的 `task.md`：背景、目标、功能、交互、视觉、约束、交付标准。
4. 生成 `rubric.json`（10-20 个叶节点，覆盖六维度）。
5. 生成 `target_states.md` 与 `README.md`。
6. 准备 `assets/` 参考截图、`mock-data/` 数据。
7. 处理源码：
   - **用户提供 starter**：放到 `projects/webdev-long-horizon/sources/<task-id>/<task-id>/`。
   - **AI 生成 starter**：基于 `projects/webdev-long-horizon/templates/starter/` 生成初始项目，放到 `projects/webdev-long-horizon/tasks/<task-id>/<task-id>/starter/`。
8. 生成 `PROMPT.md`：
   - 基于 `task.md` 与项目模板 `projects/webdev-long-horizon/templates/PROMPT.md`
   - 明确告知 agent 源码位于 `./source` 或当前目录
   - 包含完整交付要求
   ```bash
   python scripts/webdev-long-horizon/compose_prompt.py \
     --project webdev-long-horizon \
     --task <task-id>
   ```
   > 若 `compose_prompt.py` 不存在，则手动复制 `templates/PROMPT.md` 并将 `{{task_md}}` 替换为 `task.md` 内容。
9. 运行校验：
   - 外部 source：
     ```bash
     python scripts/webdev-long-horizon/validate_task.py \
       --allow-no-starter \
       webdev-task-02
     ```
   - 内置 starter：
     ```bash
     python scripts/webdev-long-horizon/validate_task.py \
       webdev-task-02
     ```
10. （推荐）本地验证源码可启动：
    ```bash
    cd projects/webdev-long-horizon/sources/webdev-task-02/webdev-task-02
    # 或 cd projects/webdev-long-horizon/tasks/webdev-task-02/webdev-task-02/starter
    npm install
    npm run dev
    ```

## 输出规范

- 任务必须迫使 agent 进入“实现 → 运行 → 观察 → 修复”闭环。
- 必须包含视觉参考截图。
- 必须覆盖至少 4 类关键状态。
- 源码必须能本地启动。
- `PROMPT.md` 必须明确源码位置、启动命令、交付要求。
- 不得在 `task.md`、源码或 `PROMPT.md` 中泄露答案。

## 与远程运行的关系

本技能只负责生成任务资产。若用户要将提示词和源码上传到 remote 用 codex 直接运行，后续由 `webdev-task-packer` skill 处理打包与上传。
