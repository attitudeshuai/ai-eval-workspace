# cc-solo 满意度标注 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，一步一步完成「Claude Code 用户满意度标注」的全流程。

配置统一读取 `projects/cc-solo/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 技术细节见 `skills/01-task-create.md` 等 skill 文件；评分表/原因写法速查见 `docs/annotate-guide.md`。

---

## 通用启动语

```text
cc-solo {项目} {操作}
```

- **generate 用「项目名 + 各类型配额」**：`cc-solo app-12 generate` + 各类型配额（如 `bugfix*5 / codegen*5 / feature*5 / understand*1 / refactor*1 / engineering*1 / test*1`）→ agent 建 N 份任务副本 + 提示词，并按类型复制进容器。
- **round / score 用「任务名」**（`{项目}-{类型}-{索引}`）：`cc-solo app-12-bugfix-01 round 1`、`cc-solo app-12-bugfix-01 score 1`。
- **export 用 `cc-solo export`**（TODO：最终交付格式未定）。

> 这里的 `cc-solo {项目} {操作}` 是**给 AI agent 的自然语言指令**（runbook 通用缩写），不是容器命令。Mac 容器**没有** `cc` 题号入口（新版隔离镜像已废弃题号与 `cc`），两者不要混淆。
>
> **你只发指令，不跑命令**：本手册里出现的 `python …` 与 `docker …` 命令**全部由 agent 在宿主机执行**，你只需要发上面这类自然语言指令（`generate` / `round N` / `score N` / `export` …），不必自己敲任何 Python 或 docker 命令。
>
> **容器模型（2026-09-10 起）**：**1 任务 = 1 会话 = 1 容器 = 1 本机工作目录**；容器名固定 `cc-solo-{任务}`（如 `cc-solo-app-12-bugfix-01`）；容器内工作目录恒为 `/workspace`（内容 = 本题任务副本）；轨迹恒在 `/home/node/.claude/projects/-workspace/`。
> 与旧版（常驻容器 + `cc <题号>` + `docker cp` 搬代码）的差异与原因见 [image-upgrade-review.md](image-upgrade-review.md)。

> 任务名 = **副本目录名 = 提示词名 = 容器名（前缀 `cc-solo-`）= `{项目}-{类型}-{索引}`**（如 `app-12-bugfix-01`，容器名 `cc-solo-app-12-bugfix-01`）。同一项目按 7 类任务复制成多份副本，**索引全局累加、两位补零**。类型 slug 对照：`0-1代码生成`→`codegen`、`Feature迭代`→`feature`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。
> 副本 = 素材源复制 + 改名；**共用同一个 base commit 快照**；**暂不建每份独立 git、不提交/push**。

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

## ⚠️ 使用前必读

- **一个任务 = 一个会话窗口（≤10 轮）；一轮 = 一条数据**。
- **AI 交付文本必须先经去 AI 化**：AI 起草的提示词/评分依据无论练习还是正式，落盘/投递前都须先经 `skills/humanizer-zh` 去 AI 化（练习阶段允许 AI 直接打分、无需人工确认；正式交付再人工复核），并严格按五维模式；人工撰写的原文保持原样。
- 被标注模型跑在 **Claude Code** 里，由用户在终端里操作，本 skill 不代跑。

## 人工 / agent 分工（一眼看清谁做什么）

| 环节 | 谁做 | 说明 |
|---|---|---|
| 建本题容器（`docker run -it`，一题一个） | **人工** | 前台交互、要占你自己的终端窗口；agent 给现成命令 |
| 播种初始代码（任务副本 → 容器 `/workspace`，启动后、首轮前） | **agent 自动** | 直接写挂载目录，不再往容器里 docker cp |
| 每轮导出轨迹到本机 records | **agent 自动** | `docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/."` |
| 容器里跟 Claude Code 交互（贴提示词、追加轮次） | **人工** | 唯一需要你操作的环节；**中途不要退出** |
| 切轮次、写 R0N、五维打分、导出 | **agent 自动** | 你只发指令（`round N`/`score N`） |
| 收尾（回导源码到任务副本 + 删容器） | **agent 自动** | 代码已在本机挂载目录，回导只为归档 |

