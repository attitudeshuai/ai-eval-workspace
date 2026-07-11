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
- 任务类别（参考 `projects/webdev-long-horizon/categories.json` 中的 `label`）
- 难度（high / medium / low）
- Arena tags（参考 `projects/webdev-long-horizon/categories.json` 中的 `arena_tags`）
- 父任务 ID（基于哪个现有任务做增量）
- 希望新增的功能描述（可选；如未提供，AI 可基于源码自动设计）

## 目录结构约定

本项目采用层级目录结构，同一任务家族放在同一个父目录下：

```text
projects/webdev-long-horizon/
├── tasks/
│   └── webdev-task-01/
│       ├── webdev-task-01/          # 顶层基础任务
│       ├── webdev-task-01.01/       # 基于 01 的增量任务
│       └── webdev-task-01.02/
└── sources/
    └── webdev-task-01/
        ├── webdev-task-01/          # 顶层基础任务源码
        ├── webdev-task-01.01/       # 增量任务源码
        └── webdev-task-01.02/
```

任务 ID 格式：
- 顶层任务：`webdev-task-01`, `webdev-task-02`, ...
- 子任务：`webdev-task-01.01`, `webdev-task-01.02`, ...

## 工作流程

1. 读取 `projects/webdev-long-horizon/categories.json` 确认类别 label 与 arena tags。
2. 读取父任务源码目录，分析现有功能、技术栈、项目结构。
3. 调用 `create_task.py --skip-starter --parent <parent-task-id>` 生成任务骨架：
   ```bash
   python scripts/create_task.py \
     --project webdev-long-horizon \
     --title "<title>" \
     --category "<category-label>" \
     --difficulty "<difficulty>" \
     --arena-tags "<tags>" \
     --prompt-type "前端" \
     --skip-starter \
     --parent webdev-task-01
   ```
   > `--category` 请使用 `categories.json` 中的中文 `label`，例如 `"电商 / 交易应用：O2O 服务 / 聚合平台"`。
   > 子任务会自动生成层级 ID，例如 `webdev-task-01.01`。
4. 将父任务源码复制到 `projects/webdev-long-horizon/sources/<family>/<task-id>/`，作为新任务的 baseline：
   ```bash
   cp -r projects/webdev-long-horizon/sources/webdev-task-01/webdev-task-01/* \
     projects/webdev-long-horizon/sources/webdev-task-01/webdev-task-01.01/
   ```
   - 在 `metadata.json` 中增加 `parent_tasks` 字段，记录父任务 ID，例如：
     ```json
     "parent_tasks": ["webdev-task-01"]
     ```
   - 在 `task.md` 背景中说明本任务基于哪个任务的源码进行增量开发。
5. 生成 `task.md`：
   - 现有项目背景与已具备的功能
   - 需要新增的模块/页面/交互
   - 新增功能必须复用现有技术栈与数据约定
   - 约束、边界状态、交付标准
6. 生成 `rubric.json`（10-20 个叶节点，覆盖六维度）。
7. 生成 `target_states.md` 与 `README.md`。
8. 准备 `assets/` 参考截图、`mock-data/` 数据。
   - 如 mock 数据需要被 agent 在源码中直接读取，建议同时复制一份到 `sources/<family>/<task-id>/mock-data/`。
9. 生成 `PROMPT.md`：
   - 基于 `task.md` 与项目模板 `projects/webdev-long-horizon/templates/PROMPT.md`
   - 明确告知 agent 源码位于 `./source` 或当前目录
   - 包含交付要求：安装依赖、运行、截图、测试
   ```bash
   python scripts/compose_prompt.py \
     --project webdev-long-horizon \
     --task <task-id>
   ```
   > 若 `compose_prompt.py` 不存在，则手动复制 `templates/PROMPT.md` 并将 `{{task_md}}` 替换为 `task.md` 内容。
10. 运行校验：
    ```bash
    python scripts/validate_task.py \
      --allow-no-starter \
      webdev-task-01.01
    ```
    > 可直接用 task_id，脚本会自动在层级目录中查找。
11. （推荐）本地验证源码可启动：
    ```bash
    cd projects/webdev-long-horizon/sources/webdev-task-01/webdev-task-01.01
    npm install
    npm run dev
    ```

## 输出规范

- 任务必须迫使 agent 进入“实现 → 运行 → 观察 → 修复”闭环。
- 必须包含视觉参考截图。
- 必须覆盖至少 4 类关键状态。
- `sources/<family>/<task-id>/` 必须能本地启动。
- `PROMPT.md` 必须明确源码位置、启动命令、交付要求。
- 不得在 `task.md`、源码或 `PROMPT.md` 中泄露答案。

## 与远程运行的关系

本技能只负责生成任务资产。若用户要将提示词和源码上传到 remote 用 codex 直接运行，后续由 `webdev-task-packer` skill 处理打包与上传。
