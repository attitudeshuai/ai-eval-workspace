# cc-solo 目录结构样例

> 以 **session=cc-solo-0909**、**项目=app-12** 为例，展示「一份素材源码 → 按 7 类任务复制成多份任务副本 → 容器执行 → 记录/打分」的完整目录结构。

---

## 总览

```
ai-eval-workspace/
│
├── projects/cc-solo/                # 项目配置 + skills
│   ├── config.toml
│   ├── secrets.toml                    # 本地密钥（不提交）
│   ├── SKILL.md
│   ├── README.md
│   ├── skills/                         # 01-task-create / 02-round-capture / 03-score-annotate / 04-export-submit
│   ├── docs/                           # runbook / structure-example / annotate-guide / docker 系列
│   └── templates/                      # task-info.md / round-file.md / submit-headers.csv
│
├── deliverables/cc-solo/            # 导出产物（TODO：最终交付格式未定）
│   └── cc-solo-0909/
│
└── sessions/cc-solo/                # 工作数据（gitignore）
    └── cc-solo-0909/                  # {SESSION_NAME}
        │
        ├── source-code/                # 素材源 + 任务副本（由 "source code/" 改名）
        │   └── app-12/                 # 项目根
        │       ├── app-12/             #   素材源（唯一 git 仓库 = base commit 快照，原始源码）
        │       │   ├── src/、README.md、.gitignore
        │       │   └── .git/
        │       ├── app-12-bugfix/      #   类型分组（按类型 + 全局索引累加）
        │       │   ├── app-12-bugfix-01/   #   任务副本 = 复制素材源内容 + 改名（无 .git）
        │       │   └── app-12-bugfix-02/
        │       ├── app-12-codegen/
        │       │   └── app-12-codegen-06/
        │       ├── app-12-feature/
        │       │   ├── app-12-feature-11/
        │       │   └── app-12-feature-12/
        │       ├── app-12-understand/app-12-understand-16/
        │       ├── app-12-refactor/app-12-refactor-17/
        │       ├── app-12-engineering/app-12-engineering-18/
        │       └── app-12-test/app-12-test-19/
        │
        └── records/                    # 任务记录（R0N 模型：每任务一个目录，每轮一条数据）
            └── app-12/
                └── app-12-bugfix/
                    └── app-12-bugfix-01/            # 任务目录（= 任务名）
                        ├── task-info.md             # 共享运行环境字段
                        ├── app-12-bugfix-01-R01.md  # 第 1 轮 = 一条数据
                        ├── app-12-bugfix-01-R02.md  # 第 2 轮（如有）
                        ├── app-12-bugfix-01-R01-trajectory.jsonl   # 每轮轨迹切片
                        └── app-12-bugfix-01-trajectory.jsonl       # 完整轨迹
                …（app-12-codegen/、app-12-feature/ … 按类型分组，与 source-code 同名）
```

## 容器镜像（同一容器，结构镜像本地 source-code/app-12/）

```
/workspace/
└── app-12/                            # 项目根（= 本地 source-code/app-12/）
    ├── app-12/                        # 素材源（可选拷入）
    ├── app-12-bugfix/
    │   ├── app-12-bugfix-01/          # 每份 = 一个独立工作目录（模型在此执行）
    │   └── app-12-bugfix-02/
    ├── app-12-codegen/
    │   └── app-12-codegen-06/
    ├── app-12-feature/
    │   ├── app-12-feature-11/
    │   └── app-12-feature-12/
    └── …
```

> 容器内路径 = `/workspace/{项目}/{项目}-{类型}/{项目}-{类型}-{索引}/`，与本地 `source-code/{项目}/` 对齐。

## 依赖排除规则（本地 ⇄ 容器都执行）

- 素材源/任务副本只含**被 git 跟踪的源码文件**（`git ls-files` 列举）；`.gitignore` 里的依赖包（`node_modules/`、`.venv/`、`venv/`、`__pycache__/`、`dist/`、`build/` 等）体积大，**本地 → 容器、容器 → 本地（review/回导）一律不复制**。
- `docker cp` 不支持按 `.gitignore` 排除，所以不整目录 cp，改用：
  - 有 `.git` 时用 `git ls-files -z | tar -c --null -T -` 打包源码再进容器解包；或
  - 用 `rsync -a --exclude-from=.gitignore`（本地机器有 rsync 时）。
- 回导（容器 → 本地 review）同理，只回导源码文件与变更，不拖依赖包。

## 命名 / 索引 / 副本规则

- **任务名 = 副本目录名 = 记录目录名 = 容器工作目录名 = `{项目}-{类型}-{索引}`**（如 `app-12-bugfix-01`）。
- 类型 slug（`config.toml [task_types].aliases`）：`bugfix`/`codegen`/`feature`/`understand`/`refactor`/`engineering`/`test`。
- **索引全局累加**、两位补零：bugfix 01-05 → codegen 06-10 → feature 11-15 → understand 16 → refactor 17 → engineering 18 → test 19（配额按 `default_quotas`：bugfix/codegen/feature 各 5，其余各 1）。
- 副本 = 素材源复制 + 改名；**共用同一个 base commit 快照**；**暂不建每份独立 git、不提交/push**。