> 一句话：你只在容器里跑 Claude Code；其余 docker cp、切片、录入、打分、导出全由 agent 在宿主机直接执行。

> **📌 交付约定：agent 每完成一步，都要在同一条回复里写出下一步。** 必须给全 **① 下一步要敲的命令原文**（可直接照抄，要替换的值标出来）、**② 怎么操作**（预期看到什么才算成功、常见报错长什么样、出错查哪一节）。不要只说一句「已完成」把下一步留到下一轮问答；多题批次还要讲清**哪几题、什么顺序、哪些能并行**。

## 前置准备

### 1. 配置本地环境

```bash
cp projects/cc-solo/secrets-simple.toml projects/cc-solo/secrets.toml
```

编辑 `secrets.toml`：

```toml
work_root = "sessions/cc-solo"
active_session = "session-0907"
annotator = "张三"
```

### 2. 准备候选仓库（工作区）

将被标注仓库（素材源）放到 `{work_root}/{SESSION_NAME}/source-code/{项目}/`，或使用本机已有路径，需已 `git init` 且有可 push 的远端。

> **⚠️ 仓库结构规范（create 第一步必检）**：素材源（项目根 = 唯一 git 仓库 = base commit 快照）固定在 `source-code/{项目}/`（如 `app-12`），其下再嵌套任务副本（`{项目}-{类型}/{项目}-{类型}-{索引}/`，全局索引累加）。若结构不规范：`create` 第一步先把实际结构 vs 规范差异列出来，**提示用户确认**，确认后整理成该格式再继续（未确认不移动文件）。

> **⚠️ 一个素材源 = 一个 base commit 快照（共用）**：同一素材源下的所有任务副本/提示词**共用一个 base commit 快照地址**，不必每任务新建仓库。来源仓库（如 `gsb0731-xxx`）是已使用/共享仓库时，不要直接向它提交；用 `github_username` + PAT 为**该素材源**新建（或复用）**一个** GitHub 仓库（命名建议 `cc-solo-{项目}`，如 `cc-solo-app-12`），把本地 origin 指到它，之后快照、模型交互、提交都基于这个仓库。
>
> 快照要求：仓库需 push 到评测团队可访问的远端（设为 **public** 公开仓库，或至少加协作者）；push 前确认 `.gitignore` 已覆盖 `.env`、密钥/连接串/token；已提交快照禁止 force-push / rebase。

---

## 第 1 步：生成任务副本 + 提示词（generate）

### 指令模板

```text
cc-solo app-12 generate
bugfix*5
codegen*5
feature*5
understand*1
refactor*1
engineering*1
test*1
```

> **generate 不用自己拼任务名**：agent 按「项目名 + 类型 + 全局索引」自动生成任务名（`app-12` + Bug修复 第 1 条 → `app-12-bugfix-01`），从素材源复制成多份副本（改目录名 + 按类型埋点）、起草提示词（`prompt-architect` + `humanizer-zh`）、按类型复制进容器。**注意**：generate 第一步会先校验仓库结构是否为 `source-code/{项目}/`（其下 `{项目}-{类型}/{项目}-{类型}-{索引}/`），不规范则提示确认后整理。

**类型 slug 对照**（任务名里用 slug）：`0-1代码生成`→`codegen`、`Feature迭代`→`feature`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。

### AI 会执行

