# webdev-long-horizon 项目实操流程

> 本文档描述在 `webdev-long-horizon` 项目中，如何准备任务资产、运行 SOTA、评估并交付的完整实操流程。
> 本文件位于 `projects/webdev-long-horizon/` 下。

---

## 前置条件

- 本地已 clone `ai-eval-workspace` 仓库
- 远程机器：`ssh root@59.49.28.154 -p 7826`
- 远程机器已安装并配置好 `codex cli`
- 远程机器使用模型：`gpt-5.6-sol`
- Python 环境已安装 `scripts/requirements.txt`

---

## 一、本地准备任务资产

### 1.1 创建任务

本项目支持两种任务创建模式。两种模式都使用 `--skip-starter`，源码与任务元数据分离管理。

> **与传统流程的区别**：不再在 `tasks/<task-id>/starter/` 中放源码，而是统一放到 `projects/webdev-long-horizon/sources/<family>/<task-id>/`（目录名与任务 ID 一致）。任务按家族分组，例如 `tasks/webdev-task-01/webdev-task-01.01/`。

#### 模式一：基于现有源码生成增量开发任务

你已有可运行项目源码，希望 agent 在其基础上实现新功能。

```bash
# 1. 创建任务骨架（不带 starter）并自动继承父任务资产。
#    基于已有任务 webdev-task-01，会自动生成 webdev-task-01.01，并完成以下四步：
#    - 创建任务目录 tasks/webdev-task-01/webdev-task-01.01/，生成 task.md 等骨架
#    - 将父任务源码复制到 sources/webdev-task-01/webdev-task-01.01/ 作为 baseline
#    - 复制父任务 mock-data/ 到任务目录与 source 目录
#    - 创建 assets/、screenshots/ 目录，并在 metadata.json 中写入 parent_tasks
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "为电商后台增加订单筛选与导出" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --difficulty "high" \
  --arena-tags "ui,e-commerce,visualize" \
  --prompt-type "前端" \
  --skip-starter \
  --parent webdev-task-01

# 假设生成任务 ID：webdev-task-01.01

# 2. AI 分析源码并填充 task.md / rubric.json / README.md / target_states.md
# 3. 补充 mock-data/ 数据（如新增 orders.json），确保 tasks/ 与 sources/ 下保持一致
# 4. 准备 assets/ 参考截图

# 5. 生成 PROMPT.md（用于 SOTA / 远程 codex 运行）
#    python scripts/webdev-long-horizon/compose_prompt.py \
#      --project webdev-long-horizon \
#      --task webdev-task-01.01
#    若 compose_prompt.py 不存在，手动复制 templates/PROMPT.md 并替换 {{task_md}}

# 6. 校验任务
python scripts/webdev-long-horizon/validate_task.py \
  --allow-no-starter \
  webdev-task-01.01

# 7. 运行 SOTA
python scripts/webdev-long-horizon/run_sota.py \
  --session session-sota-2026-07-002-codex \
  --project webdev-long-horizon \
  --task webdev-task-01.01 \
  --agent codex

# 8. 生成评估报告
python scripts/webdev-long-horizon/evaluate_task.py \
  --session session-sota-2026-07-002-codex \
  --project webdev-long-horizon \
  --task webdev-task-01.01 \
  --agent codex
```

#### 模式二：根据需求生成从零开发任务

你只有自然语言需求，任务要求 agent 从零实现完整项目。

