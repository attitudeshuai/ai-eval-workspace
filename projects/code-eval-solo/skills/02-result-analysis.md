---
name: solo-result-analysis
description: "Solo 结果分析：分析模型执行结果是否完成 prompt 要求。读取提示词文件与主仓 git 历史，调用 implementation-reviewer + 双路分析（10维度过程评价），生成结构化评价结果。Use when: Solo 项目分析, 模型回答评价, 代码质量分析, 对话过程分析。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取。
> 依赖 agent：`skills/implementation-reviewer/SKILL.md`（路线 A 代码评价）
> 路径变量同 [01-prompt-generate](01-prompt-generate.md)

# Solo 项目分析技能

## 功能概述

分析 Solo 项目中模型的执行结果是否完成 prompt 要求。

负责：收集上下文 → 调用 `implementation-reviewer` skill + 自行 10 维度过程分析 → 写入评价结果文件。

不负责：继续实现功能、修复代码、补完未完成部分。

## 自然语言优先原则（强制）

- **全程用自然语言描述**。禁止出现：函数名、方法名、变量名、类名、SQL、代码片段、接口路径、文件路径、命令行参数。
- **允许例外**：「涉及文件」字段可列文件名；可偶尔提工具名（如 `todo_write`）做行为定位，但不得罗列代码内容。
- 若需指向具体逻辑，用业务语义描述。

## 项目命名约定

- 项目名格式：`{PROJECT_PREFIX}-<id>`，不补零
- 主仓根：`{REPO_BASE_PATH}/{PROJECT_PREFIX}-<id>/`
- 结果根：`{work_root}/{SESSION_NAME}/ai-model-result/{PROJECT_PREFIX}-<id>/{PROJECT_PREFIX}-<id>-{ALIAS}/`


## 两种分析模式

- **源码模式**（默认）：`0-1代码生成`、`Bug修复`、`Feature迭代`、`代码重构`、`工程化`、`代码测试`
  - 必须读取主仓 git commit 信息（repo URL、40位hash、message、diff）
- **会话模式**：`代码理解`，无代码改动

## 执行前提

必须先向用户确认：**项目名**、**提示词编号**（`<类型>-<index>`）、**第几次对话**。

执行前必须检查评价结果文件是否已存在同一轮次评价块。若已存在 → 暂停并向用户确认是否覆盖。

## 输入来源

1. 提示词文件：取 prompt、session id、模型回答内容
2. 主仓源码：通过 git 命令获取变更

**获取 commit 的 a/b 方案**（默认 a 方案）：

- **a 方案**：用户已自行提交（commit message = trae session id）
  1. `git log -1 --format="%B"` 获取最新 message，与 session id 核对
  2. `python scripts/code-eval-solo/get_commit_id.py "<主仓目录>"` 获取完整 40 位 hash
  3. `python scripts/code-eval-solo/verify_commit_id.py "<评价结果文件>" "<主仓目录>"` curl 远程验证
  4. `git show --stat <hash>` + `git show <hash>` 获取变更

- **b 方案**：用户未提交（需先检查 session id 格式 → `git add . && git commit -m "<session_id>"` → `git push`）

> Commit Message 必须严格等于 trae session id。代码理解类型不执行 git 操作。

## 执行流程

### 1. 读取提示词文件

使用 `parse_prompt.py` 脚本解析：
```
python scripts/code-eval-solo/parse_prompt.py "<提示词文件>" 0  # 列出所有轮次
python scripts/code-eval-solo/parse_prompt.py "<提示词文件>" <N>  # 输出第 N 轮详情
```

使用 `extract_session_id.py` 精确提取 session id，与 parse_prompt 输出交叉核对。

### 2. 选择模式

- `代码理解` → 会话模式
- 其他 → 源码模式（按 a/b 方案获取 git 变更）

### 3. 双路分析

