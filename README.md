# AI 评估工作台

一个可持续、可扩展、可复现的 **多项目 AI 能力评估工作台**。支持在同一个仓库中集成任意数量的评估项目，每个项目完全自治，拥有自己的目录结构、模板、评估方式与产物格式。工作台只提供共享的基础设施：技能、脚本、会话隔离与基准汇总。

---

## 核心设计：项目自治

**本工作台不对项目内部结构做任何强制要求。**

- 每个项目是 `projects/<project-id>/` 下的一个独立目录。
- 项目可以有自己的任务格式、模板、Rubric、测试方式、文档。
- 工作台通过 `projects/<project-id>/config.toml` 读取项目基本元数据，其余内容由项目自行决定。
- `projects/webdev-long-horizon/` 是一个示例项目，展示了 Web Dev 长程任务的组织方式，但不代表所有项目必须遵循。

---

## 目录结构

```text
.
├── README.md                 # 本文件
├── AGENTS.md                 # 给 AI Agent 的工作台使用说明
├── .gitignore
├── config/                   # 工作台级通用配置（不绑定任何项目）
│   └── workspace.toml
├── .kimi/skills/             # 全局技能：项目接入、任务评估、SOTA 运行等
├── .claude/agents/           # Claude Agent 定义
├── docs/                     # 工作台级文档：流程、规范、接入指南
├── templates/                # 新项目 onboarding 模板（可选）
│   └── project/
├── scripts/                  # 通用自动化脚本
│   ├── create_project.py     # onboard 新项目（最小化）
│   ├── create_task.py        # 在项目中创建新任务（依赖项目模板）
│   ├── validate_project.py   # 校验项目配置与任务结构
│   ├── validate_task.py      # 校验单个任务结构
│   ├── run_sota.py           # 为指定任务运行 SOTA
│   ├── evaluate_task.py      # 基于 Rubric 生成评估报告
│   └── generate_report.py    # 基准汇总
├── projects/                 # 所有评估项目（完全自治）
│   └── webdev-long-horizon/  # 示例项目
│       ├── config.toml
│       ├── README.md
│       ├── docs/             # 项目专属文档
│       ├── templates/        # 项目专属模板
│       ├── rubrics/          # 项目专属 rubric
│       └── tasks/            # 项目专属任务
├── sessions/                 # 跨项目评估会话产物
└── benchmarks/               # 汇总基准
    ├── global/
    └── by-project/
```

---

## 快速开始

### 1. 初始化

```bash
pip install -r scripts/requirements.txt
```

### 2. onboard 新项目

```bash
python scripts/create_project.py \
  --id my-project \
  --name "我的评估项目" \
  --description "评估 agent 在某某场景下的能力"
```

这会创建最小化的项目骨架：

```text
projects/my-project/
  config.toml
  README.md
```

之后你可以自由组织项目内部结构，不需要遵循任何模板。

### 3. 在项目中运行 SOTA

只要项目 `config.toml` 存在，就可以创建会话：

```bash
python scripts/run_sota.py \
  --session session-sota-2026-07-001-codex \
  --project my-project \
  --task <task-id> \
  --agent codex
```

产物会按项目隔离保存到：

```text
sessions/session-sota-2026-07-001-codex/
  projects/my-project/
    submissions/
    reports/
```

### 4. 汇总基准

```bash
python scripts/generate_report.py --session session-sota-2026-07-001-codex
```

---

## 工作台原则

1. **项目自治**：工作台不强制任务格式、模板、Rubric 或目录结构。
2. **最小干预**：只要求每个项目有 `config.toml`，其余自由定义。
3. **会话隔离**：每次评估会话独立，跨项目产物按项目隔离。
4. **可扩展**：新项目的加入不改变现有项目。
5. **示例而非标准**：`webdev-long-horizon` 是示例项目，不是强制模板。

---

## 相关文档

- [AGENTS.md](./AGENTS.md) — 给 AI Agent 的使用说明
- [docs/project-onboarding.md](./docs/project-onboarding.md) — 新项目接入指南
- [docs/workflow.md](./docs/workflow.md) — 评估流程参考
- [projects/webdev-long-horizon/docs/task-template-guide.md](./projects/webdev-long-horizon/docs/task-template-guide.md) — Web Dev 项目专属任务模板指南