```bash
# 1. 创建任务骨架（不带 starter）
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "支持拖拽看板的任务管理系统" \
  --category "交互型应用：可视化 / 数据看板" \
  --difficulty "high" \
  --arena-tags "ui,visualize,drag-drop" \
  --prompt-type "前端" \
  --skip-starter

# 假设生成任务 ID：webdev-task-02
# 2. AI 根据需求生成 task.md / rubric.json / README.md / target_states.md
# 3. 准备 assets/ 参考截图与 mock-data/ 数据
# 4. 生成 PROMPT.md（用于 SOTA / 远程 codex 运行）
#    python scripts/webdev-long-horizon/compose_prompt.py \
#      --project webdev-long-horizon \
#      --task webdev-task-02
#    若 compose_prompt.py 不存在，手动复制 templates/PROMPT.md 并替换 {{task_md}}

# 5. 处理源码（二选一）
# 方式 A：你提供 starter 源码
cp -r /path/to/your-kanban-starter/* \
  projects/webdev-long-horizon/sources/webdev-task-02/webdev-task-02/

# 方式 B：AI 生成初始 starter 放到 tasks/<task-id>/starter/
# 此时不需要 --allow-no-starter

# 6. 校验任务
python scripts/webdev-long-horizon/validate_task.py \
  --allow-no-starter \
  webdev-task-02

# 7. 运行 SOTA
python scripts/webdev-long-horizon/run_sota.py \
  --session session-sota-2026-07-003-codex \
  --project webdev-long-horizon \
  --task webdev-task-02 \
  --agent codex

# 8. 生成评估报告
python scripts/webdev-long-horizon/evaluate_task.py \
  --session session-sota-2026-07-003-codex \
  --project webdev-long-horizon \
  --task webdev-task-02 \
  --agent codex
```

> **源码目录约定**：创建任务后，在 `projects/webdev-long-horizon/tasks/<family>/` 下生成任务目录（如 `tasks/webdev-task-01/webdev-task-01.01/`）。源码按约定放到 `projects/webdev-long-horizon/sources/<family>/<task-id>/`，目录名与任务 ID 保持一致。

### 1.2 填充任务内容

每个任务目录必须包含以下文件：

```text
projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01.01/
├── task.md              # 任务需求主文档
├── metadata.json        # 任务元数据
├── README.md            # 启动与测试说明
├── rubric.json          # 验收标准
├── PROMPT.md            # SOTA / 远程 codex 使用的提示词
├── target_states.md     # 关键状态说明（建议）
├── sota-run.md          # SOTA 运行记录（建议）
├── assets/              # 参考截图、素材
├── mock-data/           # mock 数据
└── tests/               # Playwright / 单元测试
```

源码有两种管理方式，任选其一：

- **内置 starter**：`tasks/webdev-task-01/webdev-task-01.01/starter/`（传统）
- **外部 source**：`sources/webdev-task-01/webdev-task-01.01/`（推荐，目录名与任务 ID 保持一致）

> 推荐将源码放到 `projects/webdev-long-horizon/sources/<family>/<task-id>/`，这样 `run_sota.py` 和校验脚本都能自动识别，无需额外传 `--source-dir`。

#### task.md 必填内容

- 背景与目标
- 功能要求（分模块、分页面）
- 交互要求
- 视觉要求
- 约束条件
- 交付标准

#### rubric.json 格式

复用 `webdev-task-01` 的 `dimensions + leaves` 结构：

- 6 大维度：功能完整性、交互完整性、视觉完成度、工程质量、边界状态、测试与证据
- 10-20 个叶节点
- 每个叶节点包含 `id`、`criterion`、`weight`、`grader_spec`、`evidence_required`

### 1.3 初始化 starter 依赖

若使用内置 starter：

```bash
cd projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01.01/starter
npm install
```

若使用外部 source：

```bash
cd projects/webdev-long-horizon/sources/webdev-task-01/webdev-task-01.01
npm install
```

建议提交前生成 `package-lock.json`，保证远程复现一致。

### 1.4 本地验证

```bash
# 1. 启动源码，确认可运行
npm run dev

# 2. 运行项目校验（若使用外部 source，加 --allow-no-starter）
python scripts/webdev-long-horizon/validate_task.py \
  --allow-no-starter \
  webdev-task-01.01

# 3. 可选：全项目批量校验
python scripts/webdev-long-horizon/validate_project.py \
  --project webdev-long-horizon \
  --tasks \
  --allow-no-starter
```

---

## 二、远程配置

在 `projects/webdev-long-horizon/config.toml` 中配置远程机器：

