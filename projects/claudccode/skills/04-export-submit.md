---
name: claudccode-export-submit
description: "claudccode 导出提交表并投递飞书：把全部任务/轮次数据汇总为正式提交表 CSV（每轮一行）+ 机械质检，并可逐行追加到满意度交付飞书多维表格。Use when: claudccode 导出, 提交表, CSV 汇总, 质检, 飞书投递。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取。路径变量同 [01-task-create](01-task-create.md)。
> 依赖脚本：`scripts/claudccode/export_submit.py`（导出 CSV + 质检）、`scripts/claudccode/append_delivery_feishu.py`（投递飞书）

# claudccode 导出正式提交表 · 投递飞书

## 功能概述

读取 `{RECORD_DIR}/` 下所有任务，把每个任务的共享字段（task-info.md）与每轮数据（`*-R*.md`）合并为**一行一条数据**，输出正式提交表 CSV 并做质检校验；质检通过后按需**逐行追加到满意度交付飞书多维表格**（每行 = 一条记录）。

> 提交口径：每一个单轮对话（prompt-response pair）= 一条数据；同一任务所有轮 SessionID 相同、运行环境字段相同，仅 prompt/turn/类型/难度/五维不同。

## 命令

| 命令 | 说明 |
|------|------|
| export | 默认。扫描全部任务 → 生成 CSV → 质检报告 |
| export <REPO> | 仅导出指定任务（REPO = 仓库目录名 = 任务 ID） |
| feishu | 把已导出的正式提交表 CSV 投递到飞书（先 --dry-run） |

## 执行流程

### 步骤 1：确认范围与输出路径

- 范围：全部任务 / 指定任务。
- 输出：`deliverables/claudccode/{SESSION_NAME}/正式提交表-{SESSION_NAME}-{date}.csv`（date = 当天 `YYYY-MM-DD`）。

### 步骤 2：运行导出脚本

```bash
python scripts/claudccode/export_submit.py
```

脚本行为：
- 遍历 `{RECORD_DIR}/*/task-info.md`（共享字段）+ 各 `{REPO}-R*.md`（每轮一条；REPO = 仓库目录名，脚本以目录名=任务 ID 分组）
- 每轮拼一行：任务类型 / 任务难度 / 语言/框架 / Harness / Harness版本 / 操作系统 / 环境可复现等级 / 初始环境快照 / User Prompt / SessionID / TurnID/PromptID / 轨迹文件 / 五维分数与描述 / 其他问题
- 表头见 `templates/submit-headers.csv`；TPM 内部字段（Repo URL/截图附件/备注/标注人）按配置追加在末尾
- 输出 UTF-8 with BOM CSV（Excel 打开中文不乱码）

### 步骤 3：质检校验（脚本内嵌 + 人工复核）

脚本输出质检报告，覆盖：

| 检查项 | 判定 |
|--------|------|
| 字段完整 | 必填列（五维分数与五条描述等）非空，否则标红列出 |
| 分数范围 | 五维为 1-5 整数，否则报错 |
| 轮次合规 | 每任务轮次数 ≤ 10；窗口拆分正确（SessionID 与任务一一对应） |
| SessionID 一致性 | 同一任务各轮 SessionID 一致 |
| TurnID 唯一 | 同一任务内 TurnID 不重复 |
| 快照格式 | `https://github.com/<org>/<repo>/commit/<40 hex>` |
| 难度合规 | 首轮非「简单」；任务类型在 7 类内 |
| 打分与描述一致性 | 分数方向与描述语气冲突 → 警示（人工复核） |
| 类型分布 | 按导出范围统计类型占比，对照偏序（0-1/Feature/Bug > 理解≈重构 > 其他）提示是否失衡 |
| 描述写质量 | 空/过短/笼统表述 → 警示（人工复核，AI 不代写） |

### 步骤 4：飞书投递（满意度交付多维表格）

> 目标表与表头差异见 `config.toml [feishu]`。字段映射/命名差异由脚本处理（如 `Feature迭代`→`feature迭代`、描述列加空格、`Harness版本`→`Harness 版本`）。
> 凭证：app_token/table_id 在 `config.toml [feishu]`；app_id/app_secret 默认复用 `code-eval-gsb/secrets.toml [feishu]`，也可在 `claudccode/secrets.toml [feishu]` 覆盖。

