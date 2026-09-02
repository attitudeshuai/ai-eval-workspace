# swe-like 目录结构样例

> 以 **session=session-0001**、**repo=restic**、分支 **restic-01/02/03** 为例。

---

## 总览

```
sessions/swe-like/session-0001/
├── repos/                        # 源码（fork clone，与 tasks 平级）
│   └── restic/                   # {repo}
│       ├── origin/               # 主分支基线（fork 的 master/main，不动）
│       ├── restic-01/           # 分支 restic-01（worktree）
│       ├── restic-02/           # 分支 restic-02（worktree）
│       └── restic-03/           # 分支 restic-03（worktree）
└── tasks/                        # 题目（结构镜像 repos，一个分支一道题）
    └── restic/                   # {repo}
        ├── restic-01/           # {branch}，对应上面同名分支
        │   ├── task.md           # 需求 Prompt（原文）
        │   ├── meta.json         # Repo URL / Commit/版本 / 主要语言 / 任务类型 / Seed 模型/版本
        │   ├── verify-rubric.md  # Verify Rubric（验收前固定）
        │   ├── session.md        # Trae 完整会话（出题阶段创建空文件，02 阶段粘贴，供步数统计）
        │   ├── run-log.md        # Trae Session ID / 有效轮数（= 模型输出步数）
        │   ├── result.md         # 产物结果 / 产物补充材料
        │   └── review.md         # 是否完成 / 是否通过质检 / 收录判定
        ├── restic-02/
        └── restic-03/
```

---

## 路径映射

| 变量 | 含义 | 示例 |
|------|------|------|
| `{work_root}` | 工作根 | `sessions/swe-like` |
| `{session}` | 会话（批次） | `session-0001` |
| `{repo}` | 仓库名 | `restic` |
| `{branch}` | 分支名（= task-id） | `restic-01` |

| 用途 | 公式 | 示例 |
|------|------|------|
| 源码基线 | `{work_root}/{session}/repos/{repo}/origin/` | `.../repos/restic/origin/` |
| 分支工作目录 | `{work_root}/{session}/repos/{repo}/{branch}/` | `.../repos/restic/restic-01/` |
| 任务目录 | `{work_root}/{session}/tasks/{repo}/{branch}/` | `.../tasks/restic/restic-01/` |
| 需求 Prompt | 同上 `task.md` | `.../restic-01/task.md` |
| 元数据 | 同上 `meta.json` | `.../restic-01/meta.json` |
| Verify Rubric | 同上 `verify-rubric.md` | `.../restic-01/verify-rubric.md` |
| 运行记录 | 同上 `run-log.md` / `result.md` | `.../restic-01/run-log.md` |
| 验收记录 | 同上 `review.md` | `.../restic-01/review.md` |

---

## 多批次示例

```
sessions/swe-like/
├── session-0001/             # 第 1 批（repo: restic）
│   ├── repos/restic/
│   │   ├── origin/
│   │   ├── restic-01/
│   │   ├── restic-02/
│   │   └── restic-03/
│   └── tasks/restic/
│       ├── restic-01/
│       ├── restic-02/
│       └── restic-03/
│
└── session-0002/             # 第 2 批（repo: pydantic）
    ├── repos/pydantic/
    │   ├── origin/
    │   ├── restic-01/
    │   ├── restic-02/
    │   └── restic-03/
    └── tasks/pydantic/
        ├── restic-01/
        ├── restic-02/
        └── restic-03/
```
