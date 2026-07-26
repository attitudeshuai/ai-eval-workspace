# code-eval-gsb 目录结构样例

> 以 **session=session-gsb1v1**、**项目 demo-hello**、**类型 bugfix** 为例。

---

## 总览

```
ai-eval-workspace/
│
├── projects/code-eval-gsb/                # 项目配置 + skills
│   ├── config.toml
│   ├── SKILL.md
│   ├── skills/
│   │   ├── 01-prompt-generate.md
│   │   ├── 02-round-review.md
│   │   └── 03-summary-analysis.md
│   ├── docs/
│   └── templates/
│
└── sessions/code-eval-gsb/
    └── session-gsb1v1/                    # {SESSION_NAME}
        │
        ├── source code/                   # 源码 + 模型分支
        │   └── demo-hello/
        │       ├── demo-hello-origin/     #   origin 仓（含 bug）
        │       ├── demo-hello-TestM_1/    #   模型1 分支
        │       └── demo-hello-TestM_2/    #   模型2 分支
        │
        └── ai-model-result/              # 提示词 + 评价
            └── demo-hello/
                └── demo-hello-bugfix/
                    ├── demo-hello-bugfix-TestM_1-对话内容.md
                    ├── demo-hello-bugfix-TestM_1-评价结果.md
                    ├── demo-hello-bugfix-TestM_2-对话内容.md
                    ├── demo-hello-bugfix-TestM_2-评价结果.md
                    └── demo-hello-bugfix-评价汇总.md
```

---

## 路径映射

| 变量 | config.toml | 展开 |
|------|------------|------|
| `{work_root}` | `sessions/code-eval-gsb` | `sessions/code-eval-gsb` |
| `{session}` | `[sessions].active` | `session-gsb1v1` |

| 用途 | 公式 | 示例 |
|------|------|------|
| origin 仓 | `{work_root}/{session}/source code/{项目名}/{项目名}-origin/` | `sessions/code-eval-gsb/session-gsb1v1/source code/demo-hello/demo-hello-origin/` |
| 模型分支 | `{work_root}/{session}/source code/{项目名}/{项目名}-{模型名}/` | `.../demo-hello-TestM_1/` |
| 对话内容 | `{work_root}/{session}/ai-model-result/{项目名}/{项目名}-{ALIAS}/{项目名}-{ALIAS}-{模型名}-对话内容.md` | `.../ai-model-result/demo-hello/demo-hello-bugfix/demo-hello-bugfix-TestM_1-对话内容.md` |
| 评价汇总 | 同上 `...-评价汇总.md` | `.../demo-hello-bugfix-评价汇总.md` |

---

## 多批次示例

```
sessions/code-eval-gsb/
├── session-gsb1v1/           # 第1批：1v1 对比
│   ├── source code/demo-hello/
│   ├── source code/another-project/
│   └── ai-model-result/...
│
├── session-gcs/              # 第2批：另一批对比
│   ├── source code/some-project/
│   └── ai-model-result/...
│
└── session-gsb0608/          # 第3批
    └── ...
```
