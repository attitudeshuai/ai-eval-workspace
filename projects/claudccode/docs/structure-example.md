# claudccode 目录结构样例

> 以 **session=session-0907** 为例，展示「一个项目派生多个类型任务 + records 嵌套布局」后的完整目录结构。
> **任务 ID = 仓库目录名-类型slug**（如 `html-demo-feat`）；records 目录支持**嵌套**（项目分组 → 任务，推荐）或**扁平**（任务直接一层），导出脚本两种都认。

---

## 总览

```
ai-eval-workspace/
│
├── projects/claudccode/                # 项目配置 + skills
│   ├── config.toml
│   ├── secrets.toml                    # 本地密钥（不提交）
│   ├── SKILL.md
│   ├── README.md
│   ├── skills/                         # 01-task-create / 02-round-capture / 03-score-annotate / 04-export-submit
│   ├── docs/                           # runbook / structure-example / annotate-guide / docker 系列
│   └── templates/                      # task-info.md / round-file.md / submit-headers.csv
│
├── deliverables/claudccode/            # 导出产物
│   └── session-0907/
│       └── 正式提交表-session-0907-2026-09-08.csv
│
└── sessions/claudccode/                # 工作数据（gitignore）
    └── session-0907/                   # {SESSION_NAME}
        │
        ├── repos/                      # 素材源 + 各任务工作副本
        │   ├── html-demo/              #   素材源（上游内容，只读）
        │   ├── html-demo-feat/         #   任务工作副本：Feature迭代
        │   ├── html-demo-bugfix/       #   任务工作副本：Bug修复
        │   ├── python-helloworld/      #   素材源
        │   └── python-helloworld-feat/ #   任务工作副本：Feature迭代
        │
        └── records/                    # 任务记录（嵌套：项目分组 → 任务）
            ├── html-demo/              #   项目分组（不含 task-info.md）
            │   ├── html-demo-feat/     #     任务：Feature迭代
            │   │   ├── task-info.md
            │   │   ├── html-demo-feat-R01.md
            │   │   └── html-demo-feat-trajectory.jsonl
            │   └── html-demo-bugfix/   #     任务：Bug修复
            │       ├── task-info.md
            │       ├── html-demo-bugfix-R01.md ~ -R03.md
            │       └── html-demo-bugfix-trajectory.jsonl
            └── python-helloworld/      #   项目分组
                └── python-helloworld-feat/  # 任务：Feature迭代
                    └── task-info.md
```

> 真实轨迹**复制一份**到 `records/{REPO}/{TASK_ID}/{TASK_ID}-trajectory.jsonl`（交付/上传用）。Claude Code 在容器里做（题号 = 任务 ID），轨迹来源容器 `/home/node/.claude/projects/-workspace-<题号>/`；Codex 在本机 `~/.codex/sessions/`。轨迹目录按 Harness 分行，不许填串。

---

## 任务 ID 与类型 slug

| 类型 | slug | 示例 |
|------|------|------|
| 0-1代码生成 | `codegen` | `solocc-0001-codegen` |
| Feature迭代 | `feat` | `html-demo-feat`、`python-helloworld-feat` |
| Bug修复 | `bugfix` | `html-demo-bugfix` |
| 代码理解 | `understand` | … |
| 代码重构 | `refactor` | … |
| 工程化 | `engineering` | … |
| 代码测试 | `test` | … |

> slug 见 `config.toml [task_types].aliases`。任务 ID / 题号始终扁平（`{repo}-{slug}`），**不能带 `/`**（容器 `cc` 脚本限制）；「多一层」只发生在 records 目录的文件系统分组上，不改变任务 ID 与题号。

---

## 同一项目的多个任务：各自独立快照

同一个项目 `html-demo` 有两个任务，初始快照是**两个不同的 commit**：

| 任务 | 任务 ID | 初始快照（baseline commit） |
|------|---------|----------------------------|
| Feature迭代 | `html-demo-feat` | `claudccode-html-demo` 的 commit `6dbc15c190d6698d75a86235db2055ec88bba3c3` |
| Bug修复 | `html-demo-bugfix` | `claudccode-html-demo-bugfix` 的 commit（mock 占位 SHA） |

