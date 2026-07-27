---
name: gsb-annotator
description: 'AI 生图 Pairwise GSB 标注。根据 prompt、输入图/参考图和两张生成图，按指令遵循/一致性/视觉效果三维度给出 GSB 判定、归因标签和 reason。Use when: 生图 GSB 标注, pairwise 对比打分, 图片质量评估, 指令遵循判定.'
---

# GSB 标注主控

> **规则来源**：`docs/annotation-rules.md`（硬性规则，执行权威）  
> **原始底稿**：`docs/annotation-guidelines.md`（保持不动）  
> **标注协议**：`skills/annotate-batch/SKILL.md`（单批次逐行执行协议）  
> 本 SKILL 负责每日工作流编排：切分批次 → 提取图片 → 逐批标注 → 校验 → 疑难 case 管理 → 交付。

---

## 〇、前置确认（有默认值，用户不指定则用默认）

| 确认项 | 默认值 | 说明 |
|--------|--------|------|
| **Session** | `0724` | 会话标识，用于隔离不同批次任务 |
| **Excel 路径** | 用户传入的第一个 Excel | 文件名不固定，用户拖入/粘贴路径即可 |
| **目标日期** | 当天日期 | 如 `2026-07-27` |
| **批次范围** | `batch-01` | `全部` / `batch-03` / `batch-01,batch-05` |

> 用户只给 Excel 不说明 → session=0724，日期=今天，批次=batch-01。

---

## 一、每日工作流总览

```text
用户传入 Excel 路径 + 批次范围
    │
    ├── Step 0：创建当日目录结构，备份原始 Excel
    ├── Step 1：切分 Excel 为 N 个批次（每批 ~15 行）
    ├── Step 2：对指定批次提取嵌入图片 / 下载 URL 图片
    ├── Step 3：逐批标注（调用 annotate-batch skill）
    ├── Step 4：逐批校验 + 修正
    ├── Step 5：疑难 case 管理（挂起 → 统一口径 → 回填 → 重校验）
    └── Step 6：汇总到 deliverables（含 summary.md）
```

---

## 二、Step 0：创建当日目录 + 备份

```bash
$SESSION="<session>"              # 如 "0724"
$DATE="<日期>"                    # 如 "2026-07-27"
$SRC="<用户提供的Excel路径>"

mkdir -p sessions/pairwise-gsb/$SESSION/$DATE
cp "$SRC" sessions/pairwise-gsb/$SESSION/$DATE/original.xlsx
```

目录结构：
```text
sessions/pairwise-gsb/<session>/<YYYY-MM-DD>/
├── original.xlsx
├── difficult-cases.xlsx          # 疑难 case 记录（自动生成）
├── difficult-cases-log.md        # 疑难 case 处理日志（自动生成）
├── batch-01/
│   ├── metadata.json
│   ├── input/items_行2-11.xlsx        # 文件名含原始行范围
│   ├── images/                        # row_002_图片1.png 等（按原始行号命名）
│   └── output/annotated_行2-11.xlsx   # 输出同样带行范围
├── batch-02/ ...
```

---

## 三、Step 1：切分 Excel 为批次

```bash
python projects/pairwise-gsb/scripts/split_batches.py \
    sessions/pairwise-gsb/$SESSION/$DATE/original.xlsx \
    sessions/pairwise-gsb/$SESSION/$DATE
```

> 批次大小从 `config.toml` 读取，默认 10 行。

---

## 四、Step 2：提取图片（仅对指定批次）

⚠️ **必须从 `original.xlsx` 提取**，不能从批次 `items_行*.xlsx` 提取——切分时 openpyxl 只复制单元格值，嵌入图片会丢失。

```bash
# batch-01 对应原始行 2~11（首批，batch_size=10），row-offset = 起始行 - 2
python projects/pairwise-gsb/scripts/extract_images.py \
    sessions/pairwise-gsb/$SESSION/$DATE/original.xlsx \
    sessions/pairwise-gsb/$SESSION/$DATE/batch-01/images/ \
    --min-row 2 --max-row 11 --row-offset 0
```

> 图片命名：`row_{原始行号}_{列名}.png`（如 `row_012_图片1.png`），与原始 Excel 行号一致；manifest.json 同时记录批次内行号与原始行号。

> 支持 Excel 嵌入图片和 URL 图片（http/https 自动下载）。
> `init_session.py` 已自动按批次行范围处理，手动执行时才需要上述参数。

---

## 五、Step 3：逐批标注（仅对指定批次）

