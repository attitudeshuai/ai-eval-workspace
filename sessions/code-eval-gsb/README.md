# code-eval-gsb 会话数据

多模型代码对比评估的工作数据存放目录。按 session 隔离。

## 目录结构

```
sessions/code-eval-gsb/
└── {session-name}/               # 如 session-gsb1v1
    ├── gitlab source/            # GitLab clone + GitHub 分支（gitignore）
    │   └── label-01035/
    │       ├── label-01035-origin/
    │       ├── label-01035-TestM_1/
    │       └── label-01035-TestM_2/
    └── ai-model-result/          # 提示词 + 评价（gitignore）
        └── label-01035/
            └── label-01035-Bug修复/
                ├── A-label-01035-Bug修复-TestM_1-对话内容.md
                ├── A-label-01035-Bug修复-TestM_1-评价结果.md
                ├── A-label-01035-Bug修复-TestM_2-对话内容.md
                ├── A-label-01035-Bug修复-TestM_2-评价结果.md
                └── A-label-01035-Bug修复-评价汇总.md
```

> `gitlab source/` 和 `ai-model-result/` 默认被 `.gitignore` 排除。
