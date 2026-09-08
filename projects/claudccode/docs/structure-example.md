# claudccode 目录结构样例

> 以 **session=session-0907**、仓库 `solocc-0001` 为例，展示执行全流程后的完整目录结构。**任务 ID = 仓库目录名**（不再用 `cc-N`），记录目录与轮次文件前缀都用仓库名。

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
│   │   ├── runbook-windows.md
│   │   ├── structure-example.md
│   │   ├── annotate-guide.md
│   │   ├── CLAUDE_CODE_DOCKER_MAC.md
│   │   ├── CLAUDE_CODE_DOCKER_windows.md
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
        │   └── solocc-0001/            #   仓库目录名 = 任务 ID；需已推到评测可访问远端
        │       ├── .git/
        │       └── src/
        │
        └── records/                    # 任务记录（目录名 = 仓库目录名 = 任务 ID）
            └── solocc-0001/
                ├── task-info.md        #   共享会话/环境字段
                ├── solocc-0001-R01.md  #   第 1 轮数据（一条数据）
                ├── solocc-0001-R02.md  #   第 2 轮数据
                ├── solocc-0001-R03.md
                ├── solocc-0001-R04.md
                ├── solocc-0001-R05.md
                └── solocc-0001-trajectory.jsonl   #   真实轨迹副本（从容器 /home/node/.claude/projects/-workspace-<题号>/.jsonl 导出，交付上传用）
```

> 真实轨迹**复制一份**到 `records/{REPO}/{REPO}-trajectory.jsonl`（交付/上传用；重命名为仓库名，避免与原始 SessionID 文件名混淆）。Claude Code 在容器里做（题号 = 仓库目录名），轨迹先导出到本机（来源容器 `/home/node/.claude/projects/-workspace-<题号>/`）再复制为 `{REPO}-trajectory.jsonl`；Codex 在本机 `~/.codex/sessions/`。轨迹目录按 Harness 分行：Codex CLI→`~/.codex/sessions/`，Claude Code→`records/{REPO}/{REPO}-trajectory.jsonl`，不许填串。

---

## 路径映射（config.toml → 实际路径）

| 变量 | config.toml 值 | 展开后（相对于 workspace） |
|------|---------------|--------------------------|
| `{work_root}` | `sessions/claudccode` | `sessions/claudccode` |
| `{SESSION_NAME}` | `[sessions].active` | `session-0907` |
| `{REPO_BASE_PATH}` | `[paths].repo_base_path` | `sessions/claudccode/session-0907/repos` |
| `{RECORD_DIR}` | `[paths].records_dir` | `sessions/claudccode/session-0907/records` |
| `{REPO}` | 仓库目录名（记录目录名 = 任务 ID） | `solocc-0001` |

| 用途 | 公式 | 实际路径 |
|------|------|---------|
| 任务信息文件 | `{RECORD_DIR}/{REPO}/task-info.md` | `sessions/claudccode/session-0907/records/solocc-0001/task-info.md` |
| 第 N 轮数据文件 | `{RECORD_DIR}/{REPO}/{REPO}-R{NN}.md` | `sessions/claudccode/session-0907/records/solocc-0001/solocc-0001-R01.md` |
| 正式提交表 | `deliverables/claudccode/{SESSION_NAME}/正式提交表-{SESSION_NAME}-{date}.csv` | `deliverables/claudccode/session-0907/正式提交表-session-0907-2026-09-07.csv` |

---

## 一次完整执行后的文件变化

### Step 1: task-create（新建任务 solocc-0001，5 轮窗口）

```
前置：
  新建独立远程仓库 claudccode-solocc-0001（github_username + PAT 创建），把本地 origin 指向它（来源仓库仅作内容来源，不再向其提交）
新增:
  records/solocc-0001/
    └── task-info.md          # 共享字段：Repo URL/快照/Harness/版本/OS/可复现等级/SessionID/轨迹根
  repos/solocc-0001/          # 首轮交互前已提交并把干净基线 commit push 到新仓库

修改:
  qianmo317/claudccode-solocc-0001 推送了初始快照 commit（40 位 SHA，不做 force-push/rebase）
```

### Step 2: 第 1 轮交互后 round-capture（agent 自取 SessionID/TurnID）

```
新增:
  records/solocc-0001/solocc-0001-R01.md    # 首轮提示词原文 + TurnID/PromptID + 任务类型/难度/语言框架
```

### Step 3: 第 1 轮打分（score-annotate，人工）

```
修改:
  records/solocc-0001/solocc-0001-R01.md    # 填入五维分数 + 五条依据描述 + 其他问题
```

### Step 4: 第 2..5 轮

```
新增:
  records/solocc-0001/solocc-0001-R02.md ~ solocc-0001-R05.md    # 每轮 = 一条数据
```

（第 5 轮若出现需要人为「继续」的思考超限，计入轮次。）

### Step 5: 会话结束 → 下一个任务

```
新增:
  records/solocc-0002/task-info.md + solocc-0002-R01.md ...
```

### Step 6: export-submit（导出提交表）

```
新增:
  deliverables/claudccode/session-0907/正式提交表-session-0907-2026-09-07.csv
  # 每轮一行：solocc-0001 的 5 行 + solocc-0002 的 3 行 = 8 条数据
```

---

## 提交表样例（节选，导出脚本生成）

| 任务类型 | 任务难度 | 语言/框架 | Harness | Harness版本 | 操作系统 | 环境可复现等级 | 初始环境快照 | User Prompt | SessionID | TurnID/PromptID | 轨迹文件 | 交付完整性 | 交付完整性-描述 | … | 其他问题 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bug修复 | 中等 | Python, FastAPI | Claude Code | 1.0.x | MacOS/Linux | 无外部依赖 | https://github.com/…/commit/<40sha> | 修复 xx… | 3f9a… | <promptId> | records/solocc-0001/solocc-0001-trajectory.jsonl | 4 | 完成… | … | 无 |

> 同一任务各行 `Harness/版本/OS/可复现/快照/SessionID` 相同，仅 `User Prompt/TurnID/类型/难度/语言/五维` 不同。
