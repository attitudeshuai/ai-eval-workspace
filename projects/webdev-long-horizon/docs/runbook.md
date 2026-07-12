# Web Dev 长程任务逐步执行 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于一步一步完成从任务创建到评估的全流程。

远程配置统一读取 `projects/webdev-long-horizon/config.toml` 和 `projects/webdev-long-horizon/secrets.toml` 中的 `[remote]` 段（`secrets.toml` 已加入 `.gitignore`，请勿提交）。连接信息（host/port/user/password）集中在 `secrets.toml`，`remote_dir` 和 `secrets_file` 在 `config.toml`。

下文示例中的 `<remote_dir>` 均指 `config.toml` 中 `[remote].remote_dir` 配置的值（当前默认 `/root/charles`）。若你修改了该值，请将示例中的 `<remote_dir>` 替换为实际路径。

> 对应技术细节见 [OPERATIONAL_WORKFLOW.md](./OPERATIONAL_WORKFLOW.md)。

---

## 通用启动语

如果你不想每次写完整指令，可以用：

```text
开始第 N 步：webdev-task-sxw-01.01，新增订单中心页面。
```

AI 会根据当前任务状态执行对应步骤。

---

## 前置依赖

确保已安装 Python 依赖：

```bash
pip install -r scripts/requirements.txt
```

---

## 第 1 步：创建任务骨架并继承父任务资产

### 指令模板

```text
基于 webdev-task-sxw-01 创建一个增量任务骨架。
- 标题：为本地生活平台新增订单中心页面
- 类别：电商 / 交易应用：O2O 服务 / 聚合平台
- 难度：medium
- arena tags：ui, e-commerce
- prompt type：前端
```

### AI 会执行

```bash
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "为本地生活平台新增订单中心页面" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --difficulty "medium" \
  --arena-tags "ui,e-commerce" \
  --prompt-type "前端" \
  --skip-starter \
  --parent webdev-task-sxw-01
```

此命令会一步完成以下操作：

1. 创建任务目录 `projects/webdev-long-horizon/tasks/webdev-task-sxw-01/webdev-task-sxw-01.01/`
2. 生成 `task.md`、`metadata.json`、`rubric.json`、`README.md`、`target_states.md` 骨架
3. 将父任务源码复制到 `projects/webdev-long-horizon/sources/webdev-task-sxw-01/webdev-task-sxw-01.01/` 作为 baseline
4. 复制父任务 `mock-data/` 到任务目录与 source 目录
5. 创建 `assets/`（含 `reference/` 子目录）、`screenshots/` 目录
6. 在 `metadata.json` 中写入 `parent_tasks`

生成目录示例：

```text
projects/webdev-long-horizon/
├── tasks/webdev-task-sxw-01/webdev-task-sxw-01.01/
│   ├── task.md
│   ├── metadata.json
│   ├── rubric.json
│   ├── README.md
│   ├── target_states.md
│   ├── assets/
│   │   └── reference/
│   ├── mock-data/
│   └── screenshots/
└── sources/webdev-task-sxw-01/webdev-task-sxw-01.01/
    ├── src/
    ├── package.json
    └── mock-data/
```

---

## 第 1B 步：准备 Greenfield 任务材料（用户手动）

用于 agent 需要**从零开始实现完整项目**的场景。**不需要运行 `create_task.py`**，只需手动准备材料。

### 你（用户）需要做的

在任务目录下放置两个文件：

```text
tasks/webdev-task-sxw-02/webdev-task-sxw-02/
├── README.md      # 项目说明（必填）
└── assets/        # 任务素材（必填）
    ├── reference/     # 参考截图
    ├── screenshots/   # 示例截图
    ├── icons/         # 图标（可选）
    └── images/        # 图片（可选）
```

**README.md 最低要求**：

```markdown
# 项目名称

## 技术栈
- Frontend: Vue 3 + Vite + Tailwind CSS
- Backend: Java Spring Boot + MyBatis（如无可省略）
- DB: MySQL 8.0（如无可省略）

## 快速启动
1. docker compose up --build
2. 访问 http://localhost:3000

## 功能介绍
- 功能 A
- 功能 B
- ...

## 项目结构
PetAdoption/
├── frontend/
├── backend/
└── docker-compose.yml
```

### 指令模板

把材料放好后，只需告诉 AI：

```text
webdev-task-sxw-02 的材料已准备好，帮我生成任务资产。
```

AI 会读取 `README.md` 和 `assets/`，自动生成 `task.md`、`metadata.json`、`rubric.json`、`target_states.md` 和 `tests/`。

---

## 第 2 步：生成任务资产

