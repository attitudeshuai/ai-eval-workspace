# swe-like 目录结构样例

> 以 **session=session-0001**、**任务 swe-fastapi-001** 为例。

---

## 总览

```
ai-eval-workspace/
│
├── projects/swe-like/                # 项目配置 + skills
│   ├── config.toml
│   ├── SKILL.md
│   ├── skills/
│   │   ├── 01-task-create.md
│   │   ├── 02-run-record.md
│   │   ├── 03-verify-review.md
│   │   └── 04-export-delivery.md
│   ├── docs/
│   │   ├── SWE-like Repo-v1.md       # 出题规范（试行）
│   │   ├── runbook.md
│   │   └── structure-example.md
│   ├── templates/
│   │   ├── task-form.md
│   │   └── delivery-form.md
│   └── scripts/
│       └── append_delivery_feishu.py
│
└── sessions/swe-like/
    └── session-0001/                 # {SESSION_NAME}
        └── tasks/
            └── swe-fastapi-001/      # {task-id}
                ├── task.md           # 需求 Prompt（原文）
                ├── meta.json         # Repo URL / Commit/版本 / 主要语言 / 任务类型 / Seed 模型/版本
                ├── verify-rubric.md  # Verify Rubric（验收前固定）
                ├── run-log.md        # Trae Session ID / 有效轮数
                ├── result.md         # 产物结果 / 产物补充材料
                └── review.md         # 是否完成 / Reviewer / 是否通过质检 / 收录判定
```

---

## 路径映射

| 变量 | config.toml | 展开 |
|------|------------|------|
| `{work_root}` | `sessions/swe-like` | `sessions/swe-like` |
| `{session}` | `[sessions].active` | `session-0001` |
| `{task-id}` | 出题时定义 | `swe-fastapi-001` |

| 用途 | 公式 | 示例 |
|------|------|------|
| 任务目录 | `{work_root}/{session}/tasks/{task-id}/` | `sessions/swe-like/session-0001/tasks/swe-fastapi-001/` |
| 需求 Prompt | 同上 `task.md` | `.../swe-fastapi-001/task.md` |
| 元数据 | 同上 `meta.json` | `.../swe-fastapi-001/meta.json` |
| Verify Rubric | 同上 `verify-rubric.md` | `.../swe-fastapi-001/verify-rubric.md` |
| 运行记录 | 同上 `run-log.md` / `result.md` | `.../swe-fastapi-001/run-log.md` |
| 验收记录 | 同上 `review.md` | `.../swe-fastapi-001/review.md` |

---

## 多批次示例

```
sessions/swe-like/
├── session-0001/             # 第 1 批
│   └── tasks/
│       ├── swe-fastapi-001/
│       ├── swe-codex-002/
│       └── swe-fastapi-003/  # 同 repo 第 2 题（注意单 repo 题量上限 2%）
│
└── session-0002/             # 第 2 批
    └── tasks/
        └── swe-pydantic-004/
```
