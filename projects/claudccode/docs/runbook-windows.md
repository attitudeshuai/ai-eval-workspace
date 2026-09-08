# claudccode 满意度标注 Runbook（Windows）

本 Runbook 是 [runbook.md](runbook.md) 的 Windows 版。流程、指令模板、产物与 Mac 版完全一致，**只有「第 2 步：与模型交互」里操作 Claude Code 的终端命令按 Windows 版 Docker 用法改写**。Windows 版 Docker 的完整使用说明见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)。

配置统一读取 `projects/claudccode/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 技术细节见 `skills/01-task-create.md` 等 skill 文件；评分表/原因写法速查见 `docs/annotate-guide.md`。

## 与 Mac 版的关键差异（速览）

| 环节 | Mac 版 | Windows 版（本文档） |
|---|---|---|
| 镜像 | `adminfather/benzhi-claude-code` | `nicehey/benzhi-claude-code:1.0` |
| 容器入口 | `docker exec -it benzhi-claude-code cc <题号>`（内置 `cc` 脚本自动建目录并拉起 Claude） | `mkdir -p` + `docker exec -it -w … bash` 进入后手动 `claude` |
| 命令审批 | `cc` 内置 `--dangerously-skip-permissions`，Claude 自动执行命令 | 普通 `claude`，执行命令/改文件前会询问，需确认「允许」 |
| 退出对话 | `/exit` 一次 | 先 `/exit` 退出 Claude，再 `exit` 退出容器 bash 回到 PowerShell |
| 工作目录 | `/workspace/<题号>` | 相同 |
| 轨迹目录 | `/home/node/.claude/projects/-workspace-<题号>/` | 相同 |
| 轨迹导出 | `docker cp …` 到 `records/<REPO>/` | 相同，但需在 PowerShell（宿主）里执行 |

> 除第 2 步的终端命令外，其余各步（建任务/出题/单轮录入/五维打分/导出提交表/投递飞书）与 Mac 版完全一致。第 3~7 步照抄 Mac 版即可。

---

## 通用启动语

```text
cc {任务ID} {操作}
```

如：`cc solocc-0001 create`、`cc solocc-0001 round 1`、`cc solocc-0001 score 1`、`cc export`

> 这里的 `cc {任务ID} {操作}` 是**给 AI agent 的自然语言指令**（runbook 通用缩写），不是容器命令。Windows 容器里**没有** `cc` 快捷入口——进入容器后是手动敲 `claude`。两者不要混淆。

> 任务 ID = **仓库目录名**（`repos/<repo>` 的目录名，如 `solocc-0001`），记录目录与轮次文件都以它为前缀，与仓库一一对应。

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

## ⚠️ 使用前必读

- **一个任务 = 一个会话窗口（≤10 轮）；一轮 = 一条数据**。
- **AI 交付文本必须先经去 AI 化**：AI 起草的提示词/评分依据无论练习还是正式，落盘/投递前都须先经 `skills/humanizer-zh` 去 AI 化（练习阶段允许 AI 直接打分、无需人工确认；正式交付再人工复核），并严格按五维模式；人工撰写的原文保持原样。
- 被标注模型跑在 **Claude Code / Codex CLI** 里，由用户在终端里操作，本 skill 不代跑。
- Windows 下 Claude Code 跑在 Docker 容器里，**终端命令用 PowerShell 执行**；Codex CLI 仍在本机直接跑。

## 前置准备

### 1. 配置本地环境

```powershell
Copy-Item projects/claudccode/secrets-simple.toml projects/claudccode/secrets.toml
```

编辑 `secrets.toml`：

```toml
work_root = "sessions/claudccode"
active_session = "session-0907"
annotator = "张三"
```

### 2. 准备候选仓库（工作区）

将被标注仓库放到 `{work_root}/{SESSION_NAME}/repos/<repo>/`（Windows 下形如 `sessions\claudccode\session-0907\repos\solocc-0001`），或使用本机已有路径，需已 `git init` 且有可 push 的远端。

> **⚠️ 建任务前先建新远程仓库（前置）**：来源仓库（如 `gsb0731-xxx`）是已使用/共享仓库，**不能直接提交**。进入第 1 步前，先用 `github_username` + PAT 为它**新建一个全新的远程仓库**（命名建议 `claudccode-{REPO}`，如 `claudccode-solocc-0001`），并把本地远端（origin）指到该新仓库。之后快照、模型交互、提交都基于这个新仓库。
>
> 快照要求：仓库需 push 到评测团队可访问的**新**远端（设为 **public** 公开仓库，或至少加协作者）；push 前确认 `.gitignore` 已覆盖 `.env`、密钥/连接串/token；已提交快照禁止 force-push / rebase。

---

## 第 1 步：新建任务（任务初始化 + 快照 + 出题）

### 指令模板

```text
cc solocc-0001 create
仓库: sessions/claudccode/session-0907/repos/solocc-0001
计划任务类型: 0-1代码生成
目标: 在划词插件里从零构建完整生词管理系统
Harness: Claude Code
Harness版本: 1.0
操作系统: Windows
```

> Windows 下 `Harness版本` 填 Windows 镜像 `nicehey/benzhi-claude-code:1.0` 对应的 Claude Code 实际版本（以 `claude --version` 输出为准）。

### AI 会执行

1. 校验仓库存在、工作区干净、`.gitignore` 无泄漏风险（`.env`/密钥/token 已覆盖）
2. **新建独立远程仓库（前置）**：用 `github_username` + PAT 创建 `claudccode-{REPO}` 新仓库，把本地 origin 指向它；来源仓库仅作内容来源，不向其提交。
3. **打初始快照**：提交一个 baseline commit → push 到**新仓库** → 取**完整 40 位 SHA** 生成 permalink（`https://github.com/<owner>/claudccode-{REPO}/commit/<40sha>`）
4. 创建 `records/solocc-0001/task-info.md`：Repo URL、本地路径、初始环境快照、Harness、Harness版本、操作系统、环境可复现等级（共享字段）；记录目录名 = 仓库目录名（任务 ID）。轨迹根目录留待首轮 SessionID 回填后按 Harness 定位（Codex CLI→`~/.codex/sessions`；Claude Code→本次导出到本机的 `records/{REPO}/{REPO}-trajectory.jsonl`，其容器内来源为 `/home/node/.claude/projects/-workspace-<REPO>/`）
5. 起草**首轮提示词**（真实用户口径、自然语言）：可引用 `prompt-architect` 起草；练习阶段经人工确认后写盘即可，正式交付时再先经 `humanizer-zh` 去 AI 化。
6. 输出：任务信息文件路径 + 首轮提示词，提示用户确认后到 Windows 容器内 Claude Code / 本机 Codex 执行

