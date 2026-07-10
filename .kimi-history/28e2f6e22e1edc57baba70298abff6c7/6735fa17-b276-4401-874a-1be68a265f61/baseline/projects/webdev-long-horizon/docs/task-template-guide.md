# 任务模板使用指南

本指南说明如何使用 `templates/task/` 和 `templates/starter/` 在指定项目下创建符合规范的新任务。

---

## 1. 快速创建

使用脚本自动生成骨架：

```bash
python scripts/create_task.py \
  --project webdev-long-horizon \
  --title "复杂 O2O 服务聚合平台" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --arena-tags "ui,map,e-commerce,visualize"
```

---

## 2. 模板文件说明

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
  "task_id": "webdev-task-0001",
  "title": "复杂 O2O 服务聚合平台",
  "category_tags": ["电商 / 交易应用：O2O 服务 / 聚合平台"],
  "arena_tags": ["ui", "map", "e-commerce", "visualize"],
  "prompt_type": "前端",
  "required_tools": ["browser", "playwright", "screenshot"],
  "difficulty": "high",
  "annotator": "",
  "status": "draft",
  "version": "0.1.0"
}
```

### 2.3 `templates/task/README.md`

说明启动方式、测试方式、目录结构、已知限制。

### 2.4 `templates/task/rubric.json`

验收标准，10-20 个叶节点。

### 2.5 `templates/task/target_states.md`

列出必须验收的关键状态。

### 2.6 `templates/starter/`

初始项目模板，基于 Vite + React + TypeScript + Tailwind CSS。

项目可以在 `projects/<project-id>/templates/starter/` 中覆盖全局 starter。

---

## 3. 目录命名规范

- 项目 ID：英文小写 + 短横线，如 `webdev-long-horizon`
- 任务 ID：`webdev-task-XXXX`，四位数字，在项目内递增
- 会话目录：`session-<type>-YYYY-MM-NNN[-<agent>]`
- 截图命名：`sota_final_desktop.png`、`sota_final_mobile.png`、`state_empty.png`

---

## 4. 必填文件清单

```text
projects/<project-id>/tasks/webdev-task-XXXX/
  ✓ task.md
  ✓ metadata.json
  ✓ README.md
  ✓ starter/
  ✓ assets/
  ✓ mock-data/
  ✓ tests/
  ✓ rubric.json
  ✓ target_states.md
  ✓ sota-run.md
  ✓ screenshots/
```

---

## 5. 常见错误

- 需求只有一句话，缺少工程上下文。
- 缺少移动端参考截图。
- Rubric 只有功能检查，缺少视觉、交互、边界。
- starter 项目无法 `npm install` 后直接运行。
- mock-data 不完整，agent 需要臆造数据。
- 任务泄露答案（如 starter 中已实现核心功能）。