```toml
[remote]
host = "59.49.28.154"
port = "7826"
user = "root"
remote_dir = "/root/charles"
secrets_file = "secrets.toml"
```

在 `projects/webdev-long-horizon/secrets.toml` 中配置密码（已加入 `.gitignore`）：

```toml
[remote]
password = "your-password"
```

---

## 三、上传源码和 PROMPT.md 到远程机器

任务资产（`task.md`、`rubric.json`、`assets/`、`tests/` 等）是本地最终交付产物，**不上传到远程**。远程只需要源码和 `PROMPT.md`。

使用 `upload_to_remote.py` 一键上传：

```bash
python scripts/webdev-long-horizon/upload_to_remote.py --task webdev-task-01.01
```

此脚本会：

1. 打包源码为 `webdev-task-01.01-source.tar.gz`（自动排除 `node_modules`、`.git` 等）
2. 通过 SSH 上传到 `/root/charles/`
3. 把 `PROMPT.md` 上传到 `/root/charles/webdev-task-01.01/PROMPT.md`
4. 远程解压并整理出 `/root/charles/webdev-task-01.01/source/`

> 远程配置从 `config.toml` 和 `secrets.toml` 读取。
> 若源码来自内置 starter，请先放到 `sources/<family>/<task-id>/` 再上传。

---

## 四、远程运行 SOTA

### 4.1 单任务运行

```bash
ssh root@59.49.28.154 -p 7826
cd /root/charles/webdev-task-01.01/source

# 自动化运行需要 --dangerously-bypass-approvals-and-sandbox
# 若手动交互运行，可去掉该参数
codex exec -m gpt-5.6-sol \
  --dangerously-bypass-approvals-and-sandbox \
  < /root/charles/webdev-task-01.01/PROMPT.md
```

> 源码目录为 `/root/charles/webdev-task-01.01/source/`，PROMPT 文件在 `/root/charles/webdev-task-01.01/PROMPT.md`。

### 4.2 使用 task.md 运行（不推荐）

如果没有生成 `PROMPT.md`，可临时使用 `task.md`，但需在命令或对话中明确交付要求：

```bash
# 自动化运行需要 --dangerously-bypass-approvals-and-sandbox
codex exec -m gpt-5.6-sol \
  --dangerously-bypass-approvals-and-sandbox \
  < /root/charles/webdev-task-01.01/task.md
```

### 4.3 Prompt 中必须包含的交付要求

无论用 `task.md` 还是 `PROMPT.md`，都要明确告诉 codex：

1. 项目代码在 `./source` 或当前目录
2. 先执行 `npm install && npm run dev`
3. 按需求完成所有功能
4. 保存关键状态截图到 `./screenshots/`
5. 运行测试并保存结果
6. 不修改任务原始目录中的文件

> 使用外部 source 时，`run_sota.py` 会自动将 `projects/webdev-long-horizon/sources/<task-id>/` 复制到 session 的 `./source/` 下。

### 4.4 批量运行 SOTA

当任务数量多时，在远程机器上使用循环脚本：

```bash
#!/bin/bash
# /root/charles/batch_run_sota.sh

TASKS_DIR=/root/charles
for task_dir in $TASKS_DIR/webdev-task-*; do
  task_id=$(basename $task_dir)
  echo "=== Running SOTA for $task_id ==="
  cd $task_dir/source
  codex exec -m gpt-5.6-sol \
    --dangerously-bypass-approvals-and-sandbox \
    < $task_dir/PROMPT.md \
    > $task_dir/sota.log 2>&1
  cd /root/charles
done
```

执行：

```bash
chmod +x /root/charles/batch_run_sota.sh
/root/charles/batch_run_sota.sh
```

> 注意：codex cli 的具体参数可能因版本不同而略有差异，请以远程机器上实际安装的版本为准。

### 4.5 源码查找优先级

`run_sota.py` 按以下优先级确定任务源码：