对每个指定批次，调用 `skills/annotate-batch/SKILL.md` 中的 **9 步标注协议**。

- 图片来自 `images/`，对照 `manifest.json` 按行号定位
- 每次只处理当前批次（~15 条），不跨批
- 每完成一条立即自检
- 遇到疑难 case 时挂起并写入 `difficult-cases.xlsx`

---

## 六、Step 4：逐批校验

```bash
python projects/pairwise-gsb/scripts/validate_annotations.py \
    sessions/pairwise-gsb/$SESSION/$DATE/batch-01/
```

校验不通过 → 修正 → 重校验 → 通过后开始下一批。

> **硬性要求**：错误率必须为 0% 才能进入下一批。

---

## 七、Step 5：疑难 case 管理

标注过程中遇到规则未覆盖或无法确认的 case：

1. **挂起**：写入 `sessions/.../<date>/difficult-cases.xlsx`，当前条目标记“待确认”。
2. **统一口径**：与项目 owner 确认判断标准。
3. **回填**：
   ```bash
   python projects/pairwise-gsb/scripts/manage_difficult_cases.py \
       resolve sessions/pairwise-gsb/$SESSION/$DATE/difficult-cases.xlsx \
       <row_id> "<统一口径结论>"
   ```
4. **重校验**：对回填批次重新执行 `validate_annotations.py`。
5. **疑难 case 未解决前，不得计入正式交付**。

---

## 八、Step 6：汇总交付

```bash
mkdir -p deliverables/pairwise-gsb/$SESSION/$DATE/

for BATCH in batch-01 batch-02 ...; do
    mkdir -p deliverables/pairwise-gsb/$SESSION/$DATE/$BATCH
    cp sessions/pairwise-gsb/$SESSION/$DATE/$BATCH/output/annotated_*.xlsx \
       deliverables/pairwise-gsb/$SESSION/$DATE/$BATCH/
    cp sessions/pairwise-gsb/$SESSION/$DATE/$BATCH/metadata.json \
       deliverables/pairwise-gsb/$SESSION/$DATE/$BATCH/
done

python projects/pairwise-gsb/scripts/merge_batches.py \
    deliverables/pairwise-gsb/$SESSION/$DATE/ \
    --strict
```

最终交付：
```text
deliverables/pairwise-gsb/<session>/<YYYY-MM-DD>/
├── annotated-full_行1-14.xlsx      # 仅含 序号/prompt/输出列，带下拉多选列表
├── summary.md
├── difficult-cases.xlsx            # 如有疑难 case
├── batch-01/annotated_行2-11.xlsx
└── batch-NN/ ...
```

---

## 九、批次选择场景速查

| 用户说 | 处理范围 |
|--------|---------|
| "全部" / "所有批次" | batch-01 ~ batch-N（全部） |
| "batch-03" | 仅 batch-03 |
| "batch-01,batch-03,batch-05" | 指定 3 批 |
| "batch-01~batch-05" | batch-01 到 batch-05 |
| 未指定 / 首次 | 默认全部批次 |

---

## 十、快速命令参考

```bash
$SESSION="0724"
$DATE="2026-07-27"

# 一键初始化（备份 + 切分 + 提取）
python projects/pairwise-gsb/scripts/init_session.py \
    $SESSION $DATE <原始Excel路径>

# 切分
python projects/pairwise-gsb/scripts/split_batches.py \
    sessions/pairwise-gsb/$SESSION/$DATE/original.xlsx \
    sessions/pairwise-gsb/$SESSION/$DATE

# 提取（batch-01 为首批；其他批次需按原始行范围调整参数）
python projects/pairwise-gsb/scripts/extract_images.py \
    sessions/pairwise-gsb/$SESSION/$DATE/original.xlsx \
    sessions/pairwise-gsb/$SESSION/$DATE/batch-01/images/ \
    --min-row 2 --max-row 11 --row-offset 0

# 校验
python projects/pairwise-gsb/scripts/validate_annotations.py \
    sessions/pairwise-gsb/$SESSION/$DATE/batch-01/

# 查看批次状态
python projects/pairwise-gsb/scripts/batch_status.py \
    sessions/pairwise-gsb/$SESSION/$DATE

# 疑难 case 管理
python projects/pairwise-gsb/scripts/manage_difficult_cases.py \
    list sessions/pairwise-gsb/$SESSION/$DATE

# 合并（严格模式：未通过校验的批次拒绝合并）
python projects/pairwise-gsb/scripts/merge_batches.py \
    deliverables/pairwise-gsb/$SESSION/$DATE/ --strict
```
