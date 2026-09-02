---
name: swe-step-count
description: "SWE 有效轮数统计：按固定顺序抓取 Trae 日志统计有效 TC（文件操作 + 终端命令），重点防漏终端命令。Use when: 步数统计, 有效轮数, 有效 TC 次数, Session ID 抓日志。"
---

# SWE 有效轮数统计（步数统计·实操）

> 被 `02-run-record.md` 第 3 步「获取有效轮数」调用。口径依据 `../docs/步数统计.txt`，本文固化**抓取顺序**与 Trae 3.3.95 的坑。

## 为什么单独成 skill

Trae CN 3.3.95 的终端命令执行（pytest / ruff / go test / 冒烟命令）**不产生 tooling 工具调用**，renderer.log 里看不到命令本身和输出，只按 renderer.log 统计会漏掉终端命令（曾把 38 误算成 30）。因此必须按下面的顺序，从「日志」和「模型最终答复」两个来源抓取，缺一不可。

## 抓取顺序（按序执行，勿跳步）

### 0. 解析 Session ID

格式：`<user_id>:<trace_id>_<session_id>.<agent_message_id>.<user_message_id>:<客户端版本时间>`

拆出 `session_id`、`trace_id`、`user_message_id` 三个搜索键，`session_id` 最常用。Session ID 原文照录，禁止改写。

### 1. 定位日志目录

- Windows：`$env:APPDATA\Trae CN\logs`（PowerShell 里 `%APPDATA%` 不展开，用 `$env:APPDATA`）
- macOS：`~/Library/Application Support/Trae CN/logs`

列出时间戳目录，找与会话时间最接近的那个（Session ID 末尾的时间，如 `2026/9/3 00:03:12` 对应 `20260902T235549`）。

### 2. 全目录搜索会话（勿只看 window1）

对整个 logs 目录递归搜索 `session_id` / `trace_id`，得到命中文件完整路径。可能有多个 window（window1/window2/window3），都要看。锁定会话后确认：`trace_id` 一致、用户消息内容对得上、会话最终 `status` 为 completed。

### 3. 确认会话归属（防错，必须先做）

Session ID 与用户报的任务名可能对不上（曾出现「restic-01 的 ID 实际跑的是 flask-01」）。抓数之前先核对：

- 工具调用里引用的仓库路径（`repos/<repo>/<branch>/`）指向哪个 repo
- 日志里 prompt 关键词（题干术语）命中哪个任务
- 与用户给的任务名不一致时，**先问用户再落盘**，绝不把 A 任务的 Session 记到 B 任务

### 4. 统计文件操作类 TC（renderer.log）

匹配模式：

```text
[message:<user_message_id>] <uuid> icube.common.commands.tooling.<Name> start
```

按唯一 UUID 去重计数。计入：

| 工具 | 含义 |
|------|------|
| applyChatSnapshotPatch | 写文件 |
| readFile | Agent 主动读文件 |
| listFolder | 列目录 / 搜索 |

排除（不计入）：getAutoRunConfig、getDocumentByUri、getDiagnostics、getRulesDetails、fileDiffCount、getConfigurationValue、getTerminalContributedEnv、getNextAvailableTerminal、getAllAgentExtensions、getAllOpenedProjects、getDeviceId、filePathSensitiveOrNot、reportIdeSubagentAICodeContribution、createBinaryFile 等客户端配置 / 诊断 / 编辑器刷新 / 上报类调用。

### 5. 终端命令不落盘——换来源（关键，最易漏）

Trae 3.3.95 终端命令走集成终端，**不产生 tooling 工具调用**，特征：

- renderer.log 无 `runCommandInTerminal` / `executeCommand` / 命令文本（pytest、ruff 都搜不到）
- 只有 `getTerminalContributedEnv`（终端环境读取，cost 0-2ms，**不计入**，只作终端活跃信号）
- ShellExec 未启用（`useShellExec=false`）
- 终端输出（`64 passed`、ruff 结果、`Unknown config key` 等）不落盘，日志里搜不到
- `Modular/ai_agent-*.alaudalog` 是二进制且常被进程锁，读不出

所以终端命令次数**从模型最终答复里数**：让用户贴模型结尾的「验证结果」段，或从会话最后一条消息取。每条独立命令计 1 次（状态轮询 / 结果读取合并不重复计）。

### 6. 确认会话状态与时间

找 `[DoneHandler] Stream done event received` / `[stream-diagnostics][done]`，确认 `status:"completed"` 及完成时间，记入 run-log。

### 7. 汇总写 run-log.md

```text
有效轮数 = 文件操作 TC + 终端命令 TC
```

run-log 里分开列：文件操作明细（工具 + 次数）、终端命令明细（命令列表 + 次数）、排除项、以及「终端命令不落盘」的统计说明，便于复核。

## 快速检查清单

- [ ] 拆出 session_id / trace_id / user_message_id
- [ ] 搜了整个 logs 目录，不是只看 window1
- [ ] 确认会话实际跑的是哪个 repo / 任务（与用户报的一致，否则先问）
- [ ] 文件操作类 TC 按唯一 UUID 去重
- [ ] 明确排除了 getTerminalContributedEnv / getDocumentByUri / getDiagnostics 等
- [ ] 终端命令从模型最终答复里数了（pytest / ruff / go test / 冒烟命令）
- [ ] 有效轮数 = 文件操作 + 终端命令，不是只看 renderer.log
- [ ] 会话 status 为 completed

## 参考案例（flask-01）

有效轮数 38 = 文件操作 30（applyChatSnapshotPatch 8 + readFile 20 + listFolder 2）+ 终端命令 8（pytest 1 + ruff check 1 + ruff format --check 1 + flask 冒烟 5）。终端命令未落盘，8 条来自模型最终答复；renderer.log 里的 getTerminalContributedEnv（10 次）是环境读取，不计入。
