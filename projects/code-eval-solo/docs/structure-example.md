# code-eval-solo 目录结构样例

> 以 **session=solo-0601**、**PROJECT_PREFIX=app**、**项目 app-12** 为例，展示执行全流程后的完整目录结构。

---

## 总览

```
ai-eval-workspace/                          # 工作台（控制中心）
│
├── projects/code-eval-solo/                # 项目配置 + skills
│   ├── config.toml                         #   路径、规则、配额
│   ├── secrets.toml                        #   本地密钥（不提交）
│   ├── SKILL.md                            #   技能索引导航
│   ├── skills/
│   │   ├── 01-prompt-generate.md
│   │   ├── 02-result-analysis.md
│   │   ├── 03-export-results.md
│   │   └── 04-export-prompt.md
│   ├── docs/
│   │   ├── runbook.md                      #   操作手册
│   │   └── workflow.md
│   └── templates/
│
├── skills/                                 # 共享 Agent（workspace 级）
│   ├── implementation-reviewer/SKILL.md
│   ├── humanizer-zh/SKILL.md
│   ├── prompt-architect/SKILL.md
│   └── excel-diff/
│       ├── SKILL.md
│       └── compare_excel.py
│
├── deliverables/code-eval-solo/            # 导出产物
│   └── solo-0601/
│       └── app-12/
│           ├── csv-app-12-export.csv
│           └── csv-app-12-prompt-export.csv
│
└── sessions/code-eval-solo/                # 工作数据 + 评估会话
    └── solo-0601/                          # {SESSION_NAME}
        │
        ├── source code/                    # {repo_base_path} 项目源码
        │   └── app-12/                     #   git 仓库
        │       ├── .git/
        │       ├── src/
        │       └── README.md
        │
        └── ai-model-result/               # 提示词 & 评价
            └── app-12/
                ├── app-12-bugfix/
                    │   ├── app-12-bugfix-01.md
                    │   ├── app-12-bugfix-01-评价结果.md
                    │   └── ...
                    ├── app-12-codegen/
                    └── ...
---

## 路径映射（config.toml → 实际路径）

| 变量 | config.toml 值 | 展开后（相对于 workspace） |
|------|---------------|--------------------------|
| `{work_root}` | `sessions/code-eval-solo` | `sessions/code-eval-solo` |
| `{SESSION_NAME}` | `[sessions].active` | `solo-0601` |
| `{PROJECT_PREFIX}` | `[source_rules].local_prefixes[0]` | `app` |
| `{REPO_BASE_PATH}` | `[paths].repo_base_path` | `sessions/code-eval-solo/solo-0601/source code` |

| 用途 | 公式 | 实际路径 |
|------|------|---------|
| 主仓源码 | `{REPO_BASE_PATH}/{PROJECT_PREFIX}-<id>/` | `sessions/code-eval-solo/solo-0601/source code/app-12/` |
| 提示词文件 | `{work_root}/{SESSION_NAME}/ai-model-result/{PROJECT_PREFIX}-<id>/{TYPE_ALIAS}/{PROJECT_PREFIX}-<id>-{TYPE_ALIAS}-{index}.md` | `sessions/code-eval-solo/solo-demo/ai-model-result/app-12/app-12-bugfix/app-12-bugfix-01.md` |
| 导出 CSV | `deliverables/code-eval-solo/{SESSION_NAME}/{PROJECT_PREFIX}-<id>/csv-{PROJECT_PREFIX}-<id>-export.csv` | `deliverables/code-eval-solo/solo-0601/app-12/csv-app-12-export.csv` |

---

## 一次完整执行后的文件变化

### Step 1: generate 后

```
新增:
  ai-model-result/app-12/
    ├── app-12-bugfix/
    │   ├── app-12-bugfix-01.md ~ 05.md        # 5 条提示词
    ├── app-12-codegen/
    │   ├── app-12-codegen-06.md ~ 10.md       # index 从 06 接续
    ├── app-12-feature/
    │   ├── app-12-feature-11.md ~ 15.md
    ├── app-12-understand/
    │   └── app-12-understand-16.md
    ├── app-12-engineering/
    │   └── app-12-engineering-17.md
    ├── app-12-refactor/
    │   └── app-12-refactor-18.md
    └── app-12-test/
        └── app-12-test-19.md

修改:
  source code/app-12/src/...                   # Bug 注入（如有）
  GitHub: https://github.com/attitudeshuai/app-12  # git push
```

### Step 2: 用户在 Trae 执行并填写后

```
修改:
  ai-model-result/app-12/app-12-bugfix/
    └── app-12-bugfix-01.md                    # 填入 session id + 模型回答
```

### Step 3: analyze 后

```
新增:
  ai-model-result/app-12/app-12-bugfix/
    └── app-12-bugfix-01-评价结果.md            # 结构化评价
```

### Step 4: export 后

```
新增:
  deliverables/code-eval-solo/solo-0601/app-12/
    ├── csv-app-12-export.csv                   # 评价结果汇总
    └── csv-app-12-prompt-export.csv            # 提示词 Session ID 汇总
```