### 增量任务

```text
为 webdev-task-sxw-01.01 生成完整任务资产。
- 基于父任务 webdev-task-sxw-01 的源码分析现有技术栈
- 填充 task.md（直接作为 SOTA 提示词），明确新增订单中心页面需求
- 完善 rubric.json
- 完善 target_states.md
- 补充 mock-data/orders.json
- 生成 assets/reference/ 参考截图
```

### Greenfield 任务

```text
webdev-task-sxw-02 的材料已准备好，帮我生成任务资产。
```

AI 会读取用户提供的 `README.md` 和 `assets/`，自动生成：

### AI 会执行

| 增量               | Greenfield                         | 文件                                 |
| ------------------ | ---------------------------------- | ------------------------------------ |
| 基于父任务源码分析 | 基于 README.md 提取技术栈/功能     | `task.md`                          |
| 10-20 叶节点       | 10-20 叶节点                       | `rubric.json`                      |
| 4+ 关键状态        | 4+ 关键状态                        | `target_states.md`                 |
| 补充导航链接       | 补充快速导航和验收标准             | `README.md`                        |
| 补充新数据         | 基于 README 功能生成 mock 数据     | `mock-data/`                       |
| 11 个验收用例      | 基于功能列表生成验收用例           | `tests/playwright.spec.ts`         |
| —                 | 基于 README 技术栈描述生成 starter | `sources/{prefix}-02/{prefix}-02/` |

---

## 第 2.5 步：准备源码 baseline（Greenfield 专用）

增量任务已继承父任务源码，**可跳过此步**。

Greenfield 任务在"第 2 步：生成任务资产"时，AI 会基于 README 中的技术栈描述自动生成 starter 到 `sources/{prefix}-XX/{prefix}-XX/`。如果你有自己的 starter 源码，也可以手动放入该目录。

```bash
# 方式 A：AI 自动生成（推荐）
# 无需手动操作，AI 在第 2 步完成后自动生成

# 方式 B：手动放入
cp -r /path/to/your-starter/* projects/webdev-long-horizon/sources/webdev-task-sxw-02/webdev-task-sxw-02/
```

- 实现所有功能并确保可构建、可运行

`upload_to_remote.py` 会把这个空目录、提示词文件、`assets/`、`tests/` 传到 remote，codex 会在 `<remote_dir>/webdev-task-02/` 下从零创建项目。

> 注意：方式 B 对 `task.md` 要求更高，必须包含“从零创建项目”的明确指令和验收标准。

---

## 第 3 步：本地校验

### 指令模板

```text
校验 webdev-task-sxw-01.01 是否通过 validate_task.py。
```

### AI 会执行

```bash
python scripts/webdev-long-horizon/validate_task.py --allow-no-starter webdev-task-sxw-01.01
```

---

## 第 4 步：打包并上传到 remote

### 指令模板

```text
把 webdev-task-sxw-01.01 的源码、task.md、assets/ 和 tests/ 上传到 remote。
```

### AI 会执行

```bash
python scripts/webdev-long-horizon/upload_to_remote.py --task webdev-task-sxw-01.01
```

此脚本会：

1. 打包源码、`assets/`、`tests/` 为 `webdev-task-sxw-01.01-source.tar.gz`
2. 通过 SSH 上传到 `<remote_dir>/`
3. 把 `task.md` 作为提示词上传到 `<remote_dir>/webdev-task-sxw-01.01/PROMPT.md`
4. 远程解压并整理出：
   - `<remote_dir>/webdev-task-sxw-01.01/`（源码）
   - `<remote_dir>/webdev-task-sxw-01.01/assets/`
   - `<remote_dir>/webdev-task-sxw-01.01/tests/`

其他任务资产（`rubric.json`、`target_states.md`、`README.md` 等）保留在本地，不上传。
远程配置读取 `config.toml` 和 `secrets.toml`。

---

## 第 5 步：remote 运行 codex

### 指令模板

```text
在 remote 上运行 codex-cli 执行 webdev-task-sxw-01.01，模型用 gpt-5.6-sol。
```

### AI 会执行

```bash
ssh root@59.49.28.154 -p 7826
cd <remote_dir>/webdev-task-sxw-01.01/source

# 自动化运行需要 --dangerously-bypass-approvals-and-sandbox
# 若手动交互运行，可去掉该参数
# 建议把输出重定向到 <remote_dir>/<task-id>/sota-run.md，方便后续回收
codex exec -m gpt-5.6-sol \
  --dangerously-bypass-approvals-and-sandbox \
  < <remote_dir>/webdev-task-sxw-01.01/PROMPT.md \
  > <remote_dir>/webdev-task-sxw-01.01/sota-run.md 2>&1
```

