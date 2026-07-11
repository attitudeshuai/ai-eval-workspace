---
name: webdev-task-packer
description: Pack a webdev-long-horizon task and its source code, then upload to a remote machine for running codex directly.
---

# Web Dev Task Packer

将 `projects/webdev-long-horizon` 的任务资产与源码打包，上传到远程机器，供 codex cli 直接运行。

## 触发条件

当用户希望把提示词和源码放到 remote 上面用 GPT/codex 跑时调用本技能。

## 远程配置

远程配置统一读取 `projects/webdev-long-horizon/config.toml` 和 `secrets.toml` 中的 `[remote]` 段：

`config.toml`（可提交）：

```toml
[remote]
# 连接信息（host/port/user/password）已集中到 secrets.toml。
# 如需覆盖，可在此声明；config.toml 中的值优先级低于 secrets.toml。
remote_dir = "/root/charles"
secrets_file = "secrets.toml"
```

> 下文示例中的 `<remote_dir>` 均指 `config.toml` 中 `[remote].remote_dir` 配置的值。若你修改了该值，请将示例中的 `<remote_dir>` 替换为实际路径。

`secrets.toml`（已加入 `.gitignore`，请勿提交）：

```toml
[remote]
host = "59.49.28.154"
port = "7826"
user = "root"
password = "your-password"
```

## 目录结构说明

任务与源码按家族分组存放：

```text
projects/webdev-long-horizon/
├── tasks/webdev-task-01/
│   ├── webdev-task-01/
│   └── webdev-task-01.01/
└── sources/webdev-task-01/
    ├── webdev-task-01/
    └── webdev-task-01.01/
```

远程运行时期望的目录结构：

```text
<remote_dir>/webdev-task-01.01/
├── source/               # 源码
├── PROMPT.md             # 提示词
└── ...
```

## 输入信息

调用前需要确认：

- 任务 ID（如 `webdev-task-01.01`）
- 远程机器配置已写入 `config.toml` 和 `secrets.toml`
- 源码位置：
  - `projects/webdev-long-horizon/sources/<family>/<task-id>/`
  - 或 `projects/webdev-long-horizon/tasks/<family>/<task-id>/starter/`

## 工作流程

1. 确认任务目录存在：
   ```bash
   ls projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01.01
   ```
2. 确认源码目录存在：
   ```bash
   ls projects/webdev-long-horizon/sources/webdev-task-01/webdev-task-01.01
   # 或
   ls projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01.01/starter
   ```
3. 打包并上传到远程机器：
   ```bash
   python scripts/webdev-long-horizon/upload_to_remote.py --task webdev-task-01.01
   ```
   此脚本会：
   - 打包任务资产为 `webdev-task-01.01.tar.gz`
   - 打包源码为 `webdev-task-01.01-source.tar.gz`
   - 通过 SSH 上传到 `<remote_dir>/`
   - 远程解压并整理出 `<remote_dir>/webdev-task-01.01/source/`
4. 提示用户在远程运行 codex：
   ```bash
   ssh root@59.49.28.154 -p 7826
   cd <remote_dir>/webdev-task-01.01/source

   # 自动化运行需要 --dangerously-bypass-approvals-and-sandbox
   # 若手动交互运行，可去掉该参数
   codex exec -m gpt-5.6-sol \
     --dangerously-bypass-approvals-and-sandbox \
     < <remote_dir>/webdev-task-01.01/PROMPT.md
   ```

## 远程产物回收

运行结束后，使用 `scripts/fetch_remote_results.py` 一键拉回并整理产物：

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task webdev-task-01.01 \
  --agent codex \
  --session session-sota-YYYY-MM-NNN-codex
```

产物会被整理到标准 session 目录：

```text
sessions/session-sota-YYYY-MM-NNN-codex/
  projects/webdev-long-horizon/
    submissions/webdev-task-01.01/codex/
      source/               # codex 修改后的源码
      screenshots/          # 关键状态截图
      sota.log              # 运行日志（如果已保存）
```

也可以只拉回到当前目录：

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task webdev-task-01.01 \
  --output ./
```

## 注意事项

- 上传前确保 `PROMPT.md` 已生成，且明确告知 codex 源码位于 `./source`。
- 若 mock 数据需要被源码读取，确保 `mock-data/` 已同时存在于任务目录和源码目录。
- 远程运行结束后，使用 `evaluator` skill 对产物进行评估。