0. **雷同题红线（第一步必检）**：对照 `docs/annotate-guide.md` §7「不被允许的雷同题」逐项核查素材源项目主题（经典小游戏与变种、塔防/2D 解谜/潜行/平台跳跃、粒子物理、喂食小动物、CLI 工具、CRUD/后台/电商/预约系统、报表看板、番茄钟/天气/记账等）。**命中即中止**，提示用户换素材，不得继续建副本/出题/打快照。
1. 校验仓库存在、工作区干净、`.gitignore` 无泄漏风险（`.env`/密钥/token 已覆盖）；**并校验仓库结构**：素材源是否位于 `source-code/{项目}/`（唯一 git 仓库），任务副本是否按类型分组 `{项目}-{类型}/{项目}-{类型}-{索引}/` 嵌套其下。结构不规范 → 先列「实际结构 vs 规范结构」差异 → **提示用户确认** → 确认后整理成该格式再继续（未确认不移动文件）。
2. **准备远端（一个素材源 = 一个 base commit 快照）**：用 `github_username` + PAT 为**该素材源**新建（或复用）**一个** GitHub 仓库（`cc-solo-{项目}`，如 `cc-solo-app-12`），把本地 origin 指向它；来源仓库仅作内容来源，不向其提交。
3. **打初始快照**：提交一个 baseline commit → push 到**该仓库** → 取**完整 40 位 SHA** 生成 permalink（`https://github.com/<owner>/cc-solo-{项目}/commit/<40sha>`）。**该素材源下所有任务副本共用这同一个快照地址。**
4. 创建 `records/app-12/app-12-codegen/task-info.md`：Repo URL、本地路径、初始环境快照、Harness、Harness版本、操作系统、环境可复现等级（共享字段）；记录目录名 = 任务 ID。轨迹根目录留待首轮 SessionID 回填后按 Harness 定位（Claude Code→本次导出到本机的 `records/{任务}/{任务}-trajectory.jsonl`，其容器内来源为 `/home/node/.claude/projects/-workspace/`）。**建议同时记录镜像 tag + manifest digest 与隔离模式**（见 [image-upgrade-review.md](image-upgrade-review.md)），否则不同批次的数据无法追溯到底跑的是哪个镜像。
5. 起草**首轮提示词**（真实用户口径、自然语言）：可引用 `prompt-architect` 起草；练习阶段经人工确认后写盘即可，正式交付时再先经 `humanizer-zh` 去 AI 化。
6. **生成本题容器启动命令**（agent 给出、人工执行）：镜像固定 `adminfather/benzhi-claude-code:20260909-isolated-git`（**勿用 `latest`**）、`--name "cc-solo-{任务}"`、新建空的 `$RUN_DIR/workspace` 并挂到 `/workspace`、`-e "apikey=…"`。**镜像强制挂载目录启动时必须为空**（错误信息即 `Import code during this session.`），所以**不能先播种再启动**，播种放到容器起来之后。
7. **播种任务副本**（agent 执行，容器启动后、人工发首轮提问**之前**）：按 `.gitignore` 排除依赖包（node_modules/.venv/__pycache__/dist 等，体积大），把任务副本内容写进挂载目录——`SRC=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}' "cc-solo-{任务}")`，再 `rsync -a --exclude-from=.gitignore "{REPO_BASE_PATH}/{项目}/{项目}-{类型}/{项目}-{类型}-{索引}/" "$SRC/"`（无 rsync 时用 `git ls-files -z | tar -c --null -T -` 打包再解包）。**⚠️ 不要在 Mac 上写 `chown`**：镜像以 `--cap-drop ALL` 运行，chown 会失败，而挂载目录的归属已自动映射。播种完成后明确回报「播种完成，可以贴首轮提示词」。
8. 输出：任务信息文件路径 + 首轮提示词 + 容器启动命令，提示人工按「启动容器 → 等 agent 报播种完成 → 贴首轮提示词」的顺序操作。

> ⚠️ **出题要难**：首轮提示词做高难度、多需求、跨模块/多约束题，严禁简单题。**Bug修复先埋点**：在初始化/打快照阶段把 bug 写进源码（无注释标记、藏得深、可复现），埋点 commit 即初始快照；首轮 prompt 只描述症状、不透露 bug 位置。（详见 skills/01-task-create.md「出题与埋点要求」）

### 产物

```text
records/app-12/app-12-codegen/task-info.md
```

