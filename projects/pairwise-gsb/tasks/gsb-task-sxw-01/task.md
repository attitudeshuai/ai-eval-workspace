# gsb-task-sxw-01: AI 生图 Pairwise GSB 标注（第一批）

## 任务概述

对 200 组 AI 生成图片进行 Pairwise GSB（Good/Same/Bad）标注。每组包含 prompt + 图片1 + 图片2（部分含输入图/参考图），标注员需在三个维度（指令遵循、一致性、视觉效果）上判定胜负并给出归因标签和 reason。

## 任务类型分布

| 类型 | 数量 | 说明 |
|------|:----:|------|
| T2I（文生图） | 11 条 | 无输入图，不判断一致性 |
| 图片编辑 | 12 条 | 有输入图，需判断一致性 |
| 参考生成 | 7 条 | 有参考图，仅判断指定参考特征 |

## 数据文件

- **输入数据**: `data/items.xlsx` — 200 条 prompt + 30 组嵌入图片
- **导出图片**: `images/` — 80 张从 Excel 提取的 PNG
- **标注输出**: `output/annotated.xlsx` — 30 条已标注结果

## 标注规范

详见项目根目录 `SKILL.md` 及 `docs/annotation-guidelines.md`。

## 目录结构

```
gsb-task-sxw-01/
├── metadata.json       # 任务元数据
├── task.md             # 本文件
├── README.md           # 任务说明
├── data/
│   └── items.xlsx      # 标注数据（200条）
├── images/             # 导出图片（80张PNG）
├── output/
│   └── annotated.xlsx  # 标注结果
└── scripts/
    └── annotate.py     # 标注脚本
```
