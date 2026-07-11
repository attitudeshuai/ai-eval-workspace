# 任务模板使用指南

本指南说明如何在 `webdev-long-horizon` 项目下创建符合规范的新任务。

**注意**：这些模板仅属于 `webdev-long-horizon` 项目，其他项目无需遵循。

---

## 1. 快速创建

### 1.1 创建顶层任务

```bash
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "复杂 O2O 服务聚合平台" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --difficulty "high" \
  --arena-tags "ui,map,e-commerce,visualize" \
  --prompt-type "前端" \
  --skip-starter
```

生成目录：`projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01/`

### 1.2 创建增量任务

```bash
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "为本地生活平台新增订单中心页面" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --difficulty "medium" \
  --arena-tags "ui,e-commerce" \
  --prompt-type "前端" \
  --skip-starter \
  --parent webdev-task-01
```

生成目录：`projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01.01/`

> `--category` 请使用 `categories.json` 中的中文 `label`，不要直接使用英文 id。

脚本会读取 `projects/webdev-long-horizon/templates/` 下的模板，生成新任务目录。

---

## 2. 模板文件说明

模板全部位于 `projects/webdev-long-horizon/templates/`：

### 2.1 `templates/task/task.md`

任务需求主文档。必须包含：

- 背景与目标
- 功能要求（分模块、分页面）
- 交互要求
- 视觉要求
- 约束条件
- 交付标准

### 2.2 `templates/task/metadata.json`

任务元数据：

```json
{
  "task_id": "webdev-task-01",
  "title": "复杂 O2O 服务聚合平台",
  "category_tags": ["电商 / 交易应用：O2O 服务 / 聚合平台"],
  "arena_tags": ["ui", "map", "e-commerce", "visualize"],
  "prompt_type": "前端",
  "required_tools": ["browser", "playwright", "screenshot"],
  "difficulty": "high",
  "annotator": "",
  "reviewer": "",
  "status": "draft",
  "version": "0.1.0"
}
```

### 2.3 `templates/task/README.md`

说明启动方式、测试方式、目录结构、已知限制。

### 2.4 `templates/task/rubric.json`

验收标准，按 `dimensions` 组织，每个 dimension 下包含若干 `leaves` 叶节点。

### 2.5 `templates/task/target_states.md`

列出必须验收的关键状态。

### 2.6 `templates/task/sota-run.md`

SOTA 运行记录表。

### 2.7 `templates/starter/`

初始项目模板，基于 Vite + React + TypeScript + Tailwind CSS。

### 2.8 `templates/PROMPT.md`

SOTA 运行时使用的 prompt 模板。`run_sota.py` 会优先读取项目级 `templates/PROMPT.md`，将 `{{task_md}}` 替换为实际任务内容，生成任务目录下的 `PROMPT.md`。

如果你要把任务上传到 remote 用 codex 直接运行，必须生成具体的 `PROMPT.md`：

```bash
python scripts/webdev-long-horizon/compose_prompt.py \
  --project webdev-long-horizon \
  --task webdev-task-01.01
```

> 若 `compose_prompt.py` 不存在，可手动复制 `templates/PROMPT.md` 到任务目录，并将 `{{task_md}}` 替换为 `task.md` 内容。

---

## 3. 目录命名规范

- 项目 ID：`webdev-long-horizon`
- 任务 ID：
  - 顶层任务：`webdev-task-01`, `webdev-task-02`, ...
  - 子任务：`webdev-task-01.01`, `webdev-task-01.02`, ...（基于父任务的层级序号）
- 任务目录按家族分组：
  - `tasks/webdev-task-01/webdev-task-01/`
  - `tasks/webdev-task-01/webdev-task-01.01/`
  - `tasks/webdev-task-02/webdev-task-02/`
- 源码目录同样按家族分组：
  - `sources/webdev-task-01/webdev-task-01/`
  - `sources/webdev-task-01/webdev-task-01.01/`
- 创建子任务时使用 `--parent <parent-task-id>`，例如 `--parent webdev-task-01`
- 会话目录：`session-<type>-YYYY-MM-NNN[-<agent>]`
- 截图命名：`sota_final_desktop.png`、`sota_final_mobile.png`、`state_empty.png`

---

## 4. 必填文件清单

```text
projects/webdev-long-horizon/tasks/webdev-task-01/webdev-task-01.01/
  ✓ task.md
  ✓ metadata.json
  ✓ README.md
  ✓ rubric.json
  ✓ PROMPT.md              # 用于 SOTA / 远程 codex 运行
```

源码管理方式二选一：

```text
  ✓ starter/           # 内置 starter（传统）
  # 或
  ✓ ../../sources/webdev-task-01/webdev-task-01.01/   # 外部 source（推荐，目录名与任务 ID 一致）
```

以下目录/文件根据任务需要补充：

```text
  assets/              # 参考截图与素材
  mock-data/           # mock 数据
  tests/               # Playwright / 单元测试
  target_states.md     # 关键状态说明
  sota-run.md          # SOTA 运行记录
  screenshots/         # 最终截图
```

---

## 5. 常见错误

- 需求只有一句话，缺少工程上下文。
- 缺少移动端参考截图。
- Rubric 只有功能检查，缺少视觉、交互、边界。
- 源码项目无法 `npm install` 后直接运行。
- mock-data 不完整，agent 需要臆造数据。
- 任务泄露答案（如 starter 中已实现核心功能）。
- 忘记生成 `PROMPT.md`，导致远程 codex 运行时缺少明确交付要求。
