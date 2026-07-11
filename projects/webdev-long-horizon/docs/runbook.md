# Web Dev 长程任务逐步执行 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于一步一步完成从任务创建到评估的全流程。

远程配置统一读取 `projects/webdev-long-horizon/config.toml` 中的 `[remote]` 段，密码读取 `projects/webdev-long-horizon/secrets.toml`（已加入 `.gitignore`，请勿提交）。

> 对应技术细节见 [OPERATIONAL_WORKFLOW.md](./OPERATIONAL_WORKFLOW.md)。

---

## 通用启动语

如果你不想每次写完整指令，可以用：

```text
开始第 N 步：webdev-task-01.01，新增订单中心页面。
```

AI 会根据当前任务状态执行对应步骤。

---

## 前置依赖

确保已安装 Python 依赖：

```bash
pip install -r scripts/requirements.txt
```

---

## 第 1 步：创建任务骨架

### 指令模板

```text
基于 webdev-task-01 创建一个增量任务骨架。
- 标题：为本地生活平台新增订单中心页面
- 类别：电商 / 交易应用：O2O 服务 / 聚合平台
- 难度：medium
- arena tags：ui, e-commerce
- prompt type：前端
```

### AI 会执行

```bash
python scripts/create_task.py \
  --project webdev-long-horizon \
  --title "为本地生活平台新增订单中心页面" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --difficulty "medium" \
  --arena-tags "ui,e-commerce" \
  --prompt-type "前端" \
  --skip-starter \
  --parent webdev-task-01
```

生成目录：

```text
projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01.01/
```

---

## 第 2 步：生成任务资产

### 指令模板

```text
为 webdev-task-01.01 生成完整任务资产。
- 基于父任务 webdev-task-01 的源码分析现有技术栈
- 生成 task.md，明确新增订单中心页面需求
- 生成 PROMPT.md
- 生成 rubric.json
- 生成 target_states.md
- 生成 mock-data/orders.json
- 生成 assets/ 参考截图
```

### AI 会执行

分析 `sources/webdev-task-01/webdev-task-01/` 源码，然后生成：

- `tasks/webdev-task-01/webdev-task-01.01/task.md`
- `tasks/webdev-task-01/webdev-task-01.01/PROMPT.md`
- `tasks/webdev-task-01/webdev-task-01.01/rubric.json`
- `tasks/webdev-task-01/webdev-task-01.01/target_states.md`
- `tasks/webdev-task-01/webdev-task-01.01/README.md`
- `tasks/webdev-task-01/webdev-task-01.01/mock-data/orders.json`
- `tasks/webdev-task-01/webdev-task-01.01/tests/playwright.spec.ts`
- `tasks/webdev-task-01/webdev-task-01.01/assets/` 参考截图

并将 mock-data 同步复制到源码目录：

```text
sources/webdev-task-01/webdev-task-01.01/mock-data/
```

---

## 第 3 步：复制父源码作为 baseline

### 指令模板

```text
把 webdev-task-01 的源码复制到 webdev-task-01.01 的 source 目录。
```

### AI 会执行

```bash
cp -r projects/webdev-long-horizon/sources/webdev-task-01/webdev-task-01/* \
  projects/webdev-long-horizon/sources/webdev-task-01/webdev-task-01.01/
```

---

## 第 4 步：本地校验

### 指令模板

```text
校验 webdev-task-01.01 是否通过 validate_task.py。
```

### AI 会执行

```bash
python scripts/validate_task.py --allow-no-starter webdev-task-01.01
```

---

## 第 5 步：打包并上传到 remote

### 指令模板

```text
把 webdev-task-01.01 打包并上传到 remote。
```

### AI 会执行

```bash
python scripts/upload_to_remote.py --task webdev-task-01.01
```

此脚本会：
1. 打包任务资产为 `webdev-task-01.01.tar.gz`
2. 打包源码为 `webdev-task-01.01-source.tar.gz`
3. 通过 SSH 上传到 `/root/charles/`
4. 远程解压并整理出 `/root/charles/webdev-task-01.01/source/`

远程配置读取 `config.toml` 和 `secrets.toml`。

---

## 第 6 步：remote 运行 codex

### 指令模板

```text
在 remote 上运行 codex-cli 执行 webdev-task-01.01，模型用 gpt-5.6-sonnet。
```

### AI 会执行

```bash
ssh root@59.49.28.154 -p 7826
cd /root/charles/webdev-task-01.01/source

codex \
  --model gpt-5.6-sonnet \
  --prompt-file /root/charles/webdev-task-01.01/PROMPT.md
```

> 注意：此步骤可能耗时较长。AI 会把命令给你，你可以选择自己盯着跑，或让 AI 后台运行并等待完成。

---

## 第 7 步：回收产物

### 指令模板

```text
把 webdev-task-01.01 在 remote 上的产物拉回本地，整理到 session 目录。
- session 名：session-sota-2026-07-01.01-codex
```

### AI 会执行

```bash
python scripts/fetch_remote_results.py \
  --task webdev-task-01.01 \
  --agent codex \
  --session session-sota-2026-07-01.01-codex
```

产物整理到：

```text
sessions/session-sota-2026-07-01.01-codex/
  projects/webdev-long-horizon/
    submissions/webdev-task-01.01/codex/
      source/
      screenshots/
      sota.log
```

---

## 第 8 步：评估

### 指令模板

```text
评估 webdev-task-01.01 的 codex 运行结果。
- session：session-sota-2026-07-01.01-codex
```

### AI 会执行

```bash
python scripts/evaluate_task.py \
  --session session-sota-2026-07-01.01-codex \
  --project webdev-long-horizon \
  --task webdev-task-01.01 \
  --agent codex
```

然后基于 `rubric.json` 逐项分析产物，生成评估报告：

```text
sessions/session-sota-2026-07-01.01-codex/
  projects/webdev-long-horizon/
    reports/webdev-task-01.01/codex/
      report.json
      report.md
```

---

## 完整流程一次性指令

如果你想一次性说完：

```text
帮我全流程跑一个基于 webdev-task-01 的增量任务：
1. 创建任务：新增订单中心页面，标题"为本地生活平台新增订单中心页面"，medium 难度
2. 生成 task.md、PROMPT.md、rubric.json、mock-data、assets
3. 打包并上传到 /root/charles/ 远程目录
4. 在 remote 上用 codex-cli 运行（模型 gpt-5.6-sonnet）
5. 运行完成后把产物拉回本地，整理到标准 session 目录
6. 基于 rubric.json 生成评估报告
```
