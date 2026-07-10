# 高难度 Web Dev 长程任务项目

本项目专注于评估 AI agent 在复杂 Web 前端开发场景下的真实工程能力。

## 项目专属内容

```text
projects/webdev-long-horizon/
├── config.toml          # 项目级配置
├── README.md            # 本文件
├── docs/                # 项目专属文档（可选）
├── templates/           # 项目专属模板（可覆盖全局模板）
├── rubrics/             # 共享 Rubric 模板
└── tasks/               # 任务仓库
    └── webdev-task-0001/
```

## 创建新任务

```bash
python scripts/create_task.py \
  --project webdev-long-horizon \
  --title "复杂 O2O 服务聚合平台" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --arena-tags "ui,map,e-commerce,visualize"
```

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
