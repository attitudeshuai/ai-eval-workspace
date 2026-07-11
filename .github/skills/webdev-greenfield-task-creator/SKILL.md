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

- **任务标题**
- **任务类别**（参考 `projects/webdev-long-horizon/categories.json` 中的 `label`）
- **难度**：`high` / `medium` / `low`
- **Arena tags**（参考 `categories.json` 中的 `arena_tags`）
- **详细需求描述**
- **源码提供方式**：用户提供 / AI 基于模板生成 starter

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

### 1. 读取分类体系

读取 `projects/webdev-long-horizon/categories.json` 确认可用的类别 label 与 arena tags。

### 2. 生成任务骨架

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

> `--category` 使用 `categories.json` 中的中文 `label`，如 `"电商 / 交易应用：O2O 服务 / 聚合平台"`。
> 不传 `--parent` 时生成顶层任务 ID。

### 3. 填充 task.md

`task.md` 必须包含：
- 项目背景与应用场景
- 核心功能需求（迫使 agent 进入"实现→运行→观察→修复"闭环）
- 视觉与交互要求（具体、可验证，禁止模糊描述如"高级、现代、美观"）
- 技术约束（必须使用的框架、库、API 限制）
- 边界状态处理要求（至少 4 类关键状态）
- 交付标准（安装依赖、运行、截图、测试命令）

`task.md` 需可直接作为 SOTA 提示词，明确告知 agent：
- 源码位于 `./source` 或当前目录
- 完整交付要求

### 4. 设计 rubric.json

10-20 个叶节点，覆盖六维度：
1. 功能完整性
2. 视觉还原度
3. 交互体验
4. 代码质量
5. 性能
6. 边界状态处理

### 5. 完善 target_states.md 与 README.md

- `target_states.md`：描述至少 4 类关键状态的预期表现
- `README.md`：任务概述与快速导航

### 6. 准备 assets/ 与 mock-data/

- 参考截图放 `assets/reference/`（`desktop.png`、`mobile.png`、`empty_state.png`、`interaction_state.png`）
- 图标、字体、示例图片按需放 `assets/icons/`、`assets/fonts/`、`assets/images/`
- Mock 数据放 `mock-data/`

### 7. 处理源码

- **用户提供 starter**：放到 `sources/<task-id>/<task-id>/`
- **AI 生成 starter**：基于 `templates/starter/` 生成初始项目，放到 `tasks/<task-id>/<task-id>/starter/`

### 8. 校验

```bash
# 外部 source 模式
python scripts/webdev-long-horizon/validate_task.py \
  --allow-no-starter \
  <task-id>

# 内置 starter 模式
python scripts/webdev-long-horizon/validate_task.py \
  <task-id>
```

### 9. 本地验证源码可启动

```bash
cd projects/webdev-long-horizon/sources/<task-id>/<task-id>
npm install
npm run dev
```

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
