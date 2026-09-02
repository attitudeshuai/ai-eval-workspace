---
name: swe-export-delivery
description: "SWE 交付导出：验收复盘完成后，把任务记录映射为交付表 24 字段（含 Type / commitUrl）并追加一条记录到飞书多维表格。Use when: SWE 导出, 交付表追加, 飞书多维表格。"
---

# SWE 交付导出 · 追加记录到飞书多维表格

> 配置从 `../config.toml [feishu]` 读取（app_token / table_id / dedupe_field），凭证在 `../secrets.toml [feishu]`（app_id / app_secret）。
> 脚本：`scripts/swe-like/append_delivery_feishu.py`（仅标准库，Python 3.11+）

每次 `review` 验收完成、用户确认 `review.md` 后执行本技能：把任务目录的记录映射为交付表的一条记录（24 字段，含「Type」「commitUrl」），追加到交付飞书多维表格（`config.toml [feishu]` 指向的「数据表」）。

## 功能概述

1. 读取该任务的 `task.md` / `meta.json` / `verify-rubric.md` / `run-log.md` / `result.md` / `review.md`
2. 按交付表 24 字段逐字段映射，生成记录 JSON
3. 调用 `append_delivery_feishu.py` 先 `--dry-run` 校验，再正式追加
4. 输出追加结果（record_id、留空字段清单），提示用户核对

**本技能不负责：**

- 出题、运行或验收（由 01/02/03 完成）
- 替人工确认判定（`review.md` 残留占位标记时中止）

## 命令

| 命令 | 说明 |
|------|------|
| export | 默认命令。任务记录 → 追加一条记录到飞书多维表格 |

## 执行流程

**输入：**
```
分支名：<repo>-01 / <repo>-02 / <repo>-03 之一
```

> Reviewer 从 `review.md` 读取（验收阶段人工填写），不再作为命令参数。

> 提交人**不填写**：飞书表格「提交人」字段有默认值，交付时脚本跳过不写入。

**步骤：**

1. **读取任务记录**：`{work_root}/{session}/tasks/{repo}/{branch}/` 下的 `task.md` / `meta.json` / `verify-rubric.md` / `run-log.md` / `result.md` / `review.md`。

2. **完成度检查（不满足则中止）**：
   - 所有文件中不得残留 `【待填写】` / `【待用户填写】` 占位标记
   - `meta.json` 的 Repo URL / Commit/版本 / 主要语言 / 任务类型 / Seed 模型/版本 齐全
   - `run-log.md` 的 Trae Session ID、有效轮数（= 步数）、commitUrl 齐全
   - `review.md` 的是否完成需求 / Reviewer / 是否通过质检 齐全

3. **生成记录 JSON**：写入 `.tmp/<task-id>-delivery.json`，键名与多维表格字段名**逐字一致**，映射规则见下节。

4. **校验并追加**（在工作台根目录执行）：

   ```bash
   # 先 dry-run 校验字段名、选项值与留空情况
   python scripts/swe-like/append_delivery_feishu.py \
     --json .tmp/<task-id>-delivery.json --dry-run

   # 确认无误后正式追加
   python scripts/swe-like/append_delivery_feishu.py \
     --json .tmp/<task-id>-delivery.json
   ```

   - 脚本按 `config.toml [feishu].dedupe_field`（默认「题目名称」）查重，重复时需用户确认后加 `--force`
   - 单选/多选字段的值必须是表格中已有选项；脚本会校验，不匹配时报错并列出全部合法选项
   - 「提交日期」为日期字段，默认填当前日期；如表格设为自动创建时间，脚本会按只读字段跳过

5. **输出结果**：追加的 record_id + 留空字段清单，提示用户在多维表格中抽查该条记录。

## 字段映射规则（24 字段）