> 注意：此步骤可能耗时较长。AI 会把命令给你，你可以选择自己盯着跑，或让 AI 后台运行并等待完成。

---

## 第 6 步：回收产物

### 指令模板

```text
把 webdev-task-sxw-01.01 在 remote 上的产物拉回本地，整理到 session 目录。
- session 名：session-sota-2026-07-01.01-codex
```

### AI 会执行

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task webdev-task-sxw-01.01 \
  --agent codex \
  --session session-sota-2026-07-01.01-codex
```

产物整理到：

```text
sessions/session-sota-2026-07-01.01-codex/
  projects/webdev-long-horizon/
    submissions/webdev-task-sxw-01.01/codex/
      source/
      screenshots/
      sota.log
```

---

## 第 7 步：评估

### 指令模板

```text
评估 webdev-task-sxw-01.01 的 codex 运行结果。
- session：session-sota-2026-07-01.01-codex
```

### AI 会执行

```bash
python scripts/webdev-long-horizon/evaluate_task.py \
  --session session-sota-2026-07-01.01-codex \
  --project webdev-long-horizon \
  --task webdev-task-sxw-01.01 \
  --agent codex
```

然后基于 `rubric.json` 逐项分析产物，生成评估报告：

```text
sessions/session-sota-2026-07-01.01-codex/
  projects/webdev-long-horizon/
    reports/webdev-task-sxw-01.01/codex/
      report.json
      report.md
```

---

## 第 8 步：整理最终交付资产

### 指令模板

```text
把 webdev-task-sxw-01.01 的最终交付资产打包好：
- 任务资产（task.md、metadata.json、rubric.json、assets、mock-data、tests 等）
- starter/：初始项目代码
- screenshots/：人工验证后放置的关键状态截图（可选）
- 输出到 deliverables/webdev-task-sxw-01.01.tar.gz
```

### AI 会执行

```bash
python scripts/webdev-long-horizon/package_deliverable.py \
  --task webdev-task-sxw-01.01 \
  --session session-sota-2026-07-01.01-codex \
  --agent codex
```

交付包结构（tar.gz 解压后）：

```text
webdev-task-sxw-01.01/
├── task.md              # 任务需求
├── metadata.json        # 任务元数据
├── README.md            # 启动与测试说明
├── rubric.json          # 验收标准
├── target_states.md     # 关键状态说明
├── sota-run.md          # SOTA 运行记录
├── starter/             # 初始项目代码
├── assets/              # 任务素材（参考截图放 assets/reference/，其他按类型分子目录）
├── mock-data/           # mock 数据
├── tests/               # Playwright / 单元测试骨架
└── screenshots/         # 人工验证后放置的关键状态截图（可选）
```

打包结果：

```text
deliverables/webdev-long-horizon/webdev-task-sxw-01.01.tar.gz
```

---

## 完整流程一次性指令

如果你想一次性说完：

### 增量任务

```text
帮我全流程跑一个基于 webdev-task-sxw-01 的增量任务：
1. 创建任务并继承父源码：新增订单中心页面，标题"为本地生活平台新增订单中心页面"，medium 难度
2. 生成/填充 task.md、rubric.json、mock-data、assets/reference/
3. 把源码、task.md、assets/、tests/ 上传到 <remote_dir>/ 远程目录
4. 在 remote 上用 codex-cli 运行（模型 gpt-5.6-sol）
5. 运行完成后把产物拉回本地，整理到标准 session 目录
6. 基于 rubric.json 生成评估报告
7. 把任务资产、starter/ 和 SOTA 最终截图打包成最终交付包 deliverables/webdev-long-horizon/webdev-task-sxw-01.01.tar.gz
```

### Greenfield 任务（无源码）

```text
帮我全流程跑一个 Greenfield 任务：
1. 创建无源码任务骨架：支持拖拽看板的任务管理系统，标题"支持拖拽看板的任务管理系统"，high 难度
2. 生成/填充 task.md、rubric.json、mock-data、assets/reference/（source 目录保持为空）
3. 把空的 source 目录、task.md、assets/、tests/ 上传到 <remote_dir>/ 远程目录
4. 在 remote 上用 codex-cli 运行（模型 gpt-5.6-sol），让 agent 从零创建完整项目
5. 运行完成后把产物拉回本地，整理到标准 session 目录
6. 基于 rubric.json 生成评估报告
7. 把任务资产、starter/ 和 SOTA 最终截图打包成最终交付包 deliverables/webdev-long-horizon/webdev-task-02.tar.gz
```
