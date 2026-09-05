# swe-like 运行数据

本目录存放 swe-like 任务的运行数据，按 session 组织。交付形态为伪 Harbor 包（见 `projects/swe-like/docs/SWE-like Repo-v3.md`）。

```
sessions/swe-like/
└── {SESSION_NAME}/
    ├── repos/                    # fork 源码与各题 worktree（见 repos/README.md）
    └── tasks/
        └── {repo}/
            ├── prompt-candidates.md  # 该 repo 候选提示词池（10 个，预检通过后选用）
            └── {repo}-{NN}/      # 题目名 = 分支名 = 目录名
                ├── task.toml           # 16 键底稿字段
                ├── instruction.md      # 需求 Prompt（原文）
                ├── environment/
                │   └── Dockerfile      # 基线 mars-base + ARG BASE_SHA
                ├── tests/
                │   └── nl_rubric.yaml  # Verify Rubric（验收前固定，唯一准则）
                ├── solution/           # 本批允许留空
                └── evidence/           # 第 2 步运行取证
                    ├── trajectory.jsonl  # TraeX 轨迹（Trae IDE 交 trajectory.md；miniswe 交 trajectory.json）
                    ├── model.patch       # diff 基准 = base_commit
                    └── screenshots/      # 验证截图（非空）
```

## 说明

- `{SESSION_NAME}` 由 `projects/swe-like/config.toml` 的 `[sessions].active` 决定（默认 `session-0001`）
- 本目录为工作数据，默认 gitignore，勿提交
- 历史旧格式（task.md / meta.json / verify-rubric.md / session.md）已废弃；如有留存归档在 `tasks/<repo>/_archive-v2/`，仅供查阅，以 harbor 文件为唯一准则
- 导出交付包时 zip 只组装规范内文件（见 `projects/swe-like/docs/runbook.md` 第 4 步）
