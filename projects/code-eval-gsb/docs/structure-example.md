# code-eval-gsb 目录结构样例

> 以 **session=session-0825**、**项目 demo-hello**、**类型 bugfix** 为例。

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
│   │   ├── 03-summary-analysis.md
│   │   └── 04-export-delivery.md
│   ├── docs/
│   └── templates/
│
└── sessions/code-eval-gsb/
    └── session-0825/                      # {SESSION_NAME}
        │
        ├── source code/                   # 源码 + 模型分支
        │   └── demo-hello/
        │       ├── demo-hello-origin/     # origin 仓（含 bug）
        │       ├── demo-hello-odysseus/   # 模型分支（anchor）
        │       ├── demo-hello-athena/
        │       ├── demo-hello-poseidon/
        │       └── demo-hello-cyclops/
        │
        └── ai-model-result/              # 提示词 + 评价
            └── demo-hello/
                └── demo-hello-bugfix/
                    ├── demo-hello-bugfix-odysseus-对话内容.md
                    ├── demo-hello-bugfix-odysseus-评价结果.md
                    ├── demo-hello-bugfix-athena-对话内容.md
                    ├── demo-hello-bugfix-athena-评价结果.md
                    ├── ...（poseidon / cyclops 同构）
                    └── demo-hello-bugfix-评价汇总.md
```

---

## 路径映射

| 变量 | config.toml | 展开 |
|------|------------|------|
| `{work_root}` | `sessions/code-eval-gsb` | `sessions/code-eval-gsb` |
| `{session}` | `[sessions].active` | `session-0825` |

| 用途 | 公式 | 示例 |
|------|------|------|
| origin 仓 | `{work_root}/{session}/source code/{项目名}/{项目名}-origin/` | `sessions/code-eval-gsb/session-0825/source code/demo-hello/demo-hello-origin/` |
| 模型分支 | `{work_root}/{session}/source code/{项目名}/{项目名}-{模型slug}/` | `.../demo-hello-odysseus/` |
| 对话内容 | `{work_root}/{session}/ai-model-result/{项目名}/{项目名}-{ALIAS}/{项目名}-{ALIAS}-{模型slug}-对话内容.md` | `.../ai-model-result/demo-hello/demo-hello-bugfix/demo-hello-bugfix-odysseus-对话内容.md` |
| 评价汇总 | 同上 `...-评价汇总.md` | `.../demo-hello-bugfix-评价汇总.md` |

---

## 多批次示例

```
sessions/code-eval-gsb/
├── session-0825/             # 0825 期（Odysseus anchor）
│   ├── source code/demo-hello/
│   ├── source code/another-project/
│   └── ai-model-result/...
│
├── session-0731/             # 上一期：0731 期（Steve anchor）
│   ├── source code/some-project/
│   └── ai-model-result/...
│
└── session-gsb1v1/           # demo 示例
    └── ...
```

---

## 0-1 代码生成示例

> 以 **session=session-0825**、**项目 gsb0825_00001**、**类型 0-1代码生成（ALIAS=codegen）** 为例。

0-1 任务的 origin 仓只含一个标准命名的 `README.md`（完整需求规格书），**项目名 = 需求 md 文件名**：

```
sessions/code-eval-gsb/session-0825/
│
├── source code/gsb0825_00001/
│   ├── gsb0825_00001-origin/      # 仅 README.md（需求规格书，无代码）
│   ├── gsb0825_00001-odysseus/
│   ├── gsb0825_00001-athena/
│   ├── gsb0825_00001-poseidon/
│   └── gsb0825_00001-cyclops/
│
└── ai-model-result/gsb0825_00001/gsb0825_00001-codegen/
    ├── gsb0825_00001-codegen-odysseus-对话内容.md
    ├── gsb0825_00001-codegen-odysseus-评价结果.md
    ├── gsb0825_00001-codegen-athena-对话内容.md
    ├── gsb0825_00001-codegen-athena-评价结果.md
    ├── ...（poseidon / cyclops 同构）
    └── gsb0825_00001-codegen-评价汇总.md
```

建仓流程：

1. 把 `projects/code-eval-gsb/docs/gsb0825_00001.md` 原样复制为 `source code/gsb0825_00001/gsb0825_00001-origin/README.md`
2. `git init` + 首次 commit → 创建 GitHub public 仓 → push main
3. 从 main 建各模型分支（odysseus / athena / poseidon / cyclops）→ 分别 clone 回本地

首轮提示词固定口径：项目主题一句话 + "需求都写在仓库的 README 里，通读后按文档把整套系统开发出来"；第 2 轮起按模型交付与 README 的差距追问（总轮次 ≤ 3）。
