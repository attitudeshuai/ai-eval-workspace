---
name: webdev-incremental-task-creator
description: 'Create an incremental development task for webdev-long-horizon based on existing source code. Use when adding features to existing web projects, creating child tasks from parent, 增量任务, 基于现有源码创建任务, incremental task.'
---

# Web Dev Incremental Task Creator

为 `projects/webdev-long-horizon` 创建基于现有源码的增量开发任务。

## When to Use

- 用户要求在现有项目上新增功能
- 已有可运行源码，希望 agent 在其上扩展
- 需要创建子任务（如 `{prefix}-01.01`，其中 `{prefix}` 为 `config.toml` 中 `task_prefix` 的值），继承父任务资产

> 如果只有自然语言需求、需要从零创建完整项目，请使用 `webdev-greenfield-task-creator` skill。

## 前置确认

调用前需确认：

- **任务标题**
- **任务类别**（参考 `projects/webdev-long-horizon/categories.json` 中的 `label`）
- **难度**：`high` / `medium` / `low`
- **Arena tags**（参考 `categories.json` 中的 `arena_tags`）
- **父任务 ID**（如 `{prefix}-01`）
- **新增功能描述**（可选；如未提供，AI 基于父任务源码自动设计）

## 目录结构约定

任务按家族分组，子任务使用点分 ID：

```text
projects/webdev-long-horizon/
├── tasks/
│   └── {prefix}-01/
│       ├── {prefix}-01/          # 顶层基础任务
│       ├── {prefix}-01.01/       # 基于 01 的增量任务
│       └── {prefix}-01.02/       # 另一个增量任务
└── sources/
    └── {prefix}-01/
        ├── {prefix}-01/          # 顶层任务源码
        ├── {prefix}-01.01/       # 增量任务源码（基于 01）
        └── {prefix}-01.02/       # 增量任务源码（基于 01）
```

> `{prefix}` 为 `config.toml` 中 `task_prefix` 的值（默认 `webdev-task-sxw`），下同。

## Procedure

### 1. 分析父任务

读取父任务源码目录，分析：
- 现有功能范围
- 技术栈（React/Vue/Vanilla、Tailwind/CSS、状态管理等）
- 项目结构与组件层级
- 数据约定（API 格式、mock 数据结构）

### 2. 读取分类体系

读取 `projects/webdev-long-horizon/categories.json` 确认可用的类别 label 与 arena tags。

### 3. 创建任务骨架（一键完成）

```bash
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "<title>" \
  --category "<category-label>" \
  --difficulty "<difficulty>" \
  --arena-tags "<tags>" \
  --prompt-type "前端" \
  --skip-starter \
  --parent <parent-task-id>
```
{prefix}
> `--category` 使用 `categories.json` 中的中文 `label`，如 `"电商 / 交易应用：O2O 服务 / 聚合平台"`。
> 子任务自动生成层级 ID，如 `{prefix}-01.01`。

此命令自动完成：
1. 创建任务目录 `tasks/<family>/<task-id>/`，生成 `task.md`、`metadata.json`、`rubric.json`、`README.md`、`target_states.md` 骨架
2. 将父任务源码复制到 `sources/<family>/<task-id>/`，作为 baseline
3. 复制父任务 `mock-data/` 到任务目录，同步到 `sources/<family>/<task-id>/mock-data/`
4. 创建 `assets/`、`screenshots/` 目录，`metadata.json` 写入 `parent_tasks`

### 4. 填充 task.md

`task.md` 必须包含：
- 说明本任务基于哪个父任务源码进行增量开发
- 现有项目背景与已具备的功能
- 需要新增的模块/页面/交互（具体、可验证）
- **新增功能必须复用现有技术栈与数据约定**
- 约束、边界状态、交付标准

`task.md` 需可直接作为 SOTA 提示词，明确告知 agent 源码位置和完整交付要求。

### 5. 完善评估资产

- `rubric.json`：10-20 个叶节点，覆盖六维度
- `target_states.md`：关键状态的预期表现
- `README.md`：任务概述

### 6. 补充 mock-data/

新增功能所需的 mock 数据（如新增 `orders.json`），确保：
- 任务目录 `mock-data/` 与 `sources/<family>/<task-id>/mock-data/` 保持一致
- 数据结构与父任务兼容

### 7. 准备 assets/

- 参考截图放 `assets/reference/`（`desktop.png`、`mobile.png`、`empty_state.png`、`interaction_state.png`）
- 其他素材按类型分目录

### 8. 校验

```bash
python scripts/webdev-long-horizon/validate_task.py \
  --allow-no-starter \
  <task-id>
```

### 9. 本地验证源码可启动

```bash
cd projects/webdev-long-horizon/sources/<family>/<task-id>
npm install
npm run dev
```

## 输出规范

- 任务必须迫使 agent 进入"实现 → 运行 → 观察 → 修复"闭环
- 必须包含视觉参考截图
- 必须覆盖至少 4 类关键状态
- `sources/<family>/<task-id>/` 必须能本地启动
- `task.md` 必须明确源码位置、启动命令、交付要求

## 禁止事项

- 不得在 `task.md`、源码或提示词中泄露答案
- 不得依赖外部登录、付费 API、不可控实时数据
- 不得使用模糊视觉描述
- 新增功能不得破坏父任务已有功能

## 与其他 Skill 的关系

- 本 skill 只负责生成任务资产；远程运行由 `webdev-task-packer` skill 处理
- 如需从零创建全新项目任务，使用 `webdev-greenfield-task-creator` skill
- 任务创建后可运行 `task-reviewer` 进行质量审查
