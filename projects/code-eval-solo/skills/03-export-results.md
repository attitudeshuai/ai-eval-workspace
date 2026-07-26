---
name: solo-export-results
description: "Solo 结果导出：把评价结果文件汇总为 CSV，含 Session ID 验证、原文一致性校验、Commit ID 远程验证。Use when: 导出评价结果, CSV 汇总, 数据分析。"
---

> 配置从 `../config.toml` 读取。路径变量同 [01-prompt-generate](01-prompt-generate.md)。
> 依赖脚本：`scripts/code-eval-solo/gen_csv.py`、`scripts/code-eval-solo/verify_session_id_cross_file.py`、`scripts/code-eval-solo/fix_session_id.py`、`scripts/code-eval-solo/verify_csv.py`、`scripts/code-eval-solo/verify_commit_id.py`

# Solo 结果导出

## 功能概述

读取任意项目的 `*-评价结果.md` 文件，将每轮评价数据提取并汇总为一个 CSV 文件。

每个评价结果文件可能含多个「第 N 次对话评价结果」块，每块输出 CSV 一行。

## 执行流程

### 步骤 1：确认扫描范围

用户给出要导出的范围：单个项目 / 多个项目 / 某个类型目录 / 所有。

若用户未说明 session，询问确认。

### 步骤 2：确定扫描根路径

根据项目名前缀自动匹配：

| 项目名前缀 | ai-model-result 根路径 |
|-----------|----------------------|
| `{PROJECT_PREFIX}-*` | `{work_root}/{SESSION_NAME}/ai-model-result/` |


输出路径：`deliverables/code-eval-solo/{SESSION_NAME}/{项目名}/csv-{项目名}-export.csv`（批量时用批次名代替项目名）

### 步骤 3：写入 Python 脚本并执行

将 Python 脚本写入 `scripts/code-eval-solo/gen_csv.py`，修改 `BASE` 和 `OUTPUT` 后执行：
```bash
python scripts/code-eval-solo/gen_csv.py
```

### 步骤 4：验证 Session ID 跨文件一致性

```bash
python scripts/code-eval-solo/verify_session_id_cross_file.py {BASE}
```

若失败 → 先修正评价结果文件：
```bash
python scripts/code-eval-solo/fix_session_id.py {BASE}
```

### 步骤 5：验证原文一致性

```bash
python scripts/code-eval-solo/verify_csv.py {OUTPUT} {BASE}
```

### 步骤 6：验证 Commit ID 正确性

```bash
python scripts/code-eval-solo/verify_commit_id.py {评价结果文件路径} {对应仓库路径}
```

## CSV 输出字段

`Repo ID`, `Trae Session ID`, `User Prompt`, `Repo URL`, `Commit ID`, `任务类型`, `业务领域`, `修改范围`, `任务难度`, `任务是否完成`, `过程与产物是否满意`, `不满意原因`

## 注意事项

1. Session ID 为空时标红，提示人工补填。
2. 所有验证步骤必须依次通过，禁止跳过。
3. Commit ID 必须完整 40 位，不得截断。