> 同一任务内（各轮）共享同一个快照；不同任务（即使同项目）各自独立快照 + 独立远程仓库 `claudccode-{TASK_ID}`。

---

## 路径映射（config.toml → 实际路径）

| 变量 | 值 | 示例 |
|------|-----|------|
| `{work_root}` | `sessions/claudccode` | `sessions/claudccode` |
| `{SESSION_NAME}` | `[sessions].active` | `session-0907` |
| `{REPO_BASE_PATH}` | `[paths].repo_base_path` | `…/repos` |
| `{RECORD_DIR}` | `[paths].records_dir` | `…/records` |
| `{REPO}` | 仓库目录名（项目/素材名） | `html-demo` |
| `{TASK_ID}` | `{REPO}-{类型slug}`（任务 ID） | `html-demo-bugfix` |

| 用途 | 公式 | 实际路径 |
|------|------|---------|
| 素材源 | `{REPO_BASE_PATH}/{REPO}/` | `…/repos/html-demo/` |
| 任务工作副本 | `{REPO_BASE_PATH}/{TASK_ID}/` | `…/repos/html-demo-bugfix/` |
| 任务记录（嵌套） | `{RECORD_DIR}/{REPO}/{TASK_ID}/` | `…/records/html-demo/html-demo-bugfix/` |
| 任务记录（扁平） | `{RECORD_DIR}/{TASK_ID}/` | `…/records/html-demo-bugfix/` |
| 任务信息文件 | `…/task-info.md` | `…/records/html-demo/html-demo-bugfix/task-info.md` |
| 第 N 轮数据 | `…/{TASK_ID}-R{NN}.md` | `…/html-demo-bugfix/html-demo-bugfix-R01.md` |
| 正式提交表 | `deliverables/claudccode/{SESSION_NAME}/正式提交表-{SESSION_NAME}-{date}.csv` | `deliverables/claudccode/session-0907/正式提交表-session-0907-2026-09-08.csv` |

---

## 迁移说明（2026-09-08）

- `records/html-demo/`（原 Feature 任务，扁平）→ `records/html-demo/html-demo-feat/`，轮次/轨迹文件重命名为 `html-demo-feat-*`。
- `records/html-demo-bugfix/` → `records/html-demo/html-demo-bugfix/`（叶子名不变，文件名不变）。
- `records/python-helloworld/` → `records/python-helloworld/python-helloworld-feat/`。
- `repos/` 下的素材源（`{repo}`）与任务工作副本（`{repo}-{slug}`）命名未变。

---

## 提交表样例（节选，导出脚本生成）

| 任务类型 | 任务难度 | 语言/框架 | Harness | Harness版本 | 操作系统 | 环境可复现等级 | 初始环境快照 | User Prompt | SessionID | TurnID/PromptID | 轨迹文件 | 交付完整性 | 交付完整性-描述 | … | 其他问题 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Feature迭代 | 中等 | HTML, CSS, JavaScript | Claude Code | 2.1.236 | Windows | 无外部依赖 | https://github.com/attitudeshuai/claudccode-html-demo-feat/commit/6dbc15c… | 加筛选与编辑… | 7bbdfcb8… | <promptId> | records/html-demo/html-demo-feat/html-demo-feat-trajectory.jsonl | 4 | 完成… | … | 无 |
| Bug修复 | 中等 | HTML, CSS, JavaScript | Claude Code | 2.1.236 | Windows | 无外部依赖 | https://github.com/attitudeshuai/claudccode-html-demo-bugfix/commit/<40sha> | 修复 id 撞车… | 3a91e6c2… | <promptId> | records/html-demo/html-demo-bugfix/html-demo-bugfix-trajectory.jsonl | 4 | 完成… | … | 无 |

> 同一任务各行 `Harness/版本/OS/可复现/快照/SessionID` 相同；不同任务（同项目不同类型）的 `初始环境快照` 各自独立。导出脚本对「嵌套」「扁平」两种布局都按叶子目录名 = 任务 ID 分组。