> ⚠️ **出题要难**：首轮提示词做高难度、多需求、跨模块/多约束题，严禁简单题。**Bug修复先埋点**：在初始化/打快照阶段把 bug 写进源码（无注释标记、藏得深、可复现），埋点 commit 即初始快照；首轮 prompt 只描述症状、不透露 bug 位置。（详见 skills/01-task-create.md「出题与埋点要求」）

### 产物

```text
records/solocc-0001/task-info.md
```

---

## 第 2 步：与模型交互（用户在 Windows 容器内的 Claude Code / 本机 Codex 中）

> Claude Code 跑在 Windows 的 Docker 容器（`benzhi-claude-code`，镜像 `nicehey/benzhi-claude-code:1.0`）里，**题号直接用仓库目录名（任务 ID）**，即容器内工作目录 `/workspace/<REPO>`。这样一题一个 `/workspace/<题号>`，轨迹落在容器内 `/home/node/.claude/projects/-workspace-<题号>/`。Codex CLI 仍在本机跑，轨迹在本机 `~/.codex/sessions/`。
>
> 与 Mac 版不同：Windows 镜像**没有 `cc` 快捷入口**，需要 `bash` 进入容器、手动 `claude` 启动；且普通 `claude` 未跳过权限确认，执行命令/改文件前会询问。
>
> 若复用的是别人已建好的容器、名称不是 `benzhi-claude-code`（如 `benzhi-claude-code-test-20260907`），请把下面所有命令里的 `benzhi-claude-code` 换成实际容器名（`docker ps -a` 可查）。

### 前置：确保容器可用（首次启动 + 三个踩坑）

首次启动容器（之后复用只需 `docker start benzhi-claude-code`）：

```powershell
docker run -d --name benzhi-claude-code -e "apikey=你的Key" nicehey/benzhi-claude-code:1.0
```

跑之前先看这三个最常踩的坑，出事按序处理：

