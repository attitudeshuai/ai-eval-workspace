---
name: swe-step-count
description: "SWE 有效轮数统计（agent step 口径）：TraeX 用 count_steps.py 对原始轨迹计数，miniswe 取 api_calls，或用 Hook 客户端。Use when: 步数统计, 有效轮数, effective_turns, agent step。"
---

# SWE 有效轮数统计（agent step 口径）

> 被 `02-run-record.md` 调用。口径依据 `../docs/内部规范-v1.md` 与 `../docs/SWE-like Repo-v3.md` 第 7 节。
> ⚠️ 旧的「读 Trae renderer.log 数有效 TC 次数」方式已作废，本文件只保留新口径。

## 新口径：agent step（一次模型调用 = 1 步）

有效轮数（`effective_turns`）以 agent step 为单位，**不是**工具调用次数：

- 一次模型调用记为一个 step；
- 一批工具调用无论包含几个调用，均记为一个 step（不是每个工具调用各算 1）；
- 未附带工具调用的收尾回复记为一个 step；
- 一次上下文压缩记为一个 step；
- 子代理（`spawn_agent`）执行的轮数一并计入；
- 环境重试不计入。

## 获取方式（三选一）

### 1. Hook 客户端（推荐，准确率高）

见 `docs/内部规范-v1.md`：https://github.com/aliAjax/tc-hook-kit-main-5a8b63a

### 2. TraeX：count_steps.py

对 `.trae/cli/sessions/` 下的**原始轨迹**跑（子代理轨迹是独立文件，依赖该目录结构定位；轨迹拷入 `evidence/` 后无法关联，计数会偏小）：

```bash
python3 count_steps.py ~/.trae/cli/sessions/2026/09/03/rollout-xxx.jsonl
python3 count_steps.py <轨迹文件> --show   # 想看每一步是什么
```

### 3. miniswe：api_calls

取 `.traj.json` 里 `info.model_stats.api_calls`，无需 count_steps.py。

## 填表

- `task.toml` 的 `effective_turns` = 上述得到的整数。
- 底稿「有效轮数」列由 `toml2base.py` 从 `task.toml` 回填。
- `count_steps.py` 与 `harbor-交付模板包.zip` 见 `SWE-like Repo-v3.md` 第 7 节附件。

## 快速检查清单

- [ ] 口径是 agent step（一次模型调用 = 1 步），不是工具调用次数
- [ ] TraeX 用 count_steps.py 对 .trae/cli/sessions/ 原始轨迹跑（不是 evidence/ 里的拷贝）
- [ ] miniswe 取 .traj.json 的 info.model_stats.api_calls
- [ ] 环境重试未计入
- [ ] 旧方式（读 renderer.log 数有效 TC）没有再用