**路线 A — 代码产物质量**：调用 `skills/implementation-reviewer/SKILL.md`，传入完整上下文，要求其：
- 覆盖 6 个核心维度（Prompt理解度/实现逻辑完整性/验证完整性/会话反馈响应性/跨迭代协调性/代码架构质量）
- 第1、2次对话用挑剔模式（7个角度逐一核查）
- 输出满意/不满意判定 + 不满意的点 + 过程满意度评分
- **全程自然语言，禁止代码符号**

**路线 B — 对话过程质量**（自行 10 维度分析）：

> 🔴 路线 B 是核心，必须逐维度严格执行。每个维度必须有具体行为描述支撑。

1. **prompt 理解**：逐需求点核对，遗漏或误解需对比原文说明。
2. **目标明确性**：是否在动手前明确列出目标。
3. **推理路径质量**：从产物反推过程，每发现产物缺陷必须找出推理根因。
4. **输出质量**：格式、截断、重复等。
5. **任务规划**：行为顺序是否合理，有无回退。
6. **工具使用**：重复调用、遗漏调用、冗余更新。
7. **整体流程**：线性推进还是回绕，各阶段分配。
8. **高危操作**：覆盖、删除、批量修改未说明影响。
9. **总结准确性**：逐条核对总结声称 vs 实际操作。
10. **虚假完成**：prompt 要求 vs 实际变更。

**整体满意度**：只由路线 A（代码产物）决定。路线 B 只影响「过程不满意的点」和「过程满意度」。

### 4. 写入评价结果

追加写入 `{PROJECT_PREFIX}-<id>-<类型>-<index>-评价结果.md`。

**输出格式**（严格按此模板，字段顺序不可改动）：

```text

# <项目名>-<类型>-<index> 第 N 次对话评价结果

### 标志：
{PROJECT_PREFIX}-150-13

## Session ID
【原文逐字复制】

## Repo URL
【去掉 .git 后缀的 https 地址】

## Commit ID
【完整 40 位 hash，通过 get_commit_id.py 获取，通过 verify_commit_id.py 远程验证】

## 提示词
【原文逐字复制】

## 修改范围
【原文逐字复制】

## 是否完成
【严格跟随是否满意】满意→"完成了任务"，不满意→"未完成任务"

## 任务难度
简单 / 一般 / 困难 / 地狱

## 是否满意
满意 / 不满意

## 不满意的点
【固定必填】满意时写"无"；不满意时以"产物不满意："开头，最多3个核心问题，全程自然语言，禁止代码符号和不确定表述。

## 过程不满意的点
【固定必填，8 个维度逐一评估】每条必须有具体行为描述支撑，禁止步骤编号和量化定位。只描述过程问题，不重复产物问题。

## 过程满意度
<80-100字连贯叙述>

## 下一轮推荐提示词
<仅不满意时填写，60-120字，必须是不满意的点的另一种说法，禁止引入新问题>

## 涉及文件
<仅不满意时填写，列出文件名+共几个文件>
```

### 5. 写入后双重验证

```
python scripts/code-eval-solo/verify_commit_id.py "<评价结果文件>" "<主仓目录>"
python scripts/code-eval-solo/verify_review.py "<评价结果文件>" "<提示词文件>" "<主仓目录>"
```

任一失败必须修正后重试。

## 注意事项

1. 每次分析前必须主动读取文件，不依赖缓存。
2. 源码路径：`{REPO_BASE_PATH}/{PROJECT_PREFIX}-<id>/`，通过 git 获取变更。
3. 文件名与标识串无 `A-` 前缀。
4. 两种模式均必须读取「模型第 N 次回答内容」。
5. 以 implementation-reviewer 结论为准。
6. 自然语言优先，禁止代码符号。
7. `Session ID`、`提示词`、`修改范围`、`Commit ID` 必须原文逐字复制。
8. 评价后必须执行双重验证脚本。
9. Session ID 提取必须用脚本，禁止凭记忆。
10. 禁止擅自覆盖已有评价结果。