- **PIPE 连不上引擎**：报错 `failed to connect to the docker API at npipe://… dockerDesktopLinuxEngine … The system cannot find the file specified`，说明 Docker Desktop 没启动或引擎未就绪。打开 Docker Desktop，等 `docker info` 能返回 `ServerVersion`，确认处于 **Linux 容器模式**，再执行 `docker run`。
- **直连 Docker Hub 拉镜像超时**：报错 `dialing registry-1.docker.io:443 … connection attempt failed`，是国内网络访问 Docker Hub 不通。或在 Docker Desktop 配 `registry-mirrors`，或改用加速地址拉取再打回标准标签，例如 `docker pull docker.1ms.run/nicehey/benzhi-claude-code:1.0` → `docker tag docker.1ms.run/nicehey/benzhi-claude-code:1.0 nicehey/benzhi-claude-code:1.0`。
- **进容器后 Claude 报 `403 key not allowed to access model`**（`can only access models=['…']. Tried to access ark/urm-01`）：镜像固化的模型名与 Key 实际可访问的模型不一致。重建容器时把所有模型环境变量覆盖成网关允许的模型名（`-e ANTHROPIC_MODEL=…` 连同 `-e ANTHROPIC_DEFAULT_OPUS/SONNET/HAIKU_MODEL=…`、`-e CLAUDE_CODE_SUBAGENT_MODEL=…`）。

详细排障见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)「常见问题」。

1. **把仓库放进容器**（首次做该题，把本机 `repos/<repo>` 复制进容器对应题号目录；在 PowerShell 中执行）：
   ```powershell
   docker exec benzhi-claude-code mkdir -p /workspace/<REPO>
   docker cp <本机 repos\<REPO> 路径>/. benzhi-claude-code:/workspace/<REPO>/
   docker exec -u root benzhi-claude-code chown -R node:node /workspace/<REPO>
   ```
   第二条末尾的 `/.` 表示复制目录**内容**（否则 `docker cp` 会把仓库目录本身作为子目录嵌套进去，如 `/workspace/<REPO>/<REPO>/`）。第三条 `chown` 是把 `docker cp` 进来的文件归属改为容器内用户 `node`，否则 Claude 只能读、不能改（改文件时报 `Permission denied`）。建议连着执行；若忘了，出现「无权修改文件」警告或 `Permission denied` 时补执行这一条即可。
2. **进入容器并启动 Claude**：
   ```powershell
   docker exec -it -w /workspace/<REPO> benzhi-claude-code bash
   ```
   看到提示符类似 `node@…:/workspace/<REPO>$` 后，在容器内输入：
   ```bash
   claude
   ```
   首次进入可能询问界面主题、显示安全提示、或询问是否信任当前目录（选择信任，路径应与 `/workspace/<REPO>` 一致）。
3. **做本轮对话**（默认推荐：一个 Claude 会话里连续发多轮，不退出）：
   - 第 1 轮：粘贴首轮提示词（见第 1 步产物 / `task-info.md` 的「首轮提示词」），开始对话。
   - 继续下一轮：直接在**同一个** Claude 会话里再发一条消息（如「继续」「再改成…」），SessionID 不变，轮次随之递增。
   - ⚠️ Windows 镜像未启用 `--dangerously-skip-permissions`，Claude 每次执行命令、创建/修改文件前都会询问，**确认操作内容后选择「允许」**。
4. **把容器里的轨迹导出到本机**（推荐：另开一个 PowerShell 窗口执行，**无需退出 Claude**；题号=仓库名，故容器内目录为 `-workspace-<REPO>`，导出到任务记录目录）：
   ```powershell
   docker cp benzhi-claude-code:/home/node/.claude/projects/-workspace-<REPO>/. <本机 records\<REPO> 路径>
   ```
   - `docker cp` 读的是容器文件系统，与正在进行的会话互不干扰：Claude 窗口照常开着、不用 `/exit`。
   - ⚠️ 导出时机：等 Claude 把当前这轮答完、处于等待你输入的静止状态再拷（别在它正跑工具、消息还没落盘时拷，否则最新几条可能不完整）。
   - 导出后 agent 从 `records/{REPO}/{REPO}-trajectory.jsonl` 解析 SessionID / TurnID（`sessionId` 字段=SessionID，一条 user 键入=一轮、其 `promptId`=TurnID），无需用户手动回填。仅当解析失败时，再把 **SessionID / TurnID(promptId) / 轨迹位置 / 模型回答** 带回给 agent。
   - 请保留整个文件夹结构，不要只挑一个 JSONL：目录里可能还有同名会话文件夹（子代理记录、工具输出），交付/上传需要它们。若提示「找不到目录」，先确认已在对应工作目录启动过 Claude、发过消息（轨迹才会生成），再用 `docker exec benzhi-claude-code ls -1 /home/node/.claude/projects` 核对实际轨迹目录名。