---

## 第 2 步：与模型交互（用户在容器内的 Claude Code 中）

> Claude Code 跑在 docker 容器（容器名 `cc-solo-{任务}`）里，**1 容器 = 1 任务 = 1 会话**。容器内工作目录恒为 `/workspace`（内容 = 本题任务副本，由 agent 在容器启动后播种）；轨迹落在容器内 `/home/node/.claude/projects/-workspace/`。
>
> 镜像固定 `adminfather/benzhi-claude-code:20260909-isolated-git`（**勿用 `latest`**）。容器启动/拉镜像/模型出错（`command not found: docker`、拉镜像超时、`model not found` / `403 key not allowed to access model`）按 [CLAUDE_CODE_DOCKER_MAC.md](CLAUDE_CODE_DOCKER_MAC.md) 的「隔离范围与排错」处理。
>
> **审批口径（两平台统一免确认）**：本镜像的 Claude Code 启动参数**已内置 `--dangerously-skip-permissions`**（免确认，自动执行命令/改文件），上面的 `docker run` **不需要也不应再手写这个 flag**，进去就是免确认模式。Windows 侧同为免确认，但要在进入命令里显式带上 `--dangerously-skip-permissions`（见 [runbook-windows.md](runbook-windows.md) 第 2 步），两侧口径一致。实际审批模式须记进 `task-info.md`。

1. **启动本题容器**（人工，前台执行；agent 会给现成命令）：
   ```bash
   TASK="app-12-bugfix-01"
   RUN_DIR="$HOME/claude-runs/${TASK}-$(date +%Y%m%d-%H%M%S)"
   mkdir -p "$RUN_DIR/workspace"
   docker run -it --init --restart=no --name "cc-solo-$TASK" \
     --cap-drop ALL --security-opt no-new-privileges \
     --mount "type=bind,src=$RUN_DIR/workspace,dst=/workspace" \
     -e "apikey=xxxxx" \
     adminfather/benzhi-claude-code:20260909-isolated-git
   ```
   看到 Claude 输入框后**先不要发消息**，等 agent 报「播种完成」再开始。

   > **能不能像 Windows 那样用 `for` 循环一次起好几题？不能照搬**，原因有三：① 隔离镜像要求**挂载目录在启动时必须为空**，每题都要先建一个空目录再起容器（不能先把副本塞进去）；② 代码要在容器起来**之后**由 agent 播种，起容器和播种是两个阶段，批量起完必须逐题确认播种完成；③ 这个镜像**不支持恢复会话**（`--continue` / `docker start` 会被拒），一个容器只有一次交互机会，批量起容器时窗口搞混或误按 Ctrl+C 就是整题报废。所以 Mac 侧沿用「一题一个终端、一题一次前台启动」的逐个流程（Windows 侧挂载即可用、可后台常驻，才适合循环批量起，见 [runbook-windows.md](runbook-windows.md) 第 2 步）。
   > 若确需少占窗口，可先拿**一题**试 `docker run -dit …` 起后台 + `docker attach "cc-solo-$TASK"`（`Ctrl-P Ctrl-Q` 脱离不杀会话）：`-dit` 下 Claude 正常运行**已实测**，但**「循环批量起 + 逐个 attach」在 Mac 上尚未实测**，正式批次前先用一题验证，别直接套到整批。
2. **做本轮对话**（默认推荐：同一个会话里连续发多轮，**中途不要退出**）：
   - 第 1 轮：粘贴首轮提示词（见第 1 步产物 / `task-info.md` 的「首轮提示词」），开始对话。
   - 继续下一轮：直接在**同一个**会话里再发一条消息（如「继续」「再改成…」），SessionID 不变，轮次随之递增。
