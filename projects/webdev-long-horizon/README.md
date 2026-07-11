# 高难度 Web Dev 长程任务项目

本项目专注于评估 AI agent 在复杂 Web 前端开发场景下的真实工程能力。

## 项目专属内容

```text
projects/webdev-long-horizon/
├── config.toml          # 项目级配置
├── categories.json      # 项目专属任务分类与 Arena 标签
├── README.md            # 本文件（项目总览）
├── OPERATIONAL_WORKFLOW.md  # 完整实操流程
├── docs/                # 项目专属文档（可选）
├── templates/           # 项目专属模板（可覆盖全局模板）
├── rubrics/             # 共享 Rubric 模板
├── tasks/               # 任务仓库（元数据、Rubric、Prompt）
│   └── webdev-task-0001/
│       └── starter/     # 旧任务保留内置 starter
└── sources/             # 任务源码仓库（推荐，替代 task/starter）
    └── webdev-task-XXXX/
```

## 创建新任务

本项目使用源码与任务元数据分离管理。源码统一放到 `projects/webdev-long-horizon/sources/<task-id>/`，目录名与任务 ID 保持一致。

### 模式一：基于现有源码生成增量开发任务

已有可运行项目源码，希望 agent 在其基础上实现新功能。

```bash
python scripts/create_task.py \
  --project webdev-long-horizon \
  --title "为电商后台增加订单筛选与导出" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --difficulty "high" \
  --arena-tags "ui,e-commerce,visualize" \
  --skip-starter
```

### 模式二：根据需求生成从零开发任务

只有自然语言需求，任务要求 agent 从零实现完整项目。

```bash
python scripts/create_task.py \
  --project webdev-long-horizon \
  --title "支持拖拽看板的任务管理系统" \
  --category "交互型应用：可视化 / 数据看板" \
  --difficulty "high" \
  --arena-tags "ui,visualize,drag-drop" \
  --skip-starter
```

> 详细操作流程（复制源码、生成 task.md / rubric、校验、运行 SOTA、评估）见 [OPERATIONAL_WORKFLOW.md](./OPERATIONAL_WORKFLOW.md)。

## 校验项目

```bash
python scripts/validate_project.py --project webdev-long-horizon
```

## 质量闸门

本项目遵循工作台的 6 大质量闸门：可运行性、完整性、视觉可验收性、Rubric 有效性、可解性、无污染风险。

## 任务准入标准

- 非局部工程改动
- 至少 3 类相互影响的约束
- 视觉输入不可省略
- 浏览器工具是必要路径
- 至少 4 类关键状态
- SOTA 可解但不轻松