5. **（可选）退出会话 + 下次怎么接着做**：如果确实想退出 Claude：
   - 退出两次：Claude 对话框输入 `/exit` 回车 → 回到 `node@…:/workspace/<REPO>$` 容器提示符；再输入 `exit` 回车 → 回到以 `PS` 开头、含 Windows 路径的 PowerShell。
   - **下次继续下一轮**：进容器后**不要用裸 `claude`**（会新建一个 SessionID，打破「一个任务 = 一个会话窗口」），改用 `claude --continue`（恢复当前目录最近一次会话，同一 SessionID）或 `claude --resume <SessionID>`。详见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)「如何恢复历史会话」。

> 💡 一句话：**一个任务的几轮对话必须落在同一个 SessionID（一个会话窗口）里。** 默认就**别退出**，一个 `claude` 会话连发多轮；导出轨迹**另开窗口**跑 `docker cp`，不用 `/exit`。要退出就记住用 `claude --continue` 恢复。

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

1. 读取本任务已导出到本机的轨迹（`records/{REPO}/{REPO}-trajectory.jsonl`；Claude Code 来自容器导出），定位本任务会话并拆出第 N 轮（一轮=一次 user 键入），取其 User Prompt 原文与 promptId
2. 创建 `records/solocc-0001/solocc-0001-R01.md`，回填 User Prompt、任务类型/难度、语言/框架、TurnID
3. 从 `task-info.md` 继承 SessionID 等共享字段（导出时合并），并按 Harness 分行回填轨迹根目录
4. 校验：轮次 ≤ 10；TurnID 在任务内唯一；SessionID 与任务一致

### 产物

```text
records/solocc-0001/solocc-0001-R01.md
```

### 关于后续轮次（R02 起）

- 第一轮不满意想接着跑：用户直接在 Claude Code 里发下一条消息（如「继续」或新的改动需求）。agent 从**同一个会话轨迹**里按「第几个 user 键入」定位这一轮，把那条消息原文作为 `records/solocc-0001/solocc-0001-R0N.md` 的 User Prompt 写入，`round N` 即可自动生成 `R0N.md`（N ≤ 10）。
- 同一任务各轮**共用同一个轨迹文件**（一个 SessionID = 一个 `.jsonl`，随轮次增长）；但**每轮一个独立 promptId**——SessionID 各轮相同、TurnID/PromptID 各轮互不相同（导出处校验 TurnID 唯一）。

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
5. **上传轨迹附件（可选）**：投递脚本（`append_delivery_feishu.py`）会把「轨迹文件」列留空，因为该字段是**附件**类型（`type=17`），不能写文本路径。若要把轨迹作为附件挂到记录上，需在投递后额外执行两步：
   - `POST /open-apis/drive/v1/medias/upload_all`（multipart 表单字段：`file_type`、`file_name`、`parent_type=bitable_file`、`parent_node=app_token`、`size`、`file`）拿到 `data.file_token`；
   - `PUT /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}`，body 写 `{"fields":{"轨迹文件":[{"file_token":"…","name":"…","size":…,"type":"file"}]}}`。
   token 用 `POST /open-apis/auth/v3/tenant_access_token/internal` 换取。完整步骤见 [../skills/04-export-submit.md](../skills/04-export-submit.md)。

> 目标表见 `config.toml [feishu]`（`Lg0mbjRpPaxjhmsj27MckrJLnec` / `tble0z2KnzCfjJmZ`）。
> 凭证默认复用 `code-eval-gsb/secrets.toml [feishu]` 的 app_id/app_secret；命名差异（`feature迭代`、描述列空格等）由脚本自动映射。
> 轨迹字段类型为「附件」(`type=17`)，因此不能写文本路径，须先上传文件得到 file_token 再写入。

### 产物

满意度交付多维表格新增 N 条记录（N = 提交表行数），每条含五维分数与描述。

### 注意事项

- 当天 20:00 前执行的数据当天提交；20:00 后产生的数据次日 14:00 前提交。
- 多维表格是最终交付物：投递前确认提交表已定稿、无返修；追加错误在表内手动删除后重投。
- 首次使用需为应用开通 `bitable:app` 权限并把应用加为该表协作者。
