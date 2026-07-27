# pairwise-gsb: 生图 Pairwise GSB 标注

评估 AI 生图模型在指令遵循、一致性、视觉效果三个维度的成对对比质量。

> **执行规则**：`docs/annotation-rules.md`（硬性规则，标注执行权威）  
> **原始底稿**：`docs/annotation-guidelines.md`（保持不动，勿修改）  
> **规则脑图**：`docs/0724答题规则.mm`（FreeMind/XMind 源文件）  
> **操作手册**：`docs/runbook.md`（对话指令 + 完整流程）  
> **主控 SKILL**：`skills/gsb-annotator/SKILL.md`（每日工作流编排）  
> **标注协议**：`skills/annotate-batch/SKILL.md`（单批次逐行协议）  
> **质量复核**：`skills/quality-audit/SKILL.md`（抽检复核）

## 目录结构

```
pairwise-gsb/
├── config.toml                       # 项目配置
├── README.md                         # 本文件
├── requirements.txt                  # Python 依赖
├── .gitignore                        # 项目级忽略规则
├── docs/
│   ├── annotation-guidelines.md      # 原始标注规则（底稿，勿修改）
│   ├── annotation-rules.md           # 硬性标注规则（执行权威）
│   ├── 0724答题规则.mm                # 规则脑图（FreeMind/XMind）
│   ├── demo-origin.xlsx              # 源数据 Excel 模板
│   └── runbook.md                    # 操作手册
├── skills/
│   ├── gsb-annotator/
│   │   └── SKILL.md                  # 主控 Skill（工作流编排）
│   ├── annotate-batch/
│   │   └── SKILL.md                  # 单批次标注协议（9 步）
│   └── quality-audit/
│       └── SKILL.md                  # 质量抽检复核协议
└── scripts/
    ├── _config.py                    # 统一配置读取
    ├── init_session.py               # 一键初始化 session
    ├── split_batches.py              # 切分 Excel 为批次
    ├── extract_images.py             # 提取嵌入图片 / 下载 URL 图片
    ├── validate_annotations.py       # 标注校验
    ├── merge_batches.py              # 合并批次结果并生成 summary
    ├── batch_status.py               # 查看批次状态
    └── manage_difficult_cases.py     # 疑难 case 管理

# 每日工作区（session/日期/批次 三层隔离）
sessions/pairwise-gsb/
└── <session>/                      # 如 0724
    └── YYYY-MM-DD/
        ├── original.xlsx
        ├── difficult-cases.xlsx    # 疑难 case 记录
        ├── difficult-cases-log.md  # 疑难 case 处理日志
        ├── batch-01/
        │   ├── metadata.json
        │   ├── input/items_行2-11.xlsx
        │   ├── images/（row_002_图片1.png 等）+ manifest.json
        │   └── output/annotated_行2-11.xlsx
        └── batch-02/ ...

# 最终产出（session/日期/批次）
deliverables/pairwise-gsb/
└── <session>/
    └── YYYY-MM-DD/
        ├── annotated-full_行1-14.xlsx  # 仅 序号/prompt/输出列，带下拉列表
        ├── summary.md
        ├── difficult-cases.xlsx    # 如有疑难 case
        ├── batch-01/annotated_行2-11.xlsx
        └── batch-02/ ...
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r projects/pairwise-gsb/requirements.txt
```

### 2. 一键初始化

```bash
python projects/pairwise-gsb/scripts/init_session.py 0724 2026-07-27 <原始Excel路径>
```

### 3. 查看批次状态

```bash
python projects/pairwise-gsb/scripts/batch_status.py sessions/pairwise-gsb/0724/2026-07-27
```

## 每日工作流

```bash
SESSION="0724"
DATE="2026-07-27"

# 1. 初始化（备份 + 切分 + 提取图片）
python projects/pairwise-gsb/scripts/init_session.py $SESSION $DATE <Excel路径>

# 2. 逐批标注（skills/annotate-batch/SKILL.md）

# 3. 校验
python projects/pairwise-gsb/scripts/validate_annotations.py \
    sessions/pairwise-gsb/$SESSION/$DATE/batch-01/

# 4. 疑难 case 管理
python projects/pairwise-gsb/scripts/manage_difficult_cases.py list \
    sessions/pairwise-gsb/$SESSION/$DATE

# 5. 交付（严格模式：未通过校验的批次拒绝合并）
python projects/pairwise-gsb/scripts/merge_batches.py \
    deliverables/pairwise-gsb/$SESSION/$DATE/ --strict
```

## 脚本速查

| 脚本 | 用途 | 用法 |
|------|------|------|
| `init_session.py` | 一键初始化 | `python scripts/init_session.py <session> <date> <xlsx>` |
| `split_batches.py` | 切分 Excel 为批次 | `python scripts/split_batches.py <src> <dest>` |
| `extract_images.py` | 提取嵌入图片 / 下载 URL | `python scripts/extract_images.py <xlsx> <out_dir>` |
| `validate_annotations.py` | 校验标注结果 | `python scripts/validate_annotations.py <batch_dir>` |
| `merge_batches.py` | 合并批次并生成 summary | `python scripts/merge_batches.py <dir> [--strict]` |
| `batch_status.py` | 查看批次状态 | `python scripts/batch_status.py <session_date_dir>` |
| `manage_difficult_cases.py` | 疑难 case 管理 | `python scripts/manage_difficult_cases.py <add|resolve|list> ...` |

## Skills 分工

| Skill | 文件 | 职责 |
|-------|------|------|
| **主控** | `skills/gsb-annotator/SKILL.md` | 每日工作流编排：切分→提取→调度→校验→疑难管理→交付 |
| **标注协议** | `skills/annotate-batch/SKILL.md` | 单批次 15 条的逐行 9 步标注协议 |
| **质量复核** | `skills/quality-audit/SKILL.md` | 对已完成批次进行 10% 抽检复核 |

## 任务列表

| 任务 ID | 标题 | 数据量 | 状态 |
|---------|------|:------:|------|
| gsb-task-sxw-01 | 第一批 GSB 标注（试标） | 200 条（30 条含图） | 试标完成 |
