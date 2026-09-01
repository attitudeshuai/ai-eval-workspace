# swe-like 运行数据

本目录存放 swe-like 任务的运行数据，按 session 组织。

```
sessions/swe-like/
└── {SESSION_NAME}/
    └── tasks/
        └── {task-id}/
            ├── task.md           # 需求 Prompt（原文）
            ├── meta.json         # Repo URL / Commit/版本 / 主要语言 / 任务类型 / Seed 模型/版本
            ├── verify-rubric.md  # Verify Rubric（验收前固定）
            ├── run-log.md        # Trae Session ID / 有效轮数
            ├── result.md         # 产物结果 / 产物补充材料
            └── review.md         # 是否完成 / Reviewer / 是否通过质检 / 收录判定
```

## 说明

- `{SESSION_NAME}` 由 `projects/swe-like/secrets.toml` 的 `active_session` 决定（默认 `session-0001`）
- 本目录为工作数据，默认 gitignore，勿提交
- 产物补充材料（`model.patch`、verifier 日志、失败测试列表等）可放任务目录下 `artifacts/` 子目录，并在 `result.md` 中记录路径