3. **红线：这个镜像不支持恢复会话**。`--continue` / `--resume` 不可用，`docker start` / `docker restart` 会被镜像直接拒绝（`This container has already been used. Export results and create a new container.`）。误退出（Ctrl+D ×2、Ctrl+C、关窗）即本题无法继续：只能按**已导出的轮次**收尾（数据不丢），剩余轮次作废。
   - 降低误关窗风险的可选做法：用 `docker run -dit` 起容器、再 `docker attach "cc-solo-$TASK"`，用 `Ctrl-P Ctrl-Q` 脱离而不杀会话（`-dit` 下 Claude 正常运行**已实测**，见 [image-upgrade-review.md](image-upgrade-review.md) 第七节）。
4. **退出方式**：本题做完后，在输入框按 **Ctrl+D 两次**回到终端（此模式**禁用斜杠命令**，没有 `/exit`）。退出后容器停止、轨迹仍在容器里；**不要加 `--rm`，导出完成前不要 `docker rm`**。

> 💡 一句话：**一个任务的几轮对话必须落在同一个 SessionID，而且只有一次机会。** 默认就**别退出**，一个 `cc-solo-{任务}` 会话连发多轮。做完一轮后直接告诉 agent `cc-solo {任务} round N` 即可——导出轨迹、切片、录入都由 agent 执行 docker 命令完成；代码本来就在本机挂载目录里，你不用手动 `docker cp`。

---

## 第 3 步：单轮录入（每轮一条数据）

### 指令模板

```text
cc-solo app-12-bugfix-01 round 1
```

> 只写这一行即可：SessionID / User Prompt / TurnID 由 agent 从本机轨迹自取；任务类型（按本轮主要意图）、任务难度、语言/框架由 agent 从轨迹 + 仓库自动推断，有疑问才回问确认。

### AI 会执行

1. **导出本轮轨迹（agent 执行 docker 命令）**：等模型答完静止后 —— `docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/." {RECORD_DIR}/{项目}/{项目}-{类型}/{任务}/`（容器停止状态下也能导出）。**代码产物不需要回导**：容器 `/workspace` 就是本机挂载目录，模型改完的代码已经在盘上；任务收尾时再由 agent 按 `.gitignore` 排除依赖包（node_modules/.venv/__pycache__ 等），把源码回导到任务副本 `{REPO_BASE_PATH}/{项目}/{项目}-{类型}/{任务}/`，供 `03-score-annotate` 做 git diff 对照。
2. 从轨迹切出第 N 轮（一轮=一次 user 键入），取其 User Prompt 原文与 promptId；本轮那段存 `records/<repo>/<题号>/<题号>-R0N-trajectory.jsonl`（**仅用于打分阶段定位单轮**），完整轨迹保留为 `records/<repo>/<题号>/<题号>-trajectory.jsonl`（**提交时的轨迹附件**，随轮次追加，会话结束才是最终版）。
3. 创建 `records/<repo>/<题号>/<题号>-R0N.md`，回填 User Prompt、任务类型/难度、语言/框架、TurnID。
4. 从 `task-info.md` 继承 SessionID 等共享字段（导出时合并），并按 Harness 分行回填轨迹根目录。
5. 校验：轮次 ≤ 10；TurnID 在任务内唯一；SessionID 与任务一致。

### 产物

```text
records/app-12/app-12-codegen/app-12-codegen-R01.md
```

### 关于后续轮次（R02 起）

- 第一轮不满意想接着跑：agent 已生成下一轮提示词（`-R02-prompt.md`，开头「修复bug：」），用户确认后贴进 Claude Code 会话。agent 从**同一个会话轨迹**里按「第几个 user 键入」定位这一轮，把那条消息原文作为 `records/app-12/app-12-codegen/app-12-codegen-R0N.md` 的 User Prompt 写入，`round N` 即可自动生成 `R0N.md`（N ≤ 10）。
- 同一任务各轮**共用同一个轨迹文件**（一个 SessionID = 一个 `.jsonl`，随轮次增长）；但**每轮一个独立 promptId**——SessionID 各轮相同、TurnID/PromptID 各轮互不相同（导出处校验 TurnID 唯一）。

---

## 第 4 步：五维打分（依据：人工撰写，或 AI 起草 → 去 AI 化 → 人工复核）

