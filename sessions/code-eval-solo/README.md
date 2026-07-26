# code-eval-solo 会话数据

单模型代码评估的工作数据存放目录。按 session 隔离，每个 session 下有源码和提示词/评价两棵树。

## 目录结构

```
sessions/code-eval-solo/
└── {session-name}/               # 如 solo-0601
    ├── source code/              # 项目源码（git 仓库，gitignore）
    │   ├── app-12/
    │   ├── app-15/
    │   └── demo-hello/
    └── ai-model-result/          # 提示词 + 评价（gitignore）
        └── self-projects/
            ├── app-12/
            │   ├── app-12-Bug修复/
            │   │   ├── app-12-Bug修复-01.md
            │   │   └── app-12-Bug修复-01-评价结果.md
            │   └── ...
            └── demo-hello/
                ├── demo-hello-Bug修复/
                └── demo-hello-Feature迭代/
```

> `source code/` 和 `ai-model-result/` 默认被 `.gitignore` 排除（数据量大）。demo 类项目如需提交，可用 `git add -f`。
