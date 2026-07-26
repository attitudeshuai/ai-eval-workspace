# 高难度 Web Dev 长程任务

评估 AI agent 在复杂 Web 前端开发场景下的真实工程能力。

## 项目结构

```
projects/webdev-long-horizon/
├── config.toml                 # 项目配置（task_prefix、评估参数、质量闸门）
├── categories.json             # 任务分类树与 Arena 标签
├── README.md                   # 本文件
├── OPERATIONAL_WORKFLOW.md     # 完整实操流程（创建→SOTA→评估→交付）
├── secrets.toml                # 远程机器 / API 密钥（gitignore）
│
├── docs/                       # 项目文档
│   ├── annotation-guidelines.md
│   ├── runbook.md
│   ├── task-template-guide.md
│   └── 高难度 Web Dev 长程任务数据采购需求 Draft.md
│
├── templates/                  # 项目模板
│   ├── starter/                # Vite + React + Tailwind + Playwright 脚手架
│   └── task/                   # 任务文件骨架（task.md / rubric.json / metadata.json 等）
│
├── sources/                    # 参考答案 / 源码仓库（按家族分组）
│   └── webdev-task-sxw-01/
│       ├── webdev-task-sxw-01/         # 顶层任务源码
│       └── webdev-task-sxw-01.01/      # 增量任务源码（继承自父任务）
│
├── tasks/                      # 任务仓库（按家族分组）
│   ├── webdev-task-sxw-01/
│   │   ├── webdev-task-sxw-01/         # 顶层任务
│   │   └── webdev-task-sxw-01.01/      # 增量任务
│   ├── webdev-task-sxw-02/
│   │   └── webdev-task-sxw-02/
│   ├── webdev-task-sxw-03/
│   │   └── webdev-task-sxw-03/
│   └── webdev-task-sxw-simple/         # 简化示例任务
│       └── webdev-task-sxw-simple/
│
└── rubrics/                    # 共享 Rubric 模板
```

> **约定**：每个任务目录下均含 `task.md`、`rubric.json`、`metadata.json`、`target_states.md`、`assets/`、`mock-data/`、`tests/` 等标准文件。

## 创建任务

### 模式一：增量开发（基于父任务）

```bash
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "为电商后台增加订单筛选与导出" \
  --category "电商 / 交易应用：O2O 服务 / 聚合平台" \
  --difficulty high \
  --arena-tags "ui,e-commerce,visualize" \
  --prompt-type "前端" \
  --skip-starter \
  --parent webdev-task-sxw-01
```

生成目录：`tasks/webdev-task-sxw-01/webdev-task-sxw-01.01/`，自动继承父任务源码与 mock-data。

### 模式二：从零开发

```bash
python scripts/webdev-long-horizon/create_task.py \
  --project webdev-long-horizon \
  --title "支持拖拽看板的任务管理系统" \
  --category "交互型应用：可视化 / 数据看板" \
  --difficulty high \
  --arena-tags "ui,visualize,drag-drop" \
  --prompt-type "前端" \
  --skip-starter
```

生成目录：`tasks/webdev-task-sxw-04/webdev-task-sxw-04/`（自动编号）。

> 详细流程见 [OPERATIONAL_WORKFLOW.md](./OPERATIONAL_WORKFLOW.md)。

## 运行 SOTA & 评估

```bash
# 运行 SOTA
python scripts/webdev-long-horizon/run_sota.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task <task-id> \
  --agent codex

# 评估
python scripts/webdev-long-horizon/evaluate_task.py \
  --session <session-name> \
  --project webdev-long-horizon \
  --task <task-id> \
  --agent codex

# 打包交付
python scripts/webdev-long-horizon/package_deliverable.py \
  --task <task-id> \
  --session <session-name> \
  --agent codex
```

## 校验

```bash
python scripts/webdev-long-horizon/validate_task.py --allow-no-starter <task-id>
```

## 质量闸门

| 闸门 | 说明 |
|---|---|
| 可运行性 | 源码可本地 `npm install && npm run dev` 启动 |
| 完整性 | task.md / rubric.json / target_states.md / mock-data / tests 齐全 |
| 视觉可验收性 | 提供参考截图，screenshot 对比可判断通过/失败 |
| Rubric 有效性 | 6 维度 10-20 叶节点，每项有明确的 grader_spec |
| 可解性 | SOTA agent 至少跑通一次 |
| 无污染风险 | 不含敏感信息、不依赖不可达外部服务 |

## 任务准入标准

- 非局部工程改动（跨模块、跨页面）
- 至少 3 类相互影响的约束
- 视觉输入不可省略
- 浏览器工具是必要路径
- 至少 4 类关键状态
- SOTA 可解但不轻松