### 指令模板

```text
cc-solo app-12-bugfix-01 score 1
```

### AI 会执行

1. 打开 `records/app-12/app-12-bugfix/app-12-bugfix-01.md`，确认该轮已录入（有 User Prompt / TurnID）
2. **录入方式二选一**（先与用户确认）：
   - 人工打分：逐字段索要 **五维分数（1-5）+ 五条依据描述 + 其他问题** → 原样录入、不改写
   - AI 代打（练习阶段默认）：**读轨迹文件 → 调 `skills/implementation-reviewer` 做代码产物评价 + 过程分析 → 合成五维分数与依据** → **先经 `skills/humanizer-zh` 去 AI 化** → 严格按五维模式落盘（练习阶段无需人工确认；正式交付再人工核对）。⚠️ 读轨迹 + 调 implementation-reviewer 是红线，缺一即拒收（详见 skills/03-score-annotate.md「分析调用链路」）
3. 机械校验：五个分数为 1-5 整数；五条描述均非空；分数与描述方向一致性提示（请人工复核）
4. 判定是否继续：产物不满意（代码漏洞 / 功能未实现 / 实现不合理）→ agent 拆分不满点、生成下一轮提示词（开头「修复bug：」、**只描述现象不写改法、不分条列举**、涉及 ≥2 文件）并写 `-R{NN+1}-prompt.md`；满意则结束，仅过程不满意不生成下一轮提示词。第 10 轮后强制结束本任务

### 产物

```text
records/app-12/app-12-codegen/app-12-codegen-R01.md   # 已填入五维打分与依据
```

---

## 第 5 步：会话结束，开新任务

- 达到 10 轮，或模型达成目标且无需继续时，本任务结束
- **收尾三步（agent 执行）**：
  1. 导出完整轨迹并核对：`docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/." "$RUN_DIR/traces"`，与该任务已录入的各轮切片比对，确认不缺轮；
  2. 回导源码到任务副本（按 `.gitignore` 排除依赖包），确认本机副本 = 模型最终产物；
  3. `docker rm "cc-solo-{任务}"`（**确认轨迹已导出后再删**），并清理运行目录里的依赖包。可用 `docker ps -a --filter name=cc-solo-` 盘点是否还有未清理的本期容器。
- 新开任务：重复第 1-4 步，使用**新的任务副本目录 + 新的空运行目录 + 新容器**（容器名换新任务名，不能复用旧容器）：同一项目继续另一种类型用 `app-12-feat`（在生成产物上迭代）/ `app-12-bugfix`（埋点后修复）等新任务 ID；全新项目则用新仓库名（如 `app-13-codegen`）
- ⚠️ 若会话中途意外退出（无法恢复）：剩余轮次作废，按已导出的轮次收尾，并在 `task-info.md` 备注「会话提前终止（第 N 轮后）」

---

## 第 6 步：生成评价结果文件

> 2026-09-10 起不再导出「正式提交表 CSV」、也不再投递飞书，改为按平台提交表单的字段规范生成**评价结果文件**（一轮 = 一条），后续通过提交接口提交。

### 指令模板

```text
cc-solo export
```

### AI 会执行

1. **先请求平台表单定义接口**（`GET .../submissions/form-schema`），与本地 `docs/submission/fields.json` 比对 fingerprint 与字段集合，防止平台表单改了本地还按旧规范生成；不一致就重跑抽取再继续。
2. 如需更新规范：`python scripts/cc-solo/extract_submit_fields.py`（**默认拉平台实时接口**，`--source js` 用本地快照）→ 写 `docs/submission/fields.json`
3. 扫描 `{RECORD_DIR}` 全部任务，按 `task-info.md` + 各 `{任务}-R{NN}.md` 合成**24 个提交字段**（任务类型/难度/语言框架、Harness 及版本、操作系统、可复现等级、初始环境快照、User Prompt、SessionID、TurnID、轨迹文件、五维分数与描述、其他问题、轮次排序）
4. 运行质检（表单规范层 + 项目规则层 + 去 AI 化层），逐条给出 error / warn
5. 输出：`deliverables/cc-solo/{SESSION_NAME}/评价结果-{SESSION_NAME}-{date}.json`（主产物）+ `-质检报告.md`（**不再产出人工核对 CSV**，2026-09-12 起取消）

