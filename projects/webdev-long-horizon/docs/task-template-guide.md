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

生成目录：`projects/webdev-long-horizon/tasks/webdev-task-sxw-01/webdev-task-sxw-01/`

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
  --parent webdev-task-sxw-01
```

生成目录：`projects/webdev-long-horizon/tasks/webdev-task-sxw-01/webdev-task-sxw-01.01/`

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
  "task_id": "webdev-task-sxw-01",
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

### 2.8 `task.md` 作为 SOTA 提示词

不再单独维护 `PROMPT.md`。`task.md` 直接作为 SOTA 提示词：

- `upload_to_remote.py` 上传时会将 `task.md` 重命名为远程 `PROMPT.md`。
- `run_sota.py` 本地运行时会基于 `task.md` 生成 session 产物中的 `PROMPT.md`。

因此 `task.md` 中必须明确：

1. 源码位置（如 `./source` 或当前目录）。
2. 启动命令（如 `npm install && npm run dev`）。
3. 交付要求（截图、测试、不修改原始任务文件等）。

---

## 3. 目录命名规范

- 项目 ID：`webdev-long-horizon`
- 任务 ID：
  - 顶层任务：`webdev-task-sxw-01`, `webdev-task-02`, ...
  - 子任务：`webdev-task-sxw-01.01`, `webdev-task-sxw-01.02`, ...（基于父任务的层级序号）
- 任务目录按家族分组：
  - `tasks/webdev-task-sxw-01/webdev-task-sxw-01/`
  - `tasks/webdev-task-sxw-01/webdev-task-sxw-01.01/`
  - `tasks/webdev-task-02/webdev-task-02/`
- 源码目录同样按家族分组：
  - `sources/webdev-task-sxw-01/webdev-task-sxw-01/`
  - `sources/webdev-task-sxw-01/webdev-task-sxw-01.01/`
- 创建子任务时使用 `--parent <parent-task-id>`，例如 `--parent webdev-task-sxw-01`
- 会话目录：`session-<type>-YYYY-MM-NNN[-<agent>]`
- 截图命名：`sota_final_desktop.png`、`sota_final_mobile.png`、`state_empty.png`

---

## 4. 必填文件清单

```text
projects/webdev-long-horizon/tasks/webdev-task-sxw-01/webdev-task-sxw-01.01/
  ✓ task.md                # 任务需求，直接作为 SOTA 提示词
  ✓ metadata.json
  ✓ README.md
  ✓ rubric.json
```

源码管理方式二选一：

```text
  ✓ starter/           # 内置 starter（传统）
  # 或
  ✓ ../../sources/webdev-task-sxw-01/webdev-task-sxw-01.01/   # 外部 source（推荐，目录名与任务 ID 一致）
```

以下目录/文件根据任务需要补充：

```text
  assets/              # 任务素材（参考截图放 assets/reference/，其他按类型分子目录）
  mock-data/           # mock 数据
  tests/               # Playwright / 单元测试
  target_states.md     # 关键状态说明
  sota-run.md          # SOTA 运行记录
  screenshots/         # 人工验证后放置的关键状态截图（可选）
```

---

## 5. 常见错误

- 需求只有一句话，缺少工程上下文。
- 缺少移动端参考截图。
- Rubric 只有功能检查，缺少视觉、交互、边界。
- 源码项目无法 `npm install` 后直接运行。
- mock-data 不完整，agent 需要臆造数据。
- 任务泄露答案（如 starter 中已实现核心功能）。
- `task.md` 没有明确源码位置、启动命令和交付要求。
