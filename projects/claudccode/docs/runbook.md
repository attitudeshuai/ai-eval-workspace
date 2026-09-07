# claudccode 满意度标注 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，一步一步完成「Claude Code / Codex 用户满意度标注」的全流程。

配置统一读取 `projects/claudccode/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 技术细节见 `skills/01-task-create.md` 等 skill 文件；评分表/原因写法速查见 `docs/annotate-guide.md`。

---

## 通用启动语

```text
cc {任务ID} {操作}
```

如：`cc solocc-0001 create`、`cc solocc-0001 round 1`、`cc solocc-0001 score 1`、`cc export`

> 任务 ID = **仓库目录名**（`repos/<repo>` 的目录名，如 `solocc-0001`），记录目录与轮次文件都以它为前缀，与仓库一一对应。

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

## ⚠️ 使用前必读

- **一个任务 = 一个会话窗口（≤10 轮）；一轮 = 一条数据**。
- **AI 交付文本必须先经去 AI 化**：AI 起草的提示词/评分依据无论练习还是正式，落盘/投递前都须先经 `skills/humanizer-zh` 去 AI 化（练习阶段允许 AI 直接打分、无需人工确认；正式交付再人工复核），并严格按五维模式；人工撰写的原文保持原样。
- 被标注模型跑在 **Claude Code / Codex CLI** 里，由用户在终端里操作，本 skill 不代跑。

## 前置准备

### 1. 配置本地环境

```bash
cp projects/claudccode/secrets-simple.toml projects/claudccode/secrets.toml
```

编辑 `secrets.toml`：

```toml
work_root = "sessions/claudccode"
active_session = "session-0907"
annotator = "张三"
```

### 2. 准备候选仓库（工作区）

将被标注仓库放到 `{work_root}/{SESSION_NAME}/repos/<repo>/`，或使用本机已有路径，需已 `git init` 且有可 push 的远端。

> 快照要求：仓库需 push 到评测团队可访问的远端；push 前确认 `.gitignore` 已覆盖 `.env`、密钥/连接串/token；已提交快照禁止 force-push / rebase。

---

## 第 1 步：新建任务（任务初始化 + 快照 + 出题）

### 指令模板

```text
cc solocc-0001 create
仓库: sessions/claudccode/session-0907/repos/solocc-0001
计划任务类型: 0-1代码生成
目标: 在划词插件里从零构建完整生词管理系统
Harness: Claude Code
Harness版本: 2.1.263
操作系统: MacOS/Linux
```

### AI 会执行

1. 校验仓库存在、工作区干净、`.gitignore` 无泄漏风险（`.env`/密钥/token 已覆盖）
2. **打初始快照**：若工作区未到基线，先提交一个 baseline commit → push → 取**完整 40 位 SHA** 生成 permalink（`https://github.com/<org>/<repo>/commit/<40sha>`）
3. 创建 `records/solocc-0001/task-info.md`：Repo URL、本地路径、初始环境快照、Harness、Harness版本、操作系统、环境可复现等级（共享字段）；记录目录名 = 仓库目录名（任务 ID）。轨迹根目录留待首轮 SessionID 回填后按 Harness 定位（Codex CLI→`~/.codex/sessions`、Claude Code→`~/.claude/projects`）
4. 起草**首轮提示词**（真实用户口径、自然语言）：可引用 `prompt-architect` 起草；练习阶段经人工确认后写盘即可，正式交付时再先经 `humanizer-zh` 去 AI 化。
5. 输出：任务信息文件路径 + 首轮提示词，提示用户确认后到 Claude Code/Codex 执行

### 产物

```text
records/solocc-0001/task-info.md
```

---

## 第 2 步：与模型交互（用户在 Claude Code / Codex 中）

1. 打开任务仓库目录（如 `repos/solocc-0001`），进入 Claude Code 或 Codex CLI
2. 粘贴首轮提示词，开始对话
3. 完成一轮后**无需手动带回 SessionID/TurnID**——agent 直接从本机轨迹自动定位并拆轮：Claude Code → `~/.claude/projects/<项目目录名>/<SessionID>.jsonl`（文件名=SessionID，一条 user 键入=一轮，promptId=TurnID）；Codex CLI → `~/.codex/sessions/<SessionID>/`。agent 同时会把该会话 `.jsonl` 复制一份到 `records/{REPO}/{REPO}-trajectory.jsonl`（重命名为仓库名，交付/上传用）。仅在读取失败时，再把 **SessionID / TurnID(promptId) / 轨迹位置 / 模型回答** 带回给 agent。