1. `--source-dir` 显式指定目录
2. `projects/webdev-long-horizon/sources/<family>/<task-id>/`
3. `projects/webdev-long-horizon/tasks/<family>/<task-id>/starter/`

> 推荐将源码放到 `sources/<family>/<task-id>/`，目录名与任务 ID 保持一致，这样无需额外传 `--source-dir`。

---

## 五、回收 SOTA 产物

使用 `scripts/fetch_remote_results.py` 一键回收并整理产物：

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task webdev-task-01.01 \
  --agent codex \
  --session session-sota-YYYY-MM-NNN-codex
```

产物会被自动整理到标准 session 目录：

```text
sessions/session-sota-YYYY-MM-NNN-codex/
  projects/webdev-long-horizon/
    submissions/webdev-task-01.01/codex/
      source/               # codex 修改后的源码
      screenshots/          # 关键状态截图
      sota.log              # 运行日志
```

也可以只拉回到当前目录：

```bash
python scripts/webdev-long-horizon/fetch_remote_results.py \
  --task webdev-task-01.01 \
  --output ./
```

### 5.1 手动回收（备选）

如果脚本不可用，可手动打包拉回：

```bash
ssh root@59.49.28.154 -p 7826 "cd /root/charles && tar czvf webdev-task-01.01-results.tar.gz webdev-task-01.01"
scp -P 7826 root@59.49.28.154:/root/charles/webdev-task-01.01-results.tar.gz ./
tar xzvf webdev-task-01.01-results.tar.gz
```

---

## 六、本地评估

### 6.1 生成评估报告

将产物放到标准 session 目录下，例如：

```text
sessions/session-sota-2026-07-XXX-codex/
  projects/webdev-long-horizon/
    submissions/webdev-task-01.01/codex/
      source/           # 对应修改后的 starter / source
      screenshots/
      sota.log
```

运行评估：

```bash
python scripts/webdev-long-horizon/evaluate_task.py \
  --session session-sota-2026-07-XXX-codex \
  --project webdev-long-horizon \
  --task webdev-task-01.01 \
  --agent codex
```

评估报告生成在：

```text
sessions/session-sota-2026-07-XXX-codex/
  projects/webdev-long-horizon/
    reports/webdev-task-01.01/codex/
      report.json
      report.md
```

### 6.2 汇总多个任务

```bash
python scripts/webdev-long-horizon/generate_report.py \
  --session session-sota-2026-07-XXX-codex
```

汇总结果会更新到：

- `benchmarks/global/summary.csv`
- `benchmarks/global/leaderboard.md`
- `benchmarks/by-project/webdev-long-horizon/summary.csv`

---

## 七、最终交付

最终交付内容统一打包为：

```text
deliverables/webdev-long-horizon/webdev-task-01.01.tar.gz
```

交付包结构（tar.gz 解压后）：

```text
webdev-task-01.01/
├── task.md              # 任务需求
├── metadata.json        # 任务元数据
├── README.md            # 启动与测试说明
├── rubric.json          # 验收标准
├── target_states.md     # 关键状态说明
├── sota-run.md          # SOTA 运行记录
├── assets/              # 参考截图与素材
├── mock-data/           # mock 数据
├── tests/               # 测试骨架
└── sota/                # SOTA 产物
    ├── source/          # 从远端拉下来的 agent 修改后源码
    ├── screenshots/     # agent 输出的关键状态截图
    ├── sota.log         # 运行日志
    ├── PROMPT.md        # 使用的提示词
    └── report/          # 评估报告
        ├── report.json
        └── report.md
```

使用 `package_deliverable.py` 一键打包：

```bash
python scripts/webdev-long-horizon/package_deliverable.py \
  --task webdev-task-01.01 \
  --session session-sota-2026-07-01.01-codex \
  --agent codex