## 路径映射（config.toml → 实际路径）

| 变量 | 值 | 展开后 |
|------|-----|--------|
| `{work_root}` | `sessions/cc-solo` | `sessions/cc-solo` |
| `{SESSION_NAME}` | `[sessions].active` | `cc-solo-0909` |
| `{REPO_BASE_PATH}` | `[paths].repo_base_path` | `sessions/cc-solo/cc-solo-0909/source-code` |
| `{RECORD_DIR}` | `[paths].records_dir` | `sessions/cc-solo/cc-solo-0909/records` |
| `{PROJECT}` | 项目名（素材源目录名） | `app-12` |

| 用途 | 公式 | 实际路径 |
|------|------|---------|
| 项目根 | `{REPO_BASE_PATH}/{PROJECT}/` | `…/source-code/app-12/` |
| 素材源（唯一 git 仓库） | `{REPO_BASE_PATH}/{PROJECT}/{PROJECT}/` | `…/source-code/app-12/app-12/` |
| 任务副本 | `{REPO_BASE_PATH}/{PROJECT}/{PROJECT}-{类型}/{PROJECT}-{类型}-{索引}/` | `…/source-code/app-12/app-12-bugfix/app-12-bugfix-01/` |
| 任务记录目录 | `{RECORD_DIR}/{PROJECT}/{PROJECT}-{类型}/{PROJECT}-{类型}-{索引}/` | `…/records/app-12/app-12-bugfix/app-12-bugfix-01/` |
| 第 N 轮数据 | `…/{PROJECT}-{类型}-{索引}-R{NN}.md` | `…/records/app-12/app-12-bugfix/app-12-bugfix-01/app-12-bugfix-01-R01.md` |
| 完整轨迹 | `…/{PROJECT}-{类型}-{索引}-trajectory.jsonl` | `…/records/app-12/app-12-bugfix/app-12-bugfix-01/app-12-bugfix-01-trajectory.jsonl` |
| 容器工作目录 | `/workspace/{PROJECT}/{PROJECT}-{类型}/{PROJECT}-{类型}-{索引}/` | `/workspace/app-12/app-12-bugfix/app-12-bugfix-01/` |

## 一次完整执行后的文件变化

### Step 1: 生成（建副本 + 出题）
```
已有:
  source-code/app-12/app-12/                       # 素材源（唯一 git 仓库）
新增:
  source-code/app-12/
    ├── app-12-bugfix/app-12-bugfix-01/ ~ 05/     # 5 份任务副本（复制素材源 + 改名 + 按类型埋点）
    ├── app-12-codegen/app-12-codegen-06/ ~ 10/
    ├── app-12-feature/app-12-feature-11/ ~ 15/
    ├── app-12-understand/app-12-understand-16/
    ├── app-12-refactor/app-12-refactor-17/
    ├── app-12-engineering/app-12-engineering-18/
    └── app-12-test/app-12-test-19/
  records/app-12/
    └── …（对应 19 个任务目录，每目录含 task-info.md + 首轮提示词）
```

### Step 2: 容器化
```
docker cp source-code/app-12/. → 容器 /workspace/app-12/  （镜像结构）
```

### Step 3: 执行（模型在各副本独立工作目录跑）
```
容器 /workspace/app-12/app-12-bugfix/app-12-bugfix-01/ 被模型修改
```

### Step 4: 回导 + 打分
```
新增/更新:
  records/app-12/app-12-bugfix/app-12-bugfix-01/
    ├── app-12-bugfix-01-trajectory.jsonl      # 完整轨迹
    ├── app-12-bugfix-01-R01-trajectory.jsonl  # 第 1 轮轨迹切片
    └── app-12-bugfix-01-R01.md                # 第 1 轮数据（五维打分写入此文件）
```

### Step 5: 导出（TODO）
```
最终交付格式未定，先占位。
```

---

## 提交表样例（节选，导出脚本生成；字段待最终交付格式定稿）

| 任务名 | 任务类型 | 语言/框架 | Harness | 交付完整性 | 指令遵循 | 任务规划 | 推理能力 | 执行能力 | 其他问题 |
|---|---|---|---|---|---|---|---|---|---|
| app-12-bugfix-01 | Bug修复 | Python | Claude Code | 4 | 4 | 3 | 4 | 4 | 无 |

> 五维打分 = 交付完整性 / 指令遵循 / 任务规划 / 推理能力 / 执行能力，各 1-5 + 必填依据描述；一个任务（会话窗口）≤ 10 轮，一轮 = 一条数据。