| # | 字段 | 来源 |
|---|------|------|
| 1 | 题目名称 | `meta.json`（与查重键一致） |
| 2 | Type | `review.md` 收录判定（单选：有效轮数 > 100 / 有效轮数 < 100 且 效果差 / 有效轮数 < 100 且 效果好） |
| 3 | 提交人 | 不填写：飞书表格该字段有默认值，脚本跳过不写入 |
| 4 | 提交日期 | 当前日期（日期字段；若为自动创建时间则跳过） |
| 5 | Repo URL | `meta.json`（超链接字段） |
| 6 | Commit/版本 | `meta.json` 固定版本 |
| 7 | 主要语言 | `meta.json`（单选，本轮仅提交 Go / Python） |
| 8 | 任务类型 | `meta.json`（单选：功能新增 / Bug 修复 / 测试增强 / 重构/性能 / 配置/工具链 / 其他 / 问题修复） |
| 9 | 需求 Prompt（原文） | `task.md` **原文复制，禁止改写** |
| 10 | 真实性与难度说明 | `task.md` 或出题交付 |
| 11 | 可能涉及模块 | 出题交付 |
| 12 | Verify Rubric | `verify-rubric.md` **原文复制，禁止改写** |
| 13 | 产物结果 | `result.md` 产物描述 |
| 14 | 产物补充材料 | `result.md` 材料路径（patch / verifier 日志等） |
| 15 | Seed 模型/版本 | `meta.json`（实际运行模型/版本） |
| 16 | Trae Session ID | `run-log.md` **原文复制，禁止改写** |
| 17 | Trae Session ID 2 | 【待确认】数字字段；疑似第二/续跑 Session，默认留空 |
| 18 | 有效轮数 | `run-log.md`（数字；= 模型输出步数 / 有效 TC 次数） |
| 19 | seed 轮次 | 【待确认】文本；默认留空 |
| 20 | 是否完成需求 | `review.md`（单选：完成 / 部分完成 / 未完成 / 无法判断） |
| 21 | Reviewer | `review.md`（验收阶段人工填写） |
| 22 | 是否通过质检 | `review.md`（单选：通过 / 未通过（题面验收未全部满足）） |
| 23 | 备注 | `review.md` 收录判定结论及其他补充 |
| 24 | commitUrl | `run-log.md`（fork 开源 repo 后、模型改完 commit 的 URL；填写规范待同步） |

> **有效轮数 = 模型输出步数**（已确认）：「有效轮数」字段填的就是「模型输出步数」（有效 TC 次数，Codex 读 Trae 日志得到）。「Trae Session ID 2」（数字）与「seed 轮次」（文本）两个字段的真实含义仍待甲方确认，默认留空。
> **commitUrl**（试标新增）：修改前 fork 开源 repo，模型改完再 commit，commitUrl 填该 commit 的 URL。填写规范待甲方同步，先记录到 `run-log.md`。

## 注意事项

1. **必须先 dry-run 再正式追加**；dry-run 输出的留空字段清单需人工过目，确认留空都是"本就无数据"而非漏映射。
2. 键名与字段名逐字一致（含空格、全角括号），脚本对未知键名直接报错。**字段名以实际 SWE 交付飞书表为准**，若表头与本文档不一致，以脚本拉取到的表头为准（「Type」「Trae Session ID 2」「seed 轮次」等字段务必以实际表头为准）。
3. 单选/多选字段只能写已有选项；如需新选项，先在多维表格中手动添加，再重新导出。
4. `需求 Prompt（原文）`、`Verify Rubric`、`Trae Session ID` 三处强制原文复制，禁止改写或推断。
5. **表单填写规范**（见 `docs/内部规范.md`）：任何字段不得含 Markdown 标签（标题/引用/代码块/加粗/斜体），去 AI 味；本轮语言仅限 Go / Python；一个 Repo 最多 3 条；Type =「有效轮数 < 100 且 效果好」的数据 ≥ 总提交 25%（不结算，不得筛掉）。
6. 多维表格是最终交付物，追加前确认任务已定稿；追加错误记录需在多维表格中手动删除后重新导出。
7. 首次使用前置：飞书开发者后台为应用开通 `bitable:app` 权限，并把应用添加为该多维表格的协作者。
