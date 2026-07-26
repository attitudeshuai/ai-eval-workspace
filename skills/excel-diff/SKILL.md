---
name: excel-diff
description: "Use when: 需要对比两个 Excel/CSV 文件的指定列，找出仅在一个文件中存在的数据。常用于核对 prompt-export 与主 export 的 Trae Session ID 是否一致。"
---

# Excel/CSV 差异对比 Skill

对比两个 Excel/CSV 文件的指定列，快速找出在一个文件中存在、但在另一个文件中缺失的数据。

## 适用场景

- 核对两份 Excel/CSV 数据的差异
- 找出"已提交"但"本地未记录"的条目
- 对比 Trae Session ID、订单号、用户ID 等唯一标识列
- 在 `skill-export-prompt` 导出完成后，校验 prompt-export 与主 export 的 Session ID 是否一致

## 依赖安装

```bash
pip install pandas openpyxl
```

## 配置文件

本技能优先通过 JSON 配置文件读取对比路径。默认配置文件：

```text
{WORKSPACE_ROOT}\scripts\excel-diff-config.json
```

配置文件格式（路径相对于 `{WORKSPACE_ROOT}`，即项目根目录）：

```json
{
  "file_a": "03.output-files\\excel list\\csv-{batch}-prompt-export.xlsx",
  "file_b": "03.output-files\\excel list\\csv-{batch}-export.xlsx",
  "column": "Trae Session ID",
  "output": "03.output-files\\excel list\\csv-{batch}-diff.xlsx"
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `file_a` | 源文件（可能包含缺失数据的文件） | - |
| `file_b` | 基准文件（要对比的目标文件） | - |
| `column` | 要对比的列名 | `Trae Session ID` |
| `output` | 差异结果导出路径 | 不导出 |

## 使用方法

### 1. 使用配置文件运行（推荐）

```bash
python skills\excel-diff\compare_excel.py --config scripts\excel-diff-config.json
```

### 2. 命令行直接运行

**最简用法**（默认对比 `Trae Session ID` 列）：

```bash
python skills\excel-diff\compare_excel.py 已提交.xlsx local.xlsx
```

**指定对比列**：

```bash
python skills\excel-diff\compare_excel.py 已提交.xlsx local.xlsx -c "订单号"
```

**导出差异结果**：

```bash
python skills\excel-diff\compare_excel.py 已提交.xlsx local.xlsx -o 差异结果.xlsx
```

### 3. 在 Python 中调用

```python
from compare_excel import compare_excel

# 对比 Trae Session ID，打印详情
missing = compare_excel("已提交.xlsx", "local.xlsx")

# 指定其他列
missing = compare_excel("A.xlsx", "B.xlsx", column="订单号")

# 不打印，只获取结果 DataFrame
missing = compare_excel("A.xlsx", "B.xlsx", verbose=False)
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `file_a` | 源文件（可能包含缺失数据的文件） | - |
| `file_b` | 基准文件（要对比的目标文件） | - |
| `-c, --column` | 要对比的列名 | `Trae Session ID` |
| `-o, --output` | 差异结果导出路径 | 不导出 |
| `-q, --quiet` | 静默模式，只输出数量 | `False` |
| `--config` | JSON 配置文件路径 | 无 |

## 输出示例

```
==================================================
文件 A: csv-solo-0601-app12-15-prompt-export.xlsx  (32 行)
文件 B: csv-solo-0601-app12-15-export.xlsx  (32 行)
对比列: Trae Session ID
==================================================
仅在 'csv-solo-0601-app12-15-prompt-export.xlsx' 中存在、在 'csv-solo-0601-app12-15-export.xlsx' 中缺失的数量: 0

✓ 所有数据都在文件 B 中存在，无缺失。
```

## 注意事项

1. 对比是**逐条精确匹配**（字符串完全相等），不是模糊匹配
2. 空值会被自动过滤，不参与对比
3. 行号提示中的 `+2` 偏移量对应 Excel 实际行号（含表头，且从 1 开始计数）
4. 支持 `.xlsx`、`.xls`、`.csv` 三种格式，输出格式由 `output` 文件扩展名决定