```

> **注意**：交付包中的源码是 `sota/source/`，即从远端拉回来的 agent 修改后源码，而不是初始 baseline。初始 baseline 仍保留在 `projects/webdev-long-horizon/sources/<family>/<task-id>/`。

交付前自检清单：

- [ ] `task.md` 完整，无泄露答案
- [ ] `PROMPT.md` 已生成，明确源码位置与交付要求
- [ ] `sota/source/` 可 `npm install && npm run dev` 直接运行
- [ ] `rubric.json` 包含 10-20 个叶节点，覆盖六维度
- [ ] `assets/` 包含桌面端和移动端参考截图
- [ ] `mock-data/` 数据完整
- [ ] `tests/` 测试骨架完整
- [ ] 已通过 `validate_task.py` 校验
- [ ] 已跑过至少一次 SOTA 可解性测试
- [ ] `deliverables/<task-id>.tar.gz` 已生成

---

## 八、常见问题

### Q1: `tasks/` 目录被 gitignore 后，任务资产如何备份？

任务资产不提交 GitHub，通过以下方式备份/同步：

- 压缩包交付到指定位置
- 内部网盘 / 对象存储
- 远程机器上的 `/root/` 目录保留副本

### Q2: 如何批量创建多个任务？

准备一个任务清单文件，例如 `task-queue.yaml`：

```yaml
tasks:
  - title: "任务 A"
    category: "电商 / 交易应用：O2O 服务 / 聚合平台"
    difficulty: "high"
    arena_tags: ["ui", "e-commerce"]
  - title: "任务 B"
    category: "交互型应用：可视化 / 数据看板"
    difficulty: "high"
    arena_tags: ["visualize", "dashboard"]
```

然后批量创建：

```bash
python scripts/webdev-long-horizon/batch_create_tasks.py \
  --project webdev-long-horizon \
  --batch task-queue.yaml
```

> `batch_create_tasks.py` 目前不存在，如需可后续实现。

### Q3: codex cli 参数怎么查？

在远程机器上执行：

```bash
codex --help
```

---

## 九、相关命令速查

| 目的                    | 命令                                                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 创建顶层任务骨架        | `python scripts/webdev-long-horizon/create_task.py --project webdev-long-horizon --title "..." --category "..." --skip-starter`                              |
| 创建增量任务骨架        | `python scripts/webdev-long-horizon/create_task.py --project webdev-long-horizon --title "..." --category "..." --skip-starter --parent webdev-task-01`     |
| 验证任务（外部 source） | `python scripts/webdev-long-horizon/validate_task.py --allow-no-starter webdev-task-01.01`                                                                   |
| 验证项目                | `python scripts/webdev-long-horizon/validate_project.py --project webdev-long-horizon --tasks --allow-no-starter`                                            |
| 打包任务元数据          | `tar czvf webdev-task-01.01.tar.gz -C projects/webdev-long-horizon/tasks/webdev-task-01 webdev-task-01.01`                               |
| 打包源码                | `tar czvf webdev-task-01.01-source.tar.gz -C projects/webdev-long-horizon/sources/webdev-task-01 webdev-task-01.01`                    |
| 打包最终交付资产        | `python scripts/webdev-long-horizon/package_deliverable.py --task webdev-task-01.01 --session <session> --agent codex`                                      |
| 上传远程                | `scp -P 7826 webdev-task-01.01.tar.gz root@59.49.28.154:/root/charles/`                                                                  |
| 运行 SOTA               | `python scripts/webdev-long-horizon/run_sota.py --session <session> --project webdev-long-horizon --task webdev-task-01.01 --agent codex`                    |
| 运行 SOTA（指定源码）   | `python scripts/webdev-long-horizon/run_sota.py --session <session> --project webdev-long-horizon --task webdev-task-01.01 --agent codex --source-dir <path>` |
| 回收远程产物            | `python scripts/webdev-long-horizon/fetch_remote_results.py --task webdev-task-01.01 --agent codex --session <session>`                                      |
| 生成评估报告            | `python scripts/webdev-long-horizon/evaluate_task.py --session <session> --project webdev-long-horizon --task webdev-task-01.01 --agent codex`               |
| 汇总报告                | `python scripts/webdev-long-horizon/generate_report.py --session <session>`                                                                                  |