> ⚠️ **多轮任务的轨迹附件口径（导出前必读）**：同一任务（同一 SessionID）的各轮记录，`轨迹文件` 都指向**同一份最终完整轨迹** `{任务}-trajectory.jsonl`（含该会话全部轮次），各轮靠 `SessionID` + `TurnID` 定位。
> 所以**导出与提交必须在任务会话结束之后执行**——会话还没结束就导出，整份轨迹只含到当时为止的轮次，后面几轮的记录会挂着一份不完整的轨迹。每轮的 `{任务}-R{NN}-trajectory.jsonl` 切片只是打分阶段定位单轮用的中间产物，**不作提交附件**。

```bash
# 由 agent 执行，你只发上面的 cc-solo export 指令即可
python scripts/cc-solo/build_eval_result.py
```

### 产物

```text
deliverables/cc-solo/session-0909/评价结果-session-0909-<date>.json
deliverables/cc-solo/session-0909/评价结果-session-0909-<date>-质检报告.md
```

> 常见阻塞项（error，必须修数据后重新生成）：`初始环境快照` 不是 GitHub 40 位 SHA permalink；首轮难度写成「简单」；轨迹文件不存在；五维分数不是 1-5 整数。修的是 `records/` 里的数据文件，不要手改产物。

---

## 第 7 步：提交（提交接口）—— ⛔ 本阶段先不提交

> **提交接口已就位**：`POST https://solo2.jzxhnh.com/api/v1/submissions`，已写在 `config.toml [submission].submit_url`（`secrets.toml [submission].submit_url` 若填写则优先），`docs/submission/fields.json` 的 `submit_api.url` 也已同步。
>
> 但**本阶段先不提交数据**（用户决定）：只做到第 6 步——生成评价结果 + 质检，**不上传轨迹附件、不调提交接口**。需要提交时用户说一声，由 agent 执行本节。
>
> 凭据在 `secrets.toml [submission]`（`cookie` + `username` / `password`）；cookie 约 2 天过期，**脚本会自动登录刷新并回写**，无需手工复制。登录结果缓存在 `projects/cc-solo/.solo_session.json`（gitignore），**没过期就不会重复登录**（`--status` 查看）。

### 指令模板（本阶段先不执行）

```text
cc-solo export submit
```

### AI 会执行

1. 确认评价结果文件已生成、质检无未处理的 error
2. **先 dry-run**（不发任何请求，只打印将上传的轨迹与将提交的字段）：
   `python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json`
3. 先只上传轨迹、验证 cookie 与附件链路：`… --upload-only --commit --write-back`（会把远端 path 回写进结果文件）
4. 正式提交：`… --commit`（或加 `--url <提交接口>`；`--only-ready` 可跳过仍有 error 的条目）
5. 输出每条的上传结果与接口返回；失败的条目修正后重试，避免重复提交

### 产物

提交接口按「一轮 = 一条记录」落库，每条含 24 个字段 + 轨迹附件。

### 注意事项

- 轨迹是**附件**字段：必须先用上传接口拿远端 path，再写进 `trace_file` 提交（脚本自动处理）。
- cookie 会过期（约 2 天）：脚本优先复用会话缓存，缺失/过期或遇到 401、403 时才自动登录刷新（也可 `--login-only --commit` 主动续期、`--status` 查看剩余有效期）。
- 时限沿用约定：当天 20:00 前产生的数据当天提交，20:00 之后的次日 14:00 前提交。
- 旧的飞书投递（`append_delivery_feishu.py`）与 CSV 提交表（`export_submit.py`）**已退役**，仅作历史留存。
