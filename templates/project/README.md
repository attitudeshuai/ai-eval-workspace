# {{project_name}}

{{description}}

## 项目专属内容

```text
projects/{{project_id}}/
├── config.toml          # 项目级配置
├── README.md            # 本文件
├── docs/                # 项目专属文档（可选）
├── templates/           # 项目专属模板（可覆盖全局模板）
├── rubrics/             # 共享 Rubric 模板
└── tasks/               # 任务仓库
```

## 创建新任务

```bash
python scripts/create_task.py \
  --project {{project_id}} \
  --title "任务标题" \
  --category "类目" \
  --arena-tags "tag1,tag2"
```

## 校验项目

```bash
python scripts/validate_project.py --project {{project_id}}
```

## 质量闸门

本项目遵循工作台的 6 大质量闸门：可运行性、完整性、可验收性、Rubric 有效性、可解性、无污染风险。
