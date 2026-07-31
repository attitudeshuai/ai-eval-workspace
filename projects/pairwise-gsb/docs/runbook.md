# Pairwise GSB 标注 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，逐步完成 GSB 标注全流程。

> 规则细节见 `docs/annotation-rules.md`（硬性规则），执行协议见 `skills/annotate-batch/SKILL.md`，主控流程见 `skills/gsb-annotator/SKILL.md`。

---

## 快速启动

```
把 <Excel路径> 标注了
```

AI 会自动识别文件、使用当天日期、默认从 batch-01 开始。

**指定批次：**

```
把 <Excel路径> 标注了，做 batch-03
把 <Excel路径> 标注了，做全部批次
把 <Excel路径> 标注了，做 batch-01,batch-03,batch-05
```

---

## 完整流程

### Step 1：切分 + 提取图片

```text
切分并提取图片
```

AI 会执行：

1. 备份原始 Excel → `sessions/pairwise-gsb/<session>/<日期>/original.xlsx`
2. 切分为批次（每批 15 行）→ `batch-01/` ~ `batch-NN/`
3. 对指定批次提取嵌入图片 → `batch-NN/images/`
4. 输出 `manifest.json`（图片→行列映射）

### Step 2：逐批标注

```text
标注 batch-01
```

AI 会按 `skills/annotate-batch/SKILL.md` 的 9 步协议逐行标注：

1. 读 prompt 列约束清单
2. 判定任务类型（T2I / 图片编辑 / 参考生成）
3. 逐图检查（指令遵循 → 一致性 → 视觉效果）
4. 专项判断（文字/结构/拉伸/画质/色调等硬规则归属）
5. 填分维度 GSB
6. 选归因标签
7. 填整体 GSB
8. 写 reason
9. 逐行自检 + 疑难 case 挂起

> 图片优先用 `ReadMediaFile` 工具查看 `images/` 下的 PNG；无法查看时 reason 会注明，并挂起为疑难 case。

### Step 3：校验

```text
校验 batch-01
```

等价于：

```bash
python projects/pairwise-gsb/scripts/validate_annotations.py sessions/pairwise-gsb/<session>/<日期>/batch-01/
```

校验项：

- 字段值合法性（GSB、标签范围）
- T2I 一致性字段是否正确
- reason 是否包含四段结构
- reason 与 GSB/标签是否矛盾
- "无法区分"占比是否 >60%

> 错误率必须为 0% 才能进入下一步。

### Step 4：修正

如有错误，AI 会读取 `errors.txt`，逐条修正 `annotated.xlsx` 后重新校验。

```text
修正 batch-01 的错误
```

### Step 5：交付

```text
导出 2026-07-27 的结果
```

AI 会执行：

1. 合并所有已完成批次的 `annotated.xlsx`
2. 统计 GSB 分布
3. 输出到 `deliverables/pairwise-gsb/<session>/<日期>/`

---

## 常用对话指令

| 你说的                          | AI 做的                         |
| ------------------------------- | ------------------------------- |
| `把这个 Excel 标注了`         | 切分→提取→标注 batch-01→校验 |
| `继续下一批`                  | 标注 batch-02                   |
| `标注全部批次`                | 从 batch-01 做到最后一批        |
| `校验 batch-03`               | 只校验不标注                    |
| `导出今天的`                  | 合并所有批次到 deliverables     |
| `重新标注 batch-02`           | 覆盖 batch-02 的标注结果        |
| `batch-01 有几条错了，帮我修` | 读 errors.txt 逐条修正→重校验  |

---

## 手动命令速查

```bash
SESSION="0724"
DATE="2026-07-27"

# 切分（batch_size 默认 10，从 config.toml 读取）
python projects/pairwise-gsb/scripts/split_batches.py \
    sessions/pairwise-gsb/$SESSION/$DATE/original.xlsx \
    sessions/pairwise-gsb/$SESSION/$DATE

# 提取图片（必须从 original.xlsx 按批次行范围提取；batch-01 为首批示例）
python projects/pairwise-gsb/scripts/extract_images.py \
    sessions/pairwise-gsb/$SESSION/$DATE/original.xlsx \
    sessions/pairwise-gsb/$SESSION/$DATE/batch-01/images/ \
    --min-row 2 --max-row 11 --row-offset 0

# 校验
python projects/pairwise-gsb/scripts/validate_annotations.py \
    sessions/pairwise-gsb/$SESSION/$DATE/batch-01/

# 合并
python projects/pairwise-gsb/scripts/merge_batches.py \
    deliverables/pairwise-gsb/$SESSION/$DATE/ --strict
```

---

## 目录速查

| 路径                                                                                  | 用途                                        |
| ------------------------------------------------------------------------------------- | ------------------------------------------- |
| `sessions/pairwise-gsb/<session>/<日期>/original.xlsx`                              | 原始备份                                    |
| `sessions/pairwise-gsb/<session>/<日期>/batch-NN/input/items_行{起}-{止}.xlsx`      | 批次输入（默认 10 行）                      |
| `sessions/pairwise-gsb/<session>/<日期>/batch-NN/images/`                           | 提取的图片（`row_{原始行号}_{列名}.png`） |
| `sessions/pairwise-gsb/<session>/<日期>/batch-NN/output/annotated_行{起}-{止}.xlsx` | 标注结果                                    |
| `sessions/pairwise-gsb/<session>/<日期>/batch-NN/errors.txt`                        | 校验报告（有错误时生成）                    |
| `deliverables/pairwise-gsb/<session>/<日期>/annotated-full_行{起}-{止}.xlsx`        | 最终交付（仅 序号/prompt/输出列）           |

---

## 故障排查

| 问题               | 处理                                                                   |
| ------------------ | ---------------------------------------------------------------------- |
| 切分后批次数不对   | 检查 Excel 是否有多余空行；可用`--batch-size` 调整                   |
| 图片提取为空       | Excel 中图片是嵌入的还是链接？链接图片需手动下载                       |
| 校验报字段错误     | 检查列名是否和 config.toml 中`input_columns`/`output_columns` 一致 |
| "无法区分"超过 60% | AI 会提醒复查，逐条确认是否确实无差异                                  |
| 某批想重做         | 删除`batch-NN/output/`，重新标注即可                                 |
