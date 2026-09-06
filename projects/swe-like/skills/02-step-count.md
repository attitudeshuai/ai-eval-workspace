---
name: swe-step-count
description: "SWE 有效轮数统计：TraeCode CN/Trae CN 用 tc-hook-kit 数有效 TC（PostToolUse 去重排除）；TraeX 用 count_steps.py 数 agent step；miniswe 取 api_calls。Use when: 步数统计, 有效轮数, effective_turns, 有效 TC, hook。"
---

# SWE 有效轮数统计

> 被 `02-run-record.md` 调用。口径依据 `../docs/内部规范-v1.md` 与 `../docs/SWE-like Repo-v3.md` 第 7 节。
> **现行确认口径：有效轮数 = 有效 TC**（甲方 2026/09 确认：「那个轮次就是有效 TC，平台表单应该有误」）。

## 口径：有效轮数 = 有效 TC

表单「有效轮数」要填的是**有效 TC**：`PostToolUse` 工具调用，按 `tool_use_id` 去重，排除轮询/配置/补丁类工具（`checkRunCommandStatus`、`getDiagnostics`、`getConfigurationValue`、`fileDiffCount`、`getAutoRunConfig`、`getDocumentByUri`、`applyChatSnapshotPatch`）。平台把字段误写成"有效轮数"，填有效 TC 即可。

不同终端怎么得到它：

| 终端 | 统计方式 | 得到 |
|------|---------|------|
| **TraeCode CN / Trae CN（IDE）** | tc-hook-kit Hook（本流水线主力） | **有效 TC** ✅ |
| **TraeX（CLI）** | `count_steps.py` 对 `.trae/cli/sessions/` 原始轨迹 | agent step（一次模型调用 = 1 步，与有效 TC 不同口径） |
| **miniswe** | `.traj.json` 的 `info.model_stats.api_calls` | api_calls |

> ⚠️ TraeX 的 `count_steps.py` 数的是 **agent step**，不是有效 TC。若结算统一按「有效 TC」，用 TraeX/miniswe 需另行换算或改口径；当前按「TraeCode CN + Hook」最直接。

## TraeCode CN 用 Hook 拿有效 TC（可行方案）

> **系统适配**：以下为 **Windows（TraeCode CN on Windows）** 的实测方案。**macOS** 直接沿用 tc-hook-kit 自带 `install.sh`（bash）即可——它写 `~/.trae-cn/hooks.json`、用 `node <bridge.js>`（node 在 PATH 上），**无需**本节的 wrapper / BOM / `setup-hook.ps1` 等 Windows 特化处理。

前置：Python 3、Node >= 18；仓库 `scratch/tc-hook-kit`（tc-hook-kit）已拉好。

### 1. 配置（初始化一次）

Windows 下在 tc-hook-kit 目录跑 `setup-hook.ps1`（替代 `install.sh`），或手动：
- 生成 secret → 写 `~/.tc-hook-kit/config.json` + `bridge.json`（二者 `server_url` 与 `hook_secret` 必须一致）。
- 写 `~/.trae-cn/hooks.json`，6 个事件（`SessionStart` / `UserPromptSubmit` / `PreToolUse` / `PostToolUse` / `Stop` / `Notification`）都指向**一个单标记无空格命令**。

### 2. 三个关键坑（Windows 特有，都踩过）

1. **trae-sandbox 按空格拆命令**。TraeCode CN 用 `trae-sandbox.exe exec --command-line <命令>` 执行 hook，命令**按空格拆分**。所以不能直接写 `"D:\Program Files\nodejs\node.exe" "…\bridge.js"`——`Program Files` 带空格会报 `unexpected argument`。
   **解决：用路径无空格的 wrapper 脚本**，命令只填 wrapper 的路径（单标记），wrapper 内部再调用 node：
   ```cmd
   @echo off
   "D:\Program Files\nodejs\node.exe" "D:\...\tc-hook-kit\bridge.js"
   ```
   hooks.json 的 command 填 `D:\...\tc-hook-kit\hook-runner.cmd`。
2. **BOM**。PowerShell 5.1 `Set-Content -Encoding utf8` 会写 UTF-8 BOM，Python `json.loads` / Node `JSON.parse` 会报 `Unexpected UTF-8 BOM`。配置/脚本必须**无 BOM**（用 `utf-8-sig` 解码或 UTF-8 无 BOM 写回）。
3. **改完要重启 TraeCode CN**（`hooks.json` 启动时读取，不热加载）。

### 3. 启动接收端 + 跑题 + 查数

```bash
# 跑题前开接收端（保持一整轮，否则事件丢；确保 8765 只有一个实例）
python D:/charles/program/ai/ai-eval-workspace/scratch/tc-hook-kit/server.py --host 127.0.0.1 --port 8765
curl.exe http://127.0.0.1:8765/health          # 应返回 ok

# 跑完后按 session 查数
curl.exe http://127.0.0.1:8765/sessions         # 列出 session_id
curl.exe "http://127.0.0.1:8765/stats?session_id=<片段>"
```

返回的 `valid_tc` 即有效 TC，填 `task.toml` 的 `effective_turns`。

## 其他终端（备用口径）

- **TraeX**：对 `.trae/cli/sessions/` 原始轨迹跑（子代理轨迹是独立文件，依赖该目录结构；拷入 `evidence/` 会漏数）：
  ```bash
  python3 count_steps.py ~/.trae/cli/sessions/2026/09/03/rollout-xxx.jsonl
  python3 count_steps.py <轨迹> --show
  ```
- **miniswe**：取 `.traj.json` 的 `info.model_stats.api_calls`。

## 快速检查清单

- [ ] 口径已确认：有效轮数 = 有效 TC，`task.toml.effective_turns` 填 `valid_tc`
- [ ] TraeCode CN 的 hook 命令是**单标记 wrapper（无空格）**，不是 `node "..."`
- [ ] 配置文件（`config.json` / `bridge.json` / `hooks.json`）**无 BOM**
- [ ] 改完 hook 配置后**重启了 TraeCode CN**
- [ ] 接收端在跑、`/health` 返回 ok，且 8765 只有 1 个进程
- [ ] `count_steps.py`（agent step）仅 TraeX 用，不用于 TraeCode CN
