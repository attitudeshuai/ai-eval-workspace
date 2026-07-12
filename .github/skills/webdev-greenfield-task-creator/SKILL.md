---
name: webdev-greenfield-task-creator
description: 'Create a greenfield (from-scratch) development task for webdev-long-horizon. Use when creating new tasks from natural language requirements, building complete web projects from scratch, 从零创建任务, 全新项目任务, greenfield task.'
---

# Web Dev Greenfield Task Creator

为 `projects/webdev-long-horizon` 创建从零开发的完整项目任务。

## When to Use

- 用户要求创建全新任务（无现有源码基础）
- 只有自然语言需求描述，需要 agent 从零实现完整项目
- 需要生成新的顶层任务 ID（如 `{prefix}-02`，其中 `{prefix}` 为 `config.toml` 中 `task_prefix` 的值）

> 如果已有可运行源码、希望在其上新增功能，请使用 `webdev-incremental-task-creator` skill。

## 前置确认

调用前需确认：

- **任务标题**（从用户提供的 `README.md` 中提取）
- **任务类别**（参考 `projects/webdev-long-horizon/categories.json` 中的 `label`）
- **难度**：`high` / `medium` / `low`
- **Arena tags**（参考 `categories.json` 中的 `arena_tags`）

## 用户提供的材料

对于 0→1（greenfield）项目，用户会在任务目录中提前放置两种材料：

```
tasks/{prefix}-XX/{prefix}-XX/
├── README.md      # 项目说明（技术栈、启动方式、功能列表、项目结构）
└── assets/        # 任务素材
    ├── reference/     # 参考截图（desktop.png、mobile.png 等）
    ├── screenshots/   # 示例截图
    ├── icons/         # 图标素材（可选）
    ├── fonts/         # 字体文件（可选）
    └── images/        # 示例图片（可选）
```

`README.md` 是核心输入，包含：
- 技术栈（前端框架、后端、数据库等）
- 快速启动命令（Docker、npm 等）
- 测试账号
- 功能列表
- 项目目录结构

AI 需要基于 README.md 和 assets/ 来生成完整的任务资产。

## 目录结构约定

顶层任务 ID 格式：`{prefix}-01`, `{prefix}-02`, ...（`{prefix}` 由 `config.toml` 的 `task_prefix` 控制，默认 `webdev-task-sxw`）

```text
projects/webdev-long-horizon/
├── tasks/
│   └── {prefix}-02/
│       └── {prefix}-02/          # 顶层从零开发任务
└── sources/
    └── {prefix}-02/
        └── {prefix}-02/          # 顶层任务源码
```

## Procedure

### 1. 确认任务目录

用户已在 `tasks/{prefix}-XX/{prefix}-XX/` 下放置了 `README.md` 和 `assets/`。确认这两个存在。

### 2. 读取用户提供的 README.md

从 README.md 中提取关键信息：
- **技术栈**：前端框架、后端、数据库、构建工具
- **启动方式**：Docker compose、npm、maven 等
- **功能列表**：每个模块的核心功能
- **项目结构**：前后端目录划分
- **测试账号**：如有

### 3. 读取分类体系

读取 `projects/webdev-long-horizon/categories.json` 确认可用的类别 label 与 arena tags。

### 4. 确认任务 ID

任务目录名即为 task_id（如 `{prefix}-02`），无需运行 `create_task.py` 重新生成。

### 5. 生成 metadata.json

```json
{
  "task_id": "{prefix}-02",
  "title": "<从README提取>",
  "category_tags": ["..."],
  "arena_tags": ["..."],
  "prompt_type": "前端",  // 或"全栈"
  "difficulty": "high",
  ...
}
```

### 6. 生成 task.md（核心步骤）

基于 README.md 的技术栈和功能列表，扩展为完整的 SOTA 提示词。必须包含：

- **起始项目**：说明源码位置、启动命令、项目结构
- **背景与目标**：从 README 功能列表扩展为完整的业务场景
- **功能要求**：将功能列表拆分为模块，每个模块包含具体验收标准
- **交互要求**：动画、过渡、hover 效果等
- **视觉要求**：引用 `assets/reference/` 中的截图，给出设计规范
- **约束条件**：技术栈约束、禁止事项
- **交付标准**：启动、截图、测试 checklist

`task.md` 直接作为 SOTA 提示词使用。

### 7. 设计 rubric.json

10-20 个叶节点，覆盖六维度：
1. 功能完整性
2. 视觉还原度
3. 交互体验
4. 代码质量
5. 边界状态处理
6. 测试与证据

### 8. 生成 target_states.md

描述至少 4 类关键状态的预期表现，与 `assets/reference/` 中的截图一一对应。

### 9. 完善 README.md

在用户提供的 README.md 基础上补充：
- 快速导航链接
- 验收标准引用
- 技术约束说明

### 10. 处理源码

Greenfield 任务**无需本地源码**。codex 会在远端从零构建整个项目。`upload_to_remote.py` 已支持无 source 目录的场景，仅上传 task.md + assets + tests。

### 11. 校验

```bash
python scripts/webdev-long-horizon/validate_task.py \
  --allow-no-starter \
  {prefix}-02
```

### 12. 本地验证（如适用）

按 README 中的启动命令验证项目可运行。

## 输出规范

- 任务必须迫使 agent 进入"实现 → 运行 → 观察 → 修复"闭环
- 必须包含视觉参考截图
- 必须覆盖至少 4 类关键状态
- 源码必须能本地启动
- `task.md` 必须明确源码位置、启动命令、交付要求

## 禁止事项

- 不得在 `task.md`、源码或提示词中泄露答案
- 不得依赖外部登录、付费 API、不可控实时数据
- 不得使用模糊视觉描述

## 与其他 Skill 的关系

- 本 skill 只负责生成任务资产；远程运行由 `webdev-task-packer` skill 处理
- 如需在现有源码基础上新增功能，使用 `webdev-incremental-task-creator` skill
- 任务创建后可运行 `task-reviewer` 进行质量审查
