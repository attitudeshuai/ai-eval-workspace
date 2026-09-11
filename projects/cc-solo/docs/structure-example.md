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
│   └── templates/                      # task-info.md / round-file.md（submit-headers.csv 已随旧流程退役）
│
├── deliverables/cc-solo/            # 评价结果（每轮一条 JSON）+ 质检报告
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

## 容器（一题一容器，容器内恒为 `/workspace`）

- **1 任务 = 1 容器**：容器名统一 `cc-solo-{任务}`（如 `cc-solo-app-12-bugfix-01`），题目身份由「容器名 + 挂载目录」承载，容器内**不再有按题号嵌套的目录**。
- 容器内工作目录恒为 `/workspace`，内容 = 本题任务副本内容：
  - **Windows**：直接把本机任务副本目录挂载为 `/workspace`（`docker run -d --mount type=bind,source=<副本目录>,target=/workspace`），无需播种、无需回导。
  - **Mac**：先 `docker run -it` 起容器，再在首轮交互前由 agent 把任务副本内容播种进挂载目录。
- 轨迹恒在容器内 `/home/node/.claude/projects/-workspace/`。

```text
cc-solo-app-12-bugfix-01   →  /workspace  = 本机 source-code/app-12/app-12-bugfix/app-12-bugfix-01/
cc-solo-app-12-bugfix-02   →  /workspace  = 本机 source-code/app-12/app-12-bugfix/app-12-bugfix-02/
cc-solo-app-12-codegen-06  →  /workspace  = 本机 source-code/app-12/app-12-codegen/app-12-codegen-06/
…
```

> 容器内路径恒为 `/workspace`（不再有 `/workspace/{项目}/{项目}-{类型}/{项目}-{类型}-{索引}/`）；题目身份由容器名与挂载目录承载。

## 依赖排除规则（进入容器前后都执行）

- 素材源/任务副本只含**被 git 跟踪的源码文件**（`git ls-files` 列举）；`.gitignore` 里的依赖包（`node_modules/`、`.venv/`、`venv/`、`__pycache__/`、`dist/`、`build/` 等）体积大，**不放进挂载目录 / 播种目录**。
- Windows 直接挂载副本目录，所以**挂载前就应确保目录里没有依赖包**（副本 = 素材源复制时已按 `.gitignore` 排除）。
- Mac 播种用 `rsync -a --exclude-from=.gitignore`（无 rsync 时用 `git ls-files -z | tar -c --null -T -` 打包解包）。
- 任务结束后，清理模型在挂载目录里新装的依赖包（`node_modules`/`.venv` 等），别把依赖提交进快照。

## 命名 / 索引 / 副本规则

- **任务名 = 副本目录名 = 记录目录名 = `{项目}-{类型}-{索引}`**（如 `app-12-bugfix-01`）；容器名 `cc-solo-{任务}`，容器内工作目录恒为 `/workspace`。
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
| 容器名 | `cc-solo-{PROJECT}-{类型}-{索引}` | `cc-solo-app-12-bugfix-01` |
| 容器工作目录 | `/workspace`（恒为 `/workspace`，= 本题副本内容） | `/workspace` |
| 容器轨迹目录 | `/home/node/.claude/projects/-workspace/` | `/home/node/.claude/projects/-workspace/` |

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

### Step 2: 容器化（一题一容器）
```
每题一个容器 cc-solo-{任务}：
  Windows：docker run -d --name cc-solo-app-12-bugfix-01 --mount type=bind,source=source-code/app-12/app-12-bugfix/app-12-bugfix-01,target=/workspace …
  Mac    ：docker run -it … 起容器后，agent 把该副本目录播种进 /workspace
```

### Step 3: 执行（模型在本任务副本的工作目录 /workspace 里跑）
```
容器 cc-solo-app-12-bugfix-01 的 /workspace 被模型修改
（= 本机 source-code/app-12/app-12-bugfix/app-12-bugfix-01/，Windows 天然落回本机）
```

### Step 4: 导出轨迹 + 收尾
```
新增/更新:
  records/app-12/app-12-bugfix/app-12-bugfix-01/
    ├── app-12-bugfix-01-trajectory.jsonl      # 完整轨迹（每轮 docker cp -workspace 目录）
    ├── app-12-bugfix-01-R01-trajectory.jsonl  # 第 1 轮轨迹切片
    └── app-12-bugfix-01-R01.md                # 第 1 轮数据（五维打分写入此文件）

  Windows：代码已在挂载目录，无需回导；任务结束清理依赖包后 docker stop / rm 容器。
  Mac    ：收尾回导源码到任务副本（rsync 按 .gitignore 排除），再 docker rm 容器。
```

### Step 5: 生成评价结果 + 提交（接口已就位；本阶段先不提交）

> 指令：用户发 `cc-solo export`，脚本由 agent 执行（用户不跑 Python 命令）。

```
新增:
  deliverables/cc-solo/cc-solo-0909/
    ├── 评价结果-cc-solo-0909-<date>.json        # 主产物：24 字段 × 每轮一条 + 轨迹附件路径
    └── 评价结果-cc-solo-0909-<date>-质检报告.md  # 逐条 error / warn（不再产出人工核对 CSV）

  agent 执行（本阶段只跑第一条）：
    python scripts/cc-solo/build_eval_result.py
    # 以下两条等用户确认要提交时再执行
    # python scripts/cc-solo/submit_eval_result.py --result <json>            # dry-run
    # python scripts/cc-solo/submit_eval_result.py --result <json> --commit   # 上传轨迹 + 提交
```

---

## 评价结果样例（节选；真实产物见 deliverables/，字段以 docs/submission/fields.json 为准）

| 任务 | 任务类型 | 语言/框架 | Harness | 轮次排序 | 交付完整性 | 指令遵循 | 任务规划 | 推理能力 | 执行能力 | 其他问题 |
|---|---|---|---|---|---|---|---|---|---|---|
| app-12-bugfix-01 | Bug修复 | Python | Claude Code | 1 | 4 | 4 | 3 | 4 | 4 | 无 |

> 五维打分 = 交付完整性 / 指令遵循 / 任务规划 / 推理能力 / 执行能力，各 1-5 + 必填依据描述；一个任务（会话窗口）≤ 10 轮，一轮 = 一条数据；每条另含 env_snapshot / User Prompt / SessionID / TurnID / 轨迹附件等 24 个字段。
