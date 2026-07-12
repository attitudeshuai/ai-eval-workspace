---
name: webdev-task-packer
description: 'Pack webdev-long-horizon task assets and source code, upload to remote machine for codex execution. Use when uploading tasks to remote, pushing to remote server, remote codex run, 打包上传, 远程运行, 上传到远程.'
---

# Web Dev Task Packer

将 `projects/webdev-long-horizon` 的任务资产与源码打包，上传到远程机器，供 codex cli 直接运行。

## When to Use

- 用户希望把提示词和源码放到 remote 上用 GPT/codex 运行
- 需要将任务资产打包并上传到远程服务器
- SOTA 远程运行模式的前置步骤

## 前置确认

调用前需确认：
- **任务 ID**（如 `{prefix}-01.01`，其中 `{prefix}` 为 `config.toml` 中 `task_prefix` 的值）
- 远程机器配置已写入 `config.toml` 和 `secrets.toml`
- 任务类型：增量任务需 `sources/` 下有源码，Greenfield 任务无需源码

## 远程配置

配置读取自两个文件：

**`projects/webdev-long-horizon/config.toml`**（可提交）：

```toml
[remote]
remote_dir = "/root/charles"
secrets_file = "secrets.toml"
```

**`projects/webdev-long-horizon/secrets.toml`**（已加入 `.gitignore`，请勿提交）：

```toml
[remote]
host = "<remote-host>"
port = "<remote-port>"
user = "<remote-user>"
password = "<remote-password>"
```

## 目录结构约定

```text
projects/webdev-long-horizon/
├── tasks/{prefix}-01/
│   ├── {prefix}-01/          # 顶层任务
│   └── {prefix}-01.01/       # 增量任务
└── sources/{prefix}-01/
    ├── {prefix}-01/          # 顶层源码
    └── {prefix}-01.01/       # 增量源码
```

> `{prefix}` 为 `config.toml` 中 `task_prefix` 的值（默认 `webdev-task-sxw`），下同。

远程运行时期望的目录结构：

```text
<remote_dir>/<task-id>/
├── source/               # 源码（agent 在此目录中工作）
├── PROMPT.md             # 提示词（由 task.md 上传后重命名）
├── assets/               # 任务素材
└── tests/                # 测试文件
```

## Procedure

### 1. 确认任务和源码存在

```bash
# 确认任务目录
ls projects/webdev-long-horizon/tasks/<family>/<task-id>/

# 确认源码目录
ls projects/webdev-long-horizon/sources/<family>/<task-id>/
```

### 2. 打包并上传

```bash
python scripts/webdev-long-horizon/upload_to_remote.py --task <task-id>
```

此脚本自动完成：
- 打包源码、`assets/`、`tests/` 为 `<task-id>-source.tar.gz`
- 通过 SSH 上传到 `<remote_dir>/`
- 把 `task.md` 上传为 `<remote_dir>/<task-id>/PROMPT.md`
- 远程解压并整理出标准目录结构

### 3. 提示用户远程运行

上传完成后，提示用户在远程机器执行：

```bash
ssh <host> -p <port>
cd <remote_dir>/<task-id>/<task-id>

# 自动化运行需要 --dangerously-bypass-approvals-and-sandbox
codex exec -m gpt-5.6-sol \
  --dangerously-bypass-approvals-and-sandbox \
  < <remote_dir>/<task-id>/PROMPT.md \
  > <remote_dir>/<task-id>/sota.log 2>&1
```

### 4. 回收远程产物

运行结束后，一键拉回并整理产物：

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task <task-id> \
  --agent codex \
  --session <session-name>
```

产物整理到标准 session 目录：

```text
sessions/<session-name>/
  projects/webdev-long-horizon/
    submissions/<task-id>/codex/
      source/               # codex 修改后的源码
      screenshots/          # 关键状态截图
      sota.log              # 运行日志
```

也可以只拉回到当前目录：

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task <task-id> \
  --output ./
```

## 注意事项

- 上传前确保 `task.md` 已准备好作为提示词
- `task.md` 需明确告知 codex 源码位于 `./source`，参考截图位于 `assets/reference/`
- 若 mock 数据需要被源码读取，确保 `mock-data/` 已同时存在于任务目录和源码目录
- secrets.toml 中的密码等敏感信息已在 `.gitignore` 中排除，不会被打包上传

## 与其他 Skill 的关系

- 前置于 `webdev-sota-runner` skill 的远程运行模式
- 运行结束后使用 `evaluator` skill 对回收的产物进行评估
