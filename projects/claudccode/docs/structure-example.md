# claudccode 目录结构样例

> 以 **session=session-0907** 为例（轮次数为通用示例，本地 `sessions/claudccode/session-0907/` 已随附实际演示数据：cc-1 两轮、cc-2 一轮），展示执行全流程后的完整目录结构。

---

## 总览

```
ai-eval-workspace/
│
├── projects/claudccode/                # 项目配置 + skills
│   ├── config.toml
│   ├── secrets.toml                    # 本地密钥（不提交）
│   ├── SKILL.md                        # 技能索引导航
│   ├── README.md
│   ├── skills/
│   │   ├── 01-task-create.md
│   │   ├── 02-round-capture.md
│   │   ├── 03-score-annotate.md
│   │   └── 04-export-submit.md
│   ├── docs/
│   │   ├── runbook.md
│   │   ├── structure-example.md
│   │   ├── annotate-guide.md
│   │   └── ClaudeCcode 用户满意度标注.docx
│   └── templates/
│       ├── task-info.md
│       ├── round-file.md
│       └── submit-headers.csv
│
├── deliverables/claudccode/            # 导出产物
│   └── session-0907/
│       └── 正式提交表-session-0907-2026-09-07.csv
│
└── sessions/claudccode/                # 工作数据（gitignore）
    └── session-0907/                   # {SESSION_NAME}
        │
        ├── repos/                      # 被标注仓库工作副本（初始快照处）
        │   └── cc-1-repo/              #   示例：本地工作区；需已推到评测可访问远端
        │       ├── .git/
        │       └── src/
        │
        └── records/                    # 任务记录
            ├── cc-1/
            │   ├── task-info.md        #   共享会话/环境字段
            │   ├── cc-1-R01.md         #   第 1 轮数据（一条数据）
            │   ├── cc-1-R02.md         #   第 2 轮数据
            │   ├── cc-1-R03.md
            │   ├── cc-1-R04.md
            │   └── cc-1-R05.md
            └── cc-2/
                ├── task-info.md
                ├── cc-2-R01.md
                ├── cc-2-R02.md
                └── cc-2-R03.md
```

> 真实轨迹**不复制**进仓库：SessionID/TurnID/轨迹根目录已足够定位，质检按 ID 回看真实轨迹。轨迹目录按 Harness 分行：Codex CLI→`~/.codex/sessions/`，Claude Code→`~/.claude/projects/`，不许填串。

---

## 路径映射（config.toml → 实际路径）

| 变量 | config.toml 值 | 展开后（相对于 workspace） |
|------|---------------|--------------------------|
| `{work_root}` | `sessions/claudccode` | `sessions/claudccode` |
| `{SESSION_NAME}` | `[sessions].active` | `session-0907` |
| `{REPO_BASE_PATH}` | `[paths].repo_base_path` | `sessions/claudccode/session-0907/repos` |
| `{RECORD_DIR}` | `[paths].records_dir` | `sessions/claudccode/session-0907/records` |
| `{TASK_PREFIX}` | `[naming].task_prefix` | `cc` |

| 用途 | 公式 | 实际路径 |
|------|------|---------|
| 任务信息文件 | `{RECORD_DIR}/{TASK_ID}/task-info.md` | `sessions/claudccode/session-0907/records/cc-1/task-info.md` |
| 第 N 轮数据文件 | `{RECORD_DIR}/{TASK_ID}/{TASK_ID}-R{NN}.md` | `sessions/claudccode/session-0907/records/cc-1/cc-1-R01.md` |
| 正式提交表 | `deliverables/claudccode/{SESSION_NAME}/正式提交表-{SESSION_NAME}-{date}.csv` | `deliverables/claudccode/session-0907/正式提交表-session-0907-2026-09-07.csv` |

---

## 一次完整执行后的文件变化

### Step 1: task-create（新建任务 cc-1，5 轮窗口）

```
新增:
  records/cc-1/
    └── task-info.md          # 共享字段：Repo URL/快照/Harness/版本/OS/可复现等级/SessionID/轨迹根
  repos/cc-1-repo/            # 首轮交互前已提交并 push（快照 commit permalink 记入 task-info.md）

修改:
  远端 cc-1-repo 推送了初始快照 commit（40 位 SHA，不做 force-push/rebase）
```

### Step 2: 第 1 轮交互（用户在 Claude Code/Codex 中）后 round-capture

```
新增:
  records/cc-1/cc-1-R01.md    # 首轮提示词原文 + TurnID/PromptID + 任务类型/难度/语言框架
```

### Step 3: 第 1 轮打分（score-annotate，人工）

```
修改:
  records/cc-1/cc-1-R01.md    # 填入五维分数 + 五条依据描述 + 其他问题
```

### Step 4: 第 2..5 轮

```
新增:
  records/cc-1/cc-1-R02.md ~ cc-1-R05.md    # 每轮 = 一条数据
```

（第 5 轮若出现需要人为「继续」的思考超限，计入轮次。）

### Step 5: 会话结束 → 下一个任务

```
新增:
  records/cc-2/task-info.md + cc-2-R01.md ...
```

### Step 6: export-submit（导出提交表）

```
新增:
  deliverables/claudccode/session-0907/正式提交表-session-0907-2026-09-07.csv
  # 每轮一行：cc-1 的 5 行 + cc-2 的 3 行 = 8 条数据
```

---

## 提交表样例（节选，导出脚本生成）

| 任务类型 | 任务难度 | 语言/框架 | Harness | Harness版本 | 操作系统 | 环境可复现等级 | 初始环境快照 | User Prompt | SessionID | TurnID/PromptID | 轨迹文件 | 交付完整性 | 交付完整性-描述 | … | 其他问题 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bug修复 | 中等 | Python, FastAPI | Claude Code | 1.0.x | MacOS/Linux | 无外部依赖 | https://github.com/…/commit/<40sha> | 修复 xx… | 3f9a… | <promptId> | ~/.claude/projects/… | 4 | 完成… | … | 无 |

> 同一任务各行 `Harness/版本/OS/可复现/快照/SessionID` 相同，仅 `User Prompt/TurnID/类型/难度/语言/五维` 不同。