---

## 第 3 步：单轮录入（每轮一条数据）

### 指令模板

```text
cc solocc-0001 round 1
（SessionID / User Prompt / TurnID(promptId) 由 agent 从本机轨迹自取，无需手动填）
任务类型: 0-1代码生成
任务难度: 困难
语言/框架: JavaScript, Chrome MV3, Dexie
人工确认: 是
```

### AI 会执行

1. 读取本机轨迹，定位本任务会话并拆出第 N 轮（一轮=一次 user 键入），取其 User Prompt 原文与 promptId
2. 创建 `records/solocc-0001/solocc-0001-R01.md`，回填 User Prompt、任务类型/难度、语言/框架、TurnID
3. 从 `task-info.md` 继承 SessionID 等共享字段（导出时合并），并按 Harness 分行回填轨迹根目录
4. 校验：轮次 ≤ 10；TurnID 在任务内唯一；SessionID 与任务一致

### 产物

```text
records/solocc-0001/solocc-0001-R01.md
```

---

## 第 4 步：五维打分（依据：人工撰写，或 AI 起草 → 去 AI 化 → 人工复核）

### 指令模板

```text
cc solocc-0001 score 1
```

### AI 会执行

1. 打开 `solocc-0001-R01.md`，确认该轮已录入（有 User Prompt / TurnID）
2. **录入方式二选一**（先与用户确认）：
   - 人工打分：逐字段索要 **五维分数（1-5）+ 五条依据描述 + 其他问题** → 原样录入、不改写
   - AI 代打（练习阶段默认）：AI 结合真实轨迹/产物起草分数与依据 → **先经 `skills/humanizer-zh` 去 AI 化** → 严格按五维模式落盘（练习阶段无需人工确认；正式交付再人工核对）
3. 机械校验：五个分数为 1-5 整数；五条描述均非空；分数与描述方向一致性提示（请人工复核）
4. 询问是否继续下一轮（≤10 轮）；第 10 轮后强制结束本任务

### 产物

```text
records/solocc-0001/solocc-0001-R01.md   # 已填入五维打分与依据
```

---

## 第 5 步：会话结束，开新任务

- 达到 10 轮，或模型达成目标且无需继续时，本任务结束
- 新开 Claude Code/Codex 会话窗口与任务目录（`solocc-0002/...`），重复第 1-4 步

---

## 第 6 步：导出正式提交表

### 指令模板

```text
cc export
```

### AI 会执行

1. 扫描 `{RECORD_DIR}` 全部任务，读取 `task-info.md` + 各 `*-R*.md`
2. 运行导出脚本生成 CSV（每轮一行），输出：
   `deliverables/claudccode/{SESSION_NAME}/正式提交表-{SESSION_NAME}-{date}.csv`
3. 运行质检校验并输出报告（字段完整、分数范围、轮次 ≤10、SessionID 一致性、TurnID 唯一、快照格式、类型分布）

### 产物

```text
deliverables/claudccode/session-0907/正式提交表-session-0907-<date>.csv
```

---

## 第 7 步：投递飞书（满意度交付多维表格）

### 指令模板

```text
cc export feishu
（或）cc solocc-0001 feishu --submitter 张三
```

### AI 会执行

1. 确认已导出的提交表 CSV（质检通过、无警示未处理项）
2. **先 dry-run**：`python scripts/claudccode/append_delivery_feishu.py --csv <提交表> --dry-run`
3. dry-run 通过后正式投递（每行 = 一轮 = 一条记录）：
   `python scripts/claudccode/append_delivery_feishu.py --csv <提交表> --submitter 张三`
4. 输出每条追加的 record_id + 汇总（新增/已存在跳过/错误）

> 目标表见 `config.toml [feishu]`（`Lg0mbjRpPaxjhmsj27MckrJLnec` / `tble0z2KnzCfjJmZ`）。
> 凭证默认复用 `code-eval-gsb/secrets.toml [feishu]` 的 app_id/app_secret；命名差异（`feature迭代`、描述列空格等）由脚本自动映射。

### 产物

满意度交付多维表格新增 N 条记录（N = 提交表行数），每条含五维分数与描述。

### 注意事项

- 当天 20:00 前执行的数据当天提交；20:00 后产生的数据次日 14:00 前提交。
- 多维表格是最终交付物：投递前确认提交表已定稿、无返修；追加错误在表内手动删除后重投。
- 首次使用需为应用开通 `bitable:app` 权限并把应用加为该表协作者。