**必须先 dry-run 再正式投递：**

```bash
# 1) dry-run：拉表头/校验选项与类型/查重，不写入
python scripts/claudccode/append_delivery_feishu.py --csv <提交表.csv> --dry-run

# 2) 正式投递（每行一条记录；按 SessionID+TurnID 去重，已存在则跳过）
python scripts/claudccode/append_delivery_feishu.py --csv <提交表.csv> --submitter 张三

# 3) 若确需重复追加（如补录），加 --force
```

脚本行为：
- 逐行读取 CSV，每行 = 一轮 = 一条记录
- 单选/多选值必须是表内已有选项，否则报错并列出合法选项
- `(SessionID, TurnID/PromptID)` 已存在 → 跳过（默认幂等）；`--force` 强制追加
- 只读/关联字段（`父记录` 等）自动跳过；`提交时间` 自动填当前时间
- 输出每条追加的 record_id + 汇总（新增/已存在跳过/错误）

> **轨迹附件上传（可选但推荐）**：投递后可用同一套 app_id/app_secret 把 `records/{REPO}/{REPO}-trajectory.jsonl` 作为「轨迹文件」字段的**附件**上传并关联到对应记录：
> - `POST /open-apis/drive/v1/medias/upload_all`：`file_type` / `file_name` / `parent_type` / `parent_node` / `size` **作为 multipart 表单字段放 body**（不是 query）；`parent_type=bitable_file`、`parent_node=app_token`、`file_type` 用合法值（如 `txt`）；用 `POST /open-apis/auth/v3/tenant_access_token/internal` 换 token；
> - 返回 `data.file_token` 后，`PUT /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}`，body = `{"fields":{"轨迹文件":[{"file_token":"...","name":"...","size":...,"type":"file"}]}}`；
> - 「轨迹文件」字段是**附件**类型(`type=17`)，不能写文本路径，故 append 脚本将该列留空（`MAPPING["轨迹文件"]=None`），由本步以附件写入。

### 步骤 5：交付核对

- 当天 20:00 前执行的数据当天提交；20:00 后产生的数据次日 14:00 前提交（TPM 层面执行）。
- 输出 CSV 路径 + 数据总量 + 质检摘要；有警示项 → 提示人工处理后重新导出（数据不允许返修，务必提交前自查到位）。

## CSV 输出字段（顺序固定）

`任务类型, 任务难度, 语言/框架, Harness, Harness版本, 操作系统, 环境可复现等级, 初始环境快照, User Prompt, SessionID, TurnID/PromptID, 轨迹文件, 交付完整性, 交付完整性-描述, 指令遵循, 指令遵循-描述, 任务规划, 任务规划-描述, 推理能力, 推理能力-描述, 执行能力, 执行能力-描述, 其他问题` +（内部追加列）`Repo URL, 截图附件, 标注人, 备注`

> 表头模板见 `templates/submit-headers.csv`，可据此在建多维表格/正式提交表时直接使用。

## 注意事项

1. 所有验证为**机械/格式级**；主观质量（描述写得是否到位、是否真看过轨迹）由 TPM/质检人工复核。
2. **交付物无 AI 痕迹**：AI 起草的字段（提示词/打分依据等）必须在 score 阶段已去 AI 化；导出/投递阶段若发现疑似 AI 痕迹（模板化、`——`、反引号等）提示人工处理后重导。
3. 数据不允许返修：导出前完成自查；被抽检高频不合格的历史数据整批拒收。
4. 导出脚本不修改任何数据文件（只读 + 输出 CSV）；飞书投递为追加写（生产表，先 dry-run）。
5. 输出 CSV 用 UTF-8 BOM；禁止用会破坏 UTF-8 的写入方式。
6. 飞书投递前确认目标表 `config.toml [feishu]` 无误；追加错误需在表内手动删除后重投。
7. 首次使用前置：飞书开发者后台为应用开通 `bitable:app` 权限，并把应用添加为该多维表格的协作者。
