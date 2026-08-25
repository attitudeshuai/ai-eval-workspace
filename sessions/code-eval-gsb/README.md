# code-eval-gsb 会话数据

多模型代码对比评估的工作数据存放目录。按 session 隔离。

## 目录结构

```
sessions/code-eval-gsb/
└── {session-name}/               # 如 session-0825
    ├── source code/              # 源码 + 模型分支（gitignore）
    │   └── demo-hello/
    │       ├── demo-hello-origin/
    │       ├── demo-hello-odysseus/
    │       ├── demo-hello-athena/
    │       ├── demo-hello-poseidon/
    │       └── demo-hello-cyclops/
    └── ai-model-result/          # 提示词 + 评价（gitignore）
        └── demo-hello/
            └── demo-hello-bugfix/
                ├── demo-hello-bugfix-odysseus-对话内容.md
                ├── demo-hello-bugfix-odysseus-评价结果.md
                ├── ...（athena / poseidon / cyclops 同构）
                └── demo-hello-bugfix-评价汇总.md
```

## 当前 session

| session | 期次 | anchor |
|---------|------|--------|
| `session-0825` | 0825 期 | Odysseus |
| `session-0731` | 0731 期（上一期） | Steve |
| `session-gsb1v1` | demo 示例 | — |

> `source code/` 和 `ai-model-result/` 默认被 `.gitignore` 排除，不提交到 Git。
