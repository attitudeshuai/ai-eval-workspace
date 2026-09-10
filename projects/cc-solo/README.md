# cc-solo：Claude Code 用户满意度标注

对真实 Coding Agent（**Claude Code**）的使用过程做用户满意度标注：还原真实用户反馈信号，判断模型是否真正满足了用户需求，为模型训练与持续优化提供数据。

## 核心思路

**一个任务 = 一个会话窗口；一轮对话 = 一条数据。**

1. 从候选仓库中挑选题目（避免雷同题），在会话**首轮前**对工作区打初始环境快照（commit permalink）
2. 在 Claude Code 中按真实用户口径出题并交互（每会话窗口 ≤ 10 轮）
3. 对**每一轮**对话按五维（交付完整性 / 指令遵循 / 任务规划 / 推理能力 / 执行能力）1-5 打分并撰写依据
4. 汇总成正式提交表：**每个有效轮次一行**，同一会话各轮共享一组运行环境字段

> ⚠️ 质量红线：AI 生成的提示词与交付文本（含 AI 起草的五维打分依据）必须先经 `skills/humanizer-zh` 去 AI 化 + 人工复核，方可使用/落盘/投递；人工撰写的原文保持原样、不做 AI 改写。本 skill 中 AI Agent 负责记录、起草、去 AI 化、机械校验与导出，最终由人工把关。

## 目录结构

```
projects/cc-solo/
├── config.toml                 # 项目配置（路径、类型、难度、评分、轮次上限）
├── SKILL.md                    # AI Agent 执行规范（入口）
├── secrets-simple.toml         # 本地敏感配置模板
├── secrets.toml                # 本地敏感配置（gitignore，不提交）
├── README.md                   # 本文件
├── skills/                     # 01-task-create / 02-round-capture / 03-score-annotate / 04-export-submit
├── docs/
│   ├── runbook.md              # 逐步操作手册（Mac）
│   ├── runbook-windows.md      # 逐步操作手册（Windows）
│   ├── structure-example.md    # 目录结构样例
│   ├── annotate-guide.md       # 评分表/原因写法速查
│   └── CLAUDE_CODE_DOCKER_*.md # Claude Code Docker 使用说明（Mac/Windows）
└── templates/                  # task-info / round-file / 提交表表头
```

## 快速开始

### 1. 配置本地环境

```bash
cp projects/cc-solo/secrets-simple.toml projects/cc-solo/secrets.toml
```

编辑 `secrets.toml`：

```toml
work_root = "sessions/cc-solo"
active_session = "session-0907"
annotator = "你的名字"
```

### 2. 新建一个任务（任务 = 一个会话窗口）

向 AI Agent 发送：

```text
cc <仓库名> create
任务类型: Bug修复
```

> 只给「仓库名 + 任务类型」即可。agent 会按「仓库名 + 类型 slug」拼任务 ID（如 `html-demo-bugfix`），校验仓库、打初始快照并 push、建任务目录、起草首轮提示词（人工确认后写入）、把工作副本 docker cp 进容器。

### 3. 录入一轮 + 打分（每轮一条数据）

在 Claude Code 中完成一轮交互后：

```text
cc html-demo-bugfix round 1
```

agent 会执行 docker 导出轨迹 + 代码、切出本轮轨迹、录入第 1 轮数据。

再按五维打分（依据：人工撰写，或 AI 代打 → 读轨迹 + implementation-reviewer + 去 AI 化）：

```text
cc html-demo-bugfix score 1
```

不满意时 agent 会自动拆分不满点、生成下一轮提示词（`-R02-prompt.md`，开头「修复bug：」）。

### 4. 导出正式提交表 + 投递飞书

```text
cc export
cc export feishu
```

导出到 `deliverables/cc-solo/{SESSION_NAME}/正式提交表-{SESSION_NAME}-{date}.csv`（每轮一行），随后逐行追加到满意度交付飞书多维表格（地址见 `config.toml [feishu]`；凭证复用 GSB 应用的 `code-eval-gsb/secrets.toml [feishu]`）。

## 多人协作

- 每个人在本地 `secrets.toml` 中配置自己的路径、session 与 annotator
- `config.toml` 默认值仅作参考，会被 `secrets.toml` 覆盖
- 不要提交 `secrets.toml` 到 Git
- 当天 20:00 前执行的数据当天提交；20:00 后产生的数据次日 14:00 前提交（TPM 层面执行）
