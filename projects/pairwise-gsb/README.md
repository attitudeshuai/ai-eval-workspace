# pairwise-gsb: 生图 Pairwise GSB 标注

评估 AI 生图模型在指令遵循、一致性、视觉效果三个维度的成对对比质量。

## 目录结构

```
pairwise-gsb/
├── config.toml                 # 项目配置（task_prefix=gsb-task-sxw）
├── SKILL.md                    # GSB 标注 Skill（AI Agent 执行规范）
├── docs/
│   └── annotation-guidelines.md  # 标注规则详细文档
├── rubrics/                    # 评分标准
├── templates/
│   └── task/                   # 任务模板（空 Excel 表头等）
├── tasks/                      # 各轮标注任务
│   └── gsb-task-sxw-01/       # 第 1 批（200条）
│       ├── metadata.json
│       ├── task.md
│       ├── data/items.xlsx     # 输入数据
│       ├── images/             # 导出图片
│       ├── output/             # 标注结果
│       └── scripts/            # 标注脚本
├── sources/                    # 参考来源
└── README.md                   # 本文件
```

## 任务列表

| 任务 ID | 标题 | 数据量 | 状态 |
|---------|------|:------:|------|
| gsb-task-sxw-01 | 第一批 GSB 标注 | 200 条（30 条含图） | 试标完成 |

## 快速开始

```bash
# 1. 查看任务
cat tasks/gsb-task-sxw-01/task.md

# 2. 运行标注脚本
python tasks/gsb-task-sxw-01/scripts/annotate.py

# 3. 查看结果
# 输出: tasks/gsb-task-sxw-01/output/annotated.xlsx
```

## 新增任务

```bash
# 复制模板
cp -r templates/task tasks/gsb-task-sxw-02

# 放入新数据 Excel
cp new-batch.xlsx tasks/gsb-task-sxw-02/data/items.xlsx

# 更新 metadata.json
```
