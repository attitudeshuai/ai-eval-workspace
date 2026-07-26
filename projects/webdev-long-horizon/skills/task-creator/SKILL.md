---
name: task-creator
description: 'Create a high-quality long-horizon eval task in any project. Use when creating new tasks, designing task requirements, generating task skeletons, 创建任务, 设计任务需求, 生成任务骨架. For webdev-long-horizon, prefer webdev-greenfield-task-creator or webdev-incremental-task-creator.'
---

# Task Creator

在指定项目中创建符合规范的高难度长程评估任务。

## When to Use

- 用户要求创建新任务
- 需要设计任务需求
- 需要生成任务骨架

> 对于 `webdev-long-horizon` 项目，优先使用 `webdev-greenfield-task-creator` 或 `webdev-incremental-task-creator` skill。

## 前置确认

调用前需确认：
- **目标项目 ID**（如未指定，询问用户）

## Procedure

### 1. 读取项目约定

读取项目级文档确认分类体系与源码存放约定：
- `projects/<project-id>/AGENTS.md`
- `projects/<project-id>/SKILL.md`
- `projects/<project-id>/README.md`
- `projects/<project-id>/config.toml`
- `projects/<project-id>/categories.json`（如存在）

### 2. 生成任务骨架

```bash
python scripts/webdev-long-horizon/create_task.py --project <project-id> [options]
```

若项目是层级结构（如 webdev-long-horizon），增量任务传 `--parent <task-id>`。

### 3. 填充任务内容

- **task.md**：背景、目标、功能、交互、视觉、约束、交付标准
- **源码**：按项目约定准备（如 `starter/`、`sources/<family>/<task-id>/` 等）
- **assets/**：任务素材（参考截图放 `assets/reference/`，其他素材按类型分子目录）
- **mock-data/**：mock 数据

### 4. 设计评估体系

- **rubric.json**：10-20 个叶节点，覆盖六维度（功能完整性、视觉还原度、交互体验、代码质量、性能、边界状态）
- **target_states.md**：至少 4 类关键状态的预期表现
- **README.md**：任务概述

### 5. 校验

按项目约定运行校验脚本自检。

## 输出规范

- 任务必须迫使 agent 进入"实现 → 运行 → 观察 → 修复"闭环
- 必须包含视觉参考截图（如项目需要）
- 必须覆盖至少 4 类关键状态
- 源码必须能本地启动
- 如项目直接使用 `task.md` 作为 SOTA 提示词，确保包含完整源码位置、启动命令和交付要求

## 禁止事项

- 不得在 `task.md` 或源码中泄露答案
- 不得依赖外部登录、付费 API、不可控实时数据
- 不得使用模糊视觉描述（如"高级、现代、美观"）

## 与其他 Skill 的关系

- webdev-long-horizon 项目使用专用的 `webdev-greenfield-task-creator` 或 `webdev-incremental-task-creator`
- 任务创建后可运行 `task-reviewer` 进行质量审查
