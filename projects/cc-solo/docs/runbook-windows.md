# cc-solo 满意度标注 Runbook（Windows）

本 Runbook 是 [runbook.md](runbook.md) 的 Windows 版。流程、指令模板、产物与 Mac 版完全一致，**只有「第 2 步：与模型交互」里操作 Claude Code 的终端命令按 Windows 版 Docker 用法改写**。Windows 版 Docker 的完整使用说明见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)；**从安装 Docker 到导出轨迹**的完整操作见 [WINDOWS_DOCKER_SETUP.md](WINDOWS_DOCKER_SETUP.md)。

配置统一读取 `projects/cc-solo/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 技术细节见 `skills/01-task-create.md` 等 skill 文件；评分表/原因写法速查见 `docs/annotate-guide.md`。

## 与 Mac 版的关键差异（速览）

| 环节 | Mac 版 | Windows 版（本文档） |
|---|---|---|
| 镜像 | `adminfather/benzhi-claude-code:20260909-isolated-git`（固定 tag，勿用 latest） | `nicehey/benzhi-claude-code:1.0`（Windows 侧无新镜像，仅此一个 tag） |
| 启动方式 | `docker run -it`（前台直接进 Claude，启动后 agent 再播种） | `docker run -d`（后台常驻）+ 挂载本机任务副本目录为 `/workspace` |
| 批量建容器 | **逐题**前台启动（镜像要求空目录 + 启动后播种，循环批量**不可照搬**，见 [runbook.md](runbook.md) 第 2 步） | **`foreach` 循环一次起多题（已实测）**，见第 2 步「单题 vs 多题」 |
| 容器入口 | 启动即进入 Claude | `docker exec -it -w /workspace "cc-solo-{任务}" claude --dangerously-skip-permissions` |
| 命令审批 | 镜像**内置** `--dangerously-skip-permissions`，Claude 自动执行命令（无需人工确认） | **统一免确认**：启动命令里显式带 `--dangerously-skip-permissions`，与 Mac 口径一致，见第 2 步第 1 条 |
| 退出方式 | Ctrl+D 两次（无 `/exit`） | `/exit` 一次，容器保留 |
| 工作目录 | `/workspace` | `/workspace` |
| 轨迹目录 | `/home/node/.claude/projects/-workspace/` | 相同 |
| 会话恢复 | 不可恢复（一次性容器，哨兵拒绝 `--continue`） | 同题可 `claude --continue` / `--resume` |

> 除第 2 步的终端命令外，其余各步（建任务/出题/单轮录入/五维打分/生成评价结果/提交/返修）与 Mac 版完全一致。第 3~8 步照抄 Mac 版即可；本文各步里凡涉及路径与命令的地方按 Windows 写法（反斜杠、PowerShell）。

---

## 通用启动语

```text
cc-solo {项目} {操作}
```

- **generate 用「项目名 + 各类型配额」**：`cc-solo app-12 generate` + 各类型配额（如 `bugfix*5 / codegen*5 / feature*5 / understand*1 / refactor*1 / engineering*1 / test*1`）→ agent 建 N 份任务副本 + 提示词（Windows 下这些副本目录直接作为挂载源，无需复制进容器）。
- **round / score 用「任务名」**（`{项目}-{类型}-{索引}`）：`cc-solo app-12-bugfix-01 round 1`、`cc-solo app-12-bugfix-01 score 1`。
- **export 用 `cc-solo export`**（TODO：最终交付格式未定）。

> 这里的 `cc-solo {项目} {操作}` 是**给 AI agent 的自然语言指令**（runbook 通用缩写），不是容器命令。Windows 容器里**没有** `cc` 快捷入口——进入容器后是手动敲 `claude`。两者不要混淆。
>
> **你只发指令，不跑命令**：本手册里出现的 `python …` 与 `docker …` 命令**全部由 agent 在宿主机执行**，你只需要发上面这类自然语言指令（`generate` / `round N` / `score N` / `export` …）。唯一需要你自己敲的是进容器跟 Claude 对话那两条 docker 命令。

> 任务名 = **副本目录名 = 提示词名 = `{项目}-{类型}-{索引}`**（如 `app-12-bugfix-01`）。**1 任务 = 1 容器**：容器名统一 `cc-solo-{任务}`（如 `cc-solo-app-12-bugfix-01`），容器内工作目录恒为 `/workspace`，题目身份由「容器名 + 挂载目录」承载。同一项目按 7 类任务复制成多份副本，**索引全局累加、两位补零**。类型 slug 对照：`0-1代码生成`→`codegen`、`Feature迭代`→`feature`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。
> 副本 = 素材源复制 + 改名；**共用同一个 base commit 快照**；**暂不建每份独立 git、不提交/push**。

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

## ⚠️ 使用前必读

- **一个任务 = 一个会话窗口（≤10 轮）= 一个容器 = 一个本机工作目录；一轮 = 一条数据**。
- **AI 交付文本必须先经去 AI 化**：AI 起草的提示词/评分依据无论练习还是正式，落盘/投递前都须先经 `skills/humanizer-zh` 去 AI 化（练习阶段允许 AI 直接打分、无需人工确认；正式交付再人工复核），并严格按五维模式；人工撰写的原文保持原样。
- **提示词不得有空行（红线）**：首轮提示词与 `{任务}-R{NN}-prompt.md` 全文都不得出现空行，一段一段分行写、段间只用单个换行。空行粘进容器输入框会被当成回车提前提交，题会被截成两半（Windows 侧虽然能用 `claude --continue` 接着跑，但会白多出一轮）；提交表里的 `User Prompt` 也会原样带上这串空行。落盘前跑 `python scripts/cc-solo/lint_round_prompt.py --project {项目}`（含空行记 error）；此前已发出的提示词不追改。
- 被标注模型跑在 **Claude Code** 里，由用户在终端里操作，本 skill 不代跑。
- Windows 下 Claude Code 跑在 Docker 容器里，**终端命令用 PowerShell 执行**。

## 人工 / agent 分工（一眼看清谁做什么）

| 环节 | 谁做 | 说明 |
|---|---|---|
| 本地 → 容器（挂载任务副本为 `/workspace`，无需 docker cp/chown） | **agent 自动** | Windows 直接挂载，Mac 由 agent 启动后播种 |
| 容器 → 本地（导出轨迹；代码产物已在挂载目录，无需回导） | **agent 自动** | 依赖包按 `.gitignore` 排除/清理 |
| 容器里跟 Claude Code 交互（贴提示词、追加轮次） | **人工** | 唯一需要你操作的环节 |
| 收尾（导出完整轨迹核对 + 按 .gitignore 清理依赖 + 删容器） | **agent 自动** | Windows 直接挂载，源码不用回导，只清理依赖 |
| 切轮次、写 R0N、五维打分、导出 | **agent 自动** | 你只发指令（`round N`/`score N`） |

> 一句话：你只在容器里跑 Claude Code；其余建副本、挂载、导出轨迹、切片、录入、打分、导出全由 agent 在宿主机直接执行。

> **📌 交付约定：agent 每完成一步，都要在同一条回复里写出下一步。** 必须给全 **① 下一步要敲的命令原文**（可直接照抄，要替换的值标出来）、**② 怎么操作**（预期看到什么才算成功、常见报错长什么样、出错查哪一节）。不要只说一句「已完成」把下一步留到下一轮问答；多题批次还要讲清**哪几题、什么顺序、哪些能并行**。

## 前置准备

### 1. 配置本地环境

```powershell
Copy-Item projects/cc-solo/secrets-simple.toml projects/cc-solo/secrets.toml
```

编辑 `secrets.toml`：

```toml
work_root = "sessions/cc-solo"
active_session = "session-0907"
annotator = "张三"
```

### 2. 准备候选仓库（工作区）

将被标注仓库（素材源）放到 `{work_root}/{SESSION_NAME}/source-code/{项目}/`（Windows 下形如 `sessions\cc-solo\session-0907\source-code\app-12`），或使用本机已有路径，需已 `git init` 且有可 push 的远端。

> **⚠️ generate 第一步必检两件事**：
> ① **雷同题红线**——素材源项目若落在 `docs/annotate-guide.md` §7「不被允许的雷同题」清单（经典小游戏与变种、塔防/2D 解谜/潜行/平台跳跃、粒子物理、喂食小动物、CLI 工具、CRUD/后台/电商/预约系统、报表看板、番茄钟/天气/记账等），**命中即中止**、提示换素材，不得建副本/出题/打快照；
> ② **仓库结构规范**——素材源（项目根 = 唯一 git 仓库 = base commit 快照）固定在 `source-code/{项目}/`（如 `app-12`），其下再嵌套任务副本（`{项目}-{类型}/{项目}-{类型}-{索引}/`，全局索引累加）。结构不规范 → 先列「实际结构 vs 规范结构」差异，**提示用户确认**，确认后整理成该格式再继续（未确认不移动文件）。
>
> 快照要求：**一个素材源 = 一个 base commit 快照，所有任务副本共用同一个地址**（不必每任务新建仓库）；仓库需 push 到评测团队可访问的远端（设为 **public** 公开仓库，或至少加协作者）；push 前确认 `.gitignore` 已覆盖 `.env`、密钥/连接串/token；已提交快照禁止 force-push / rebase。

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

> **generate 不用自己拼任务名**：agent 按「项目名 + 类型 + 全局索引」自动生成任务名（`app-12` + Bug修复 第 1 条 → `app-12-bugfix-01`），从素材源复制成多份副本（改目录名 + 按类型埋点）、起草提示词（`prompt-architect` + `humanizer-zh`）。**注意**：generate 第一步会先校验仓库结构是否为 `source-code/{项目}/`（其下 `{项目}-{类型}/{项目}-{类型}-{索引}/`），不规范则提示确认后整理。

**类型 slug 对照**（任务名里用 slug）：`0-1代码生成`→`codegen`、`Feature迭代`→`feature`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。

### AI 会执行

0. **雷同题红线（第一步必检）**：对照 `docs/annotate-guide.md` §7「不被允许的雷同题」逐项核查素材源项目主题（经典小游戏与变种、塔防/2D 解谜/潜行/平台跳跃、粒子物理、喂食小动物、CLI 工具、CRUD/后台/电商/预约系统、报表看板、番茄钟/天气/记账等）。**命中即中止**，提示用户换素材，不得继续建副本/出题/打快照。
1. 校验仓库存在、工作区干净、`.gitignore` 无泄漏风险（`.env`/密钥/token 已覆盖）；**并校验仓库结构**：素材源是否位于 `source-code/{项目}/`（唯一 git 仓库），任务副本是否按类型分组 `{项目}-{类型}/{项目}-{类型}-{索引}/` 嵌套其下。结构不规范 → 先列「实际结构 vs 规范结构」差异 → **提示用户确认** → 确认后整理成该格式再继续（未确认不移动文件）。
2. **准备远端（一个素材源 = 一个 base commit 快照）**：用 `github_username` + PAT 为**该素材源**新建（或复用）**一个** GitHub 仓库（`cc-solo-{项目}`，如 `cc-solo-app-12`），把本地 origin 指向它；来源仓库仅作内容来源，不向其提交。
3. **打初始快照**：提交一个 baseline commit → push 到**该仓库** → 取**完整 40 位 SHA** 生成 permalink（`https://github.com/<owner>/cc-solo-{项目}/commit/<40sha>`）。**该素材源下所有任务副本共用这同一个快照地址。**
4. 创建 `records/app-12/app-12-codegen/task-info.md`：Repo URL、本地路径、初始环境快照、Harness、Harness版本、操作系统、环境可复现等级（共享字段）；记录目录名 = 任务 ID。轨迹根目录留待首轮 SessionID 回填后按 Harness 定位（Claude Code→本次导出到本机的 `records/{任务}/{任务}-trajectory.jsonl`，其容器内来源为 `/home/node/.claude/projects/-workspace/`）。**建议同时记录镜像 tag + manifest digest 与隔离模式**，否则不同批次的数据无法追溯到底跑的是哪个镜像。
5. 起草**首轮提示词**（真实用户口径、自然语言）：可引用 `prompt-architect` 起草；练习阶段经人工确认后写盘即可，正式交付时再先经 `humanizer-zh` 去 AI 化。
6. **准备容器挂载源（Windows）**：任务副本目录就是模型工作目录。Windows 直接把本机任务副本目录 `{REPO_BASE_PATH}\{项目}\{项目}-{类型}\{项目}-{类型}-{索引}\` 挂载为容器的 `/workspace`（见第 2 步 `docker run -d --mount type=bind,source=<副本目录>,target=/workspace`），**不需要 `docker cp` 把代码放进容器，也不需要 chown**。⚠️ 挂载目录里**不要放依赖包**（node_modules/.venv/__pycache__/dist 等，体积大），副本应只含被 git 跟踪的源码文件；任务结束后按 `.gitignore` 清理模型新装的依赖。
7. 输出：任务信息文件路径 + 首轮提示词，提示用户确认后到 Windows 容器内 Claude Code 执行

> ⚠️ **出题要难**：首轮提示词做高难度、多需求、跨模块/多约束题，严禁简单题。**Bug修复先埋点**：在初始化/打快照阶段把 bug 写进源码（无注释标记、藏得深、可复现），埋点 commit 即初始快照；首轮 prompt 只描述症状、不透露 bug 位置。（详见 skills/01-task-create.md「出题与埋点要求」）

### 产物

```text
records/app-12/app-12-codegen/task-info.md
```

---

## 第 2 步：与模型交互（用户在 Windows 容器内的 Claude Code 中）

> Claude Code 跑在 Windows 的 Docker 容器（`cc-solo-{任务}`，镜像 `nicehey/benzhi-claude-code:1.0`）里，**容器内工作目录恒为 `/workspace`**（= 挂载的本机任务副本目录，见下）。轨迹落在容器内 `/home/node/.claude/projects/-workspace/`。
>
> 与 Mac 版不同：Windows 镜像**没有 `cc` 快捷入口**，用 `docker exec -it -w /workspace "cc-solo-{任务}" claude --dangerously-skip-permissions` 直接进入。
>
> 权限**统一免确认**（`--dangerously-skip-permissions`，与 Mac 内置口径一致）：启动命令里必须显式带上这个 flag，见第 2 步第 1 条。
>
> 容器名统一 `cc-solo-{任务}`（如 `cc-solo-app-12-bugfix-01`），`{任务}` 就是任务 ID；`docker ps -a` 可查。

### 前置：确保容器可用（首次启动 + 常见踩坑）

首次启动容器（**每题一个容器**，勿复用做别的题；同题中断后可用 `docker start "cc-solo-$task"` 续用）：

```powershell
$task='app-12-bugfix-01'; $model='<管理员给的完整模型名>'
$taskDir='<本机任务副本目录>'   # 即 source-code\app-12\app-12-bugfix\app-12-bugfix-01
docker run -d --name "cc-solo-$task" `
  --mount "type=bind,source=$taskDir,target=/workspace" `
  -e "apikey=<你的Key>" `
  -e "ANTHROPIC_MODEL=$model" -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" `
  nicehey/benzhi-claude-code:1.0
```

### 单题 vs 多题：一次起好几题用循环（推荐）

- **只起一题**：用上面那条单题命令即可。
- **一次起多题（多题批次推荐，已实测）**：变量与循环写在**同一段**里一次贴完，需要哪几题就改 `$tasks`。

```powershell
$root  = 'D:\charles\program\ai\ai-eval-workspace\sessions\cc-solo\session-0909\source-code\cc-001\cc-001-feature'
$model = 'auto_model/urm'          # 网关允许的完整模型名（本机 secrets.toml [claude_gateway].model）
$key   = '<你的Key>'
$tasks = 6..10 | ForEach-Object { 'cc-001-feature-{0:D2}' -f $_ }

foreach ($task in $tasks) {
  $src = (Resolve-Path (Join-Path $root $task)).Path   # 目录不存在/变量为空会当场报错，不会拼出非法路径
  Write-Host "启动 $task  <-  $src" -ForegroundColor Cyan
  docker run -d --name "cc-solo-$task" `
    --mount "type=bind,source=$src,target=/workspace" `
    -e "apikey=$key" `
    -e "ANTHROPIC_MODEL=$model" -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" `
    -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" `
    -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" `
    nicehey/benzhi-claude-code:1.0
}
docker ps --format "{{.Names}}`t{{.Status}}"   # 每个任务应各有一行 Up
```

> 三个要点：① **变量只在当前 PowerShell 窗口有效**，换窗口/重开就没了，所以「设变量」和「跑循环」必须一次贴完（已实测踩坑：`$root` 为空时 `--mount` 会拼成 `\cc-001-feature-06`，docker 报 `is not a valid Windows path`）；② 用 `Join-Path` + `Resolve-Path` 拼路径，目录不存在时提前报错，而不是把空字符串塞进 `--mount`；③ 每轮 `Write-Host` 打印真实挂载源，出问题一眼看出是哪个变量空了。
>
> 重建前先清残留（`docker ps -a` 里状态不是 `Up` 的同名容器）：
> ```powershell
> foreach ($task in $tasks) { docker rm -f "cc-solo-$task" 2>$null }
> ```

跑之前先看这四个最常踩的坑，出事按序处理：

- **PIPE 连不上引擎**：报错 `failed to connect to the docker API at npipe://… dockerDesktopLinuxEngine … The system cannot find the file specified`，说明 Docker Desktop 没启动或引擎未就绪。打开 Docker Desktop，等 `docker info` 能返回 `ServerVersion`，确认处于 **Linux 容器模式**，再执行 `docker run`。
- **直连 Docker Hub 拉镜像超时**：报错 `dialing registry-1.docker.io:443 … connection attempt failed`，是国内网络访问 Docker Hub 不通。或在 Docker Desktop 配 `registry-mirrors`，或改用加速地址拉取再打回标准标签，例如 `docker pull docker.1ms.run/nicehey/benzhi-claude-code:1.0` → `docker tag docker.1ms.run/nicehey/benzhi-claude-code:1.0 nicehey/benzhi-claude-code:1.0`。
- **进容器后 Claude 报 `403 key not allowed to access model`**（`can only access models=['…']. Tried to access ark/urm-01`）：镜像固化的模型名与 Key 实际可访问的模型不一致。把上面的 5 个模型环境变量（`$model`）都覆盖成网关允许的完整模型名后重建容器。
- **`docker run` 报 `\cc-001-feature-06%!(EXTRA string=is not a valid Windows path)`**：`--mount` 的 `source` 拼出来是空的——九成是 `$root`/`$taskDir` 这类变量没在**当前窗口**赋值（变量跨窗口会丢），少数是副本目录不存在。按上面的循环写法（变量与循环写在同一段 + `Resolve-Path`）一次贴完即可。

详细排障见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)「常见问题」。

1. **进入容器并启动 Claude（统一免确认模式）**：
   ```powershell
   docker exec "cc-solo-$task" git config --global --add safe.directory /workspace

   docker exec -it -w /workspace "cc-solo-$task" claude --dangerously-skip-permissions
   ```
   第一条是告诉 Git 信任 `/workspace`（避免 `dubious ownership` 报错，每个新容器首次执行一次）。第二条打开 Claude，在 `/workspace`（= 本机任务副本目录）中工作。首次进入可能询问界面主题、显示安全提示、或询问是否信任当前目录（选择信任，路径应为 `/workspace`）。

   > **本项目统一用免确认模式**：容器内是 `node` 非 root 用户，`--dangerously-skip-permissions` 可用（`claude --help` 已确认；等价写法 `--permission-mode bypassPermissions`），与 Mac 镜像内置的口径一致。**不要用裸 `claude`**——那会退化成逐条询问，同批数据的 Harness 审批口径就不一致了；`task-info.md` 的「审批模式」字段统一记为 `claude --dangerously-skip-permissions（免确认 / bypassPermissions）`。
   > - ⚠️ **代价**：进去之后 Claude 会自动执行命令、改文件、访问网络，**不再逐条问你**。影响范围限于本机挂载的那个任务副本目录，进去前先确认挂载的是本题目录（`docker inspect` 可查）。
   > - **万一进成了逐条询问模式**：`/exit` 退出后带 `--continue` 重进，保留同一 SessionID：`docker exec -it -w /workspace "cc-solo-$task" claude --dangerously-skip-permissions --continue`。
   > ✅ 已实测：挂载目录在容器内是 `-rwxrwxrwx root root`，`node` 用户可直接新建/追加文件 ⇒ **不需要 `chown`**；但挂载**带 `.git` 的仓库**时，不执行上面那条 `safe.directory` 会报 `fatal: detected dubious ownership in repository at '/workspace'`。详见 [image-upgrade-review.md](image-upgrade-review.md) 第七节。
2. **做本轮对话**（默认推荐：一个 Claude 会话里连续发多轮，不退出）：
   - 第 1 轮：粘贴首轮提示词（见第 1 步产物 / `task-info.md` 的「首轮提示词」），开始对话。
   - 继续下一轮：直接在**同一个** Claude 会话里再发一条消息（如「继续」「再改成…」），SessionID 不变，轮次随之递增。
   - 免确认模式下 Claude 会自行执行命令、改文件（见第 1 条），你只需看它的产出、决定下一轮怎么提要求。
3. **（可选）退出会话 + 下次怎么接着做**：如果确实想退出 Claude：
   - `/exit` 一次即回到 PowerShell；**容器保留**（常驻容器，不会随退出销毁）。
   - **下次继续下一轮**（**仅限同一道题**）：进容器后**不要用裸 `claude`**（会新建一个 SessionID，打破「一个任务 = 一个会话窗口」），改用 `claude --continue`（恢复当前目录最近一次会话，同一 SessionID）或 `claude --resume <SessionID>`，命令形如 `docker exec -it -w /workspace "cc-solo-$task" claude --dangerously-skip-permissions --continue`。详见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)「如何恢复历史会话」。
   - **换一道题**必须新建容器（`cc-solo-{新任务}` + 新挂载目录），不能拿旧容器接着做。

> 💡 一句话：**一个任务的几轮对话必须落在同一个 SessionID（一个会话窗口）里。** 默认就**别退出**，一个 `claude` 会话连发多轮。做完一轮后直接告诉 agent `cc-solo {任务} round N` 即可——导出轨迹、切片、录入都由 agent 执行 PowerShell docker 命令完成，你不用手动 `docker cp`。

---

## 第 3 步：单轮录入（每轮一条数据）

### 指令模板

```text
cc-solo app-12-bugfix-01 round 1
```

> 只写这一行即可：SessionID / User Prompt / TurnID 由 agent 从本机轨迹自取；任务类型（按本轮主要意图）、任务难度、语言/框架由 agent 从轨迹 + 仓库自动推断，有疑问才回问确认。

### AI 会执行

1. **从容器导出本轮轨迹（agent 执行 PowerShell docker 命令）**：等模型答完静止后导出轨迹——`docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/." records\{项目}\{项目}-{类型}\{任务}\`。**代码产物已在本机任务副本目录（挂载为 `/workspace`），无需回导**；只做依赖清理：任务结束后按 `.gitignore` 清理模型在挂载目录里新装的依赖包（node_modules/.venv/__pycache__ 等），不整目录回导。
2. 从轨迹切出第 N 轮（一轮=一次 user 键入），取其 User Prompt 原文与 promptId；本轮那段存 `records\<repo>\<题号>\<题号>-R0N-trajectory.jsonl`（**仅用于打分阶段定位单轮**），完整轨迹保留为 `records\<repo>\<题号>\<题号>-trajectory.jsonl`（**提交时的轨迹附件**，随轮次追加，会话结束才是最终版）。
3. 创建 `records\<repo>\<题号>\<题号>-R0N.md`，回填 User Prompt、任务类型/难度、语言/框架、TurnID。
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
  1. 导出完整轨迹并核对：`docker cp "cc-solo-{任务}:/home/node/.claude/projects/-workspace/." <目标目录>`，与该任务已录入的各轮切片比对，确认不缺轮；
  2. 源码不用回导——Windows 是把任务副本目录直接挂载成 `/workspace`，模型改的就是本机那份，只需按 `.gitignore` 排除/清理模型新装的依赖包（node_modules/.venv/__pycache__/dist 等）；
  3. 该任务不再需要继续对话时 `docker rm "cc-solo-{任务}"`（**确认轨迹已导出后再删**）。Windows 侧容器支持 `--continue`，想留着补几轮就先别删；可用 `docker ps -a --filter name=cc-solo-` 盘点本期还有哪些容器。
- 新开任务：重复第 1-4 步，使用**新的任务副本目录 + 新容器**（容器名换新任务名，不能复用旧容器）：同一项目继续另一种类型用 `app-12-feat`（在生成产物上迭代）/ `app-12-bugfix`（埋点后修复）等新任务 ID；全新项目则用新仓库名（如 `app-13-codegen`）
- ⚠️ 若会话中途意外退出且无法继续：剩余轮次作废，按已导出的轮次收尾，并在 `task-info.md` 备注「会话提前终止（第 N 轮后）」

---

## 第 6 步：生成评价结果文件

> 2026-09-10 起不再导出「正式提交表 CSV」、也不再投递飞书，改为按平台提交表单的字段规范生成**评价结果文件**（一轮 = 一条），后续通过提交接口提交。Mac 与 Windows 完全一致。

### 指令模板

```text
cc-solo export
```

### AI 会执行

1. **先请求平台表单定义接口**（`GET .../submissions/form-schema`），与本地 `docs/submission/fields.json` 比对 fingerprint 与字段集合，防止平台表单改了本地还按旧规范生成；不一致就重跑抽取再继续。
2. 如需更新规范：`python scripts/cc-solo/extract_submit_fields.py`（**默认拉平台实时接口**，`--source js` 用本地快照）→ 写 `docs/submission/fields.json`
3. 扫描 `{RECORD_DIR}` 全部任务，按 `task-info.md` + 各 `{任务}-R{NN}.md` 合成**24 个提交字段**（任务类型/难度/语言框架、Harness 及版本、操作系统、可复现等级、初始环境快照、User Prompt、SessionID、TurnID、轨迹文件、五维分数与描述、其他问题、轮次排序）
   - **样例项目不导出、不提交**：`records/{项目}/` 下的 `h5-demo` 只是样例（快照填的是本地裸 SHA、首轮难度写了「简单」，本就不满足提交要求），导出脚本按 `config.toml [exclude].projects` 直接跳过并打印跳过了哪几条。新增样例项目时往那个数组里加名字即可，**不要靠临时参数或人工记得排除**。
4. 运行质检（表单规范层 + 项目规则层 + 去 AI 化层），逐条给出 error / warn
5. 输出：`deliverables/cc-solo/{SESSION_NAME}/评价结果-{SESSION_NAME}-{date}.json`（主产物）+ `-质检报告.md`（**不再产出人工核对 CSV**，2026-09-12 起取消）

> ⚠️ **多轮任务的轨迹附件口径（导出前必读）**：同一任务（同一 SessionID）的各轮记录，`轨迹文件` 都指向**同一份最终完整轨迹** `{任务}-trajectory.jsonl`（含该会话全部轮次），各轮靠 `SessionID` + `TurnID` 定位。
> 所以**导出与提交必须在任务会话结束之后执行**——会话还没结束就导出，整份轨迹只含到当时为止的轮次，后面几轮的记录会挂着一份不完整的轨迹。每轮的 `{任务}-R{NN}-trajectory.jsonl` 切片只是打分阶段定位单轮用的中间产物，**不作提交附件**。

```powershell
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

> **本节与 Mac 版完全一致**：提交走同一套接口与脚本，与容器跑在哪台机器无关；命令按 Windows 写法执行（PowerShell，路径用反斜杠）。

## 第 7 步：提交（提交接口）

> **提交接口已启用**：`POST https://solo2.jzxhnh.com/api/v1/submissions`，已写在 `config.toml [submission].submit_url`（`secrets.toml [submission].submit_url` 若填写则优先），`docs/submission/fields.json` 的 `submit_api.url` 也已同步。2026-09-12 起已实际提交（app-001-codegen-03~10 共 10 条）。
>
> 凭据在 `secrets.toml [submission]`（`cookie` + `username` / `password`）；cookie 约 2 天过期，**脚本会自动登录刷新并回写**，无需手工复制。登录结果缓存在 `projects/cc-solo/.solo_session.json`（gitignore），**没过期就不会重复登录**（`--status` 查看）。

### 指令模板

```text
cc-solo export submit
```

### AI 会执行

1. 确认评价结果文件已生成、质检无未处理的 error
2. **先 dry-run**（不发任何请求，只打印将上传的轨迹与将提交的字段）：
   `python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json`
3. 先只上传轨迹、验证 cookie 与附件链路：`… --upload-only --commit --write-back`（会把远端 path 回写进结果文件）
4. 正式提交：`… --commit`（或加 `--url <提交接口>`；`--only-ready` 可跳过仍有 error 的条目、`--record <任务#轮次>` 可只提某一条）
5. 输出每条的上传结果与接口返回；失败的条目修正后重试，**已提交的同一条不要再 POST**（平台按 SessionID + TurnID 判重，会返回 422）

### 产物

提交接口按「一轮 = 一条记录」落库，每条含 24 个字段 + 轨迹附件。

### 注意事项

- 轨迹是**附件**字段：必须先用上传接口拿远端 path，再写进 `trace_file` 提交（脚本自动处理）。
- cookie 会过期（约 2 天）：脚本优先复用会话缓存，缺失/过期或遇到 401、403 时才自动登录刷新（也可 `--login-only --commit` 主动续期、`--status` 查看剩余有效期）。
- 时限沿用约定：当天 20:00 前产生的数据当天提交，20:00 之后的次日 14:00 前提交。
- 旧的飞书投递（`append_delivery_feishu.py`）与 CSV 提交表（`export_submit.py`）**已退役**，仅作历史留存。

---

## 第 8 步：返修（提交被打回后整改并更新）

> 平台质检（本地规则 / 查重 / 五维描述）会给每条提交一个结论：**通过**（`QC_PASSED`）或 **待返修**（`PENDING_FIX`）退回，退回时给出「维度 · 规则」与缺失要素（如「任务规划 · 非满分描述缺少核心要素：未写明具体位置与客观后果」；也见过「只有主观形容词、没有客观证据」「描述是电报式短语堆砌、不成完整句」「打分与描述极端背离」）。

**链路**：发现（列表）→ 归类原因 → 查详情 → 整改 `records/` → 过门禁 → 重新生成评价结果 → PUT 更新升版本 → 复盘（把新规则写回文档）。

### 指令模板

```text
cc-solo 返修
```

**不带 ID 时由 agent 自己去发现**（下一个要处理的批次）；已知 ID 时写 `cc-solo 返修 5237 5238`（空格或逗号分隔）。**你只发这一行**，下面全部由 agent 执行。

> ⛔ **排除名单（红线）**：`config.toml [submission].fix_exclude_ids`（当前 `4142, 4143, 4144`）里的提交**一律不整改、不更新**——这几条规则的最终判定还没定，动了会与别人正在对齐的口径冲突。脚本会把它们从待处理清单里剔除并单独打印「另排除 N 条」。

### AI 会执行

1. **发现 + 归类**（不带 ID 时的第一步）：
   ```powershell
   python scripts/cc-solo/list_pending_fix.py --detail
   ```
   列表接口 `GET {提交接口}?page=1&page_size=20&stage=&keyword=&date_from=&date_to=&user_id=0`（返回 `items[]` + `meta{page,page_size,total,total_pages}`）；脚本自动翻页、只看 `status == PENDING_FIX`、剔除排除名单。**先按「维度 · 规则」统计本批是哪几条规则在打回、各占多少条，再决定改法**——同类规则要批量改，别逐条凭感觉改字。
2. **查详情**（只读 GET `{提交接口}/{ID}`）：读出状态（`status` / `status_label`）、`current_version`、`editable`、命中规则、打回原因（`qc_summary`）、重复命中明细（`dedup_hits[]`：命中字段、相似度、对比来源、历史侧与本次侧摘要）、锁定字段（`locked_fields`）。原始详情落盘到 `deliverables/cc-solo/{SESSION}/submission-{ID}-detail.json` 备查。
   ```powershell
   python scripts/cc-solo/submit_eval_result.py --detail-id 5237
   ```
3. **按原因整改 `records/` 里对应轮的描述**（不是改平台上的字，也不是改产物文件）：
   - 命中 **B-7 分段复读 / 长片段** → **针对本轮实际轨迹重写**该字段：换掉与历史池重合的句式，写进这一轮独有的证据（读了哪些文件、依赖顺序、中途改了什么方案、哪一步没核实），依据一件不减、不添新说法；
   - 命中 **A 表套话词 / 符号** → 按 `docs/annotate-guide.md` §9 改写；定位信息写到页面、处理、第几步与对应文件或方法（英文标识可直接写）；
   - 命中 **跨轮次 / 前后对比** → 去掉「上一轮／原来／原先／本来」这类说法，直接陈述现象与现状；
   - 命中 **非满分描述缺少核心要素 / 只有主观形容词 / 电报式短语 / 打分与描述背离**（2026-09-12 实测：一批 22 条里 55 处栽在这四条）→ ① 任何 **<5 分**的维度都要写清「具体位置（第几步 / 哪次工具调用 / 哪个页面或接口 / 哪个文件或函数 / 哪条命令或报错原文）＋ 该维度哪里不足 ＋ 客观后果（返工、遗漏、用户看到什么、多花了哪些步骤）」；② 不写「不可追踪／轻微反复／明显的猜测式推理」这类主观形容词，换成客观事实；③ 每个分句都要有主谓，不能名词短语堆砌；④ **4 分档也要写出扣分点**，整段只肯定会被判「打分与描述极端背离」。
   - **第二轮打回实测（2026-09-13：一批 29 条里 7 条二轮再被打回，全部栽在「位置不够具体 + 没有后果」）**：
     ⑤ **次数统计 ≠ 位置**：「四十次调用里只有一次被拒」「三次没成功」「多花了五次命令」这类没有对象的次数会被判「读者无法定位」；要摊开成第几次工具调用 + 文件名或函数名 + 命令原文或报错原文 + 后果（例：`第 12 次调用的验证脚本只建了编号 42 的用户，却拿编号 43 的过期令牌请求下载接口，外键找不到对应用户、接口返回 500，第 13 到第 17 次调用连跑五条排查命令才缩回这条用例`）。
     ⑥ **空指代一律不写**：`查不清的那条`、`同一条现象`、`这一步`、`那处判断`要换成具体指向（哪一组现象、哪个页面、哪个文件、第几次调用）。
     ⑦ **环境原因不算「执行能力」扣分**：容器或环境缺依赖（没装数据库访问组件、基础镜像没有编译工具链）造成的失败，平台判「这不是模型自身能力造成的」；扣分点换成模型自身失误（写错断言或桩、命令参数写错、同一段逻辑换三版、自查命令过滤条件写错）。
     ⑧ **同批整改不得共用骨架**：按同一条规则批量补三要素时最容易写成同一套句式，实测被按 **B-6 骨架累加雷同**判中（相似度 47.7%）；每条换结构，写完横着比一遍开头。
     ⑨ **改完门禁 + 全字段红线扫描两遍都要干净**：改写本身会引入新红线（实测一轮改写新引入 A 表词 `收尾` 1 处、humanizer 符号 `「」` 1 处）。
   改完过门禁：`python scripts/cc-solo/check_round_files.py --task {任务}`（要 `error 0`），再跑一遍描述风险自查 `python scripts/cc-solo/scan_desc_risks.py --project {项目}`（提示级：R1 次数无对象 / R2 空指代 / R3 环境原因挂扣分 / R4 主观形容词，命中需人工判断），最后重新生成评价结果：`python scripts/cc-solo/build_eval_result.py --task <任务1,任务2,…>`。
4. **更新到平台**（PUT `{提交接口}/{ID}`，body 与提交同形，另带 `comment`）：轨迹附件**沿用平台上已有的那一份**，不重新上传；字段逐项与平台现值比对，只把改动写上去，更新前打印「将更新 N 个字段」供确认。
   ```powershell
   # 先预览（不发请求）
   python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json --update-id 5237
   # 确认后执行（把 --commit 加上；--comment 可自定义备注）
   python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json \
     --update-id 5237 --comment "按质检打回意见整改后更新" --commit --write-back
   ```
5. **回报 + 复盘（自我学习）**：回报新版本号（`current_version`）、新状态，以及这次改了哪个字段、改前改后字数；平台随即重新质检，稍后可再 `--detail-id` 查看新结论。然后把这一轮**新出现的打回规则**补进 `docs/annotate-guide.md` §9、`skills/03-score-annotate.md` 的硬性要求、`skills/04-export-submit.md` 步骤 6——写成带反例与改写示例的**自查项**；同一条规则再次被打回，说明自查项没落地，**优先改自查项**而不是只改这一条数据。

### 注意事项

- **排除名单里的 ID 一律不动**（`config.toml [submission].fix_exclude_ids`），也不要为了让它们「看起来通过」去改别的字段。
- `editable=false`（如质检中、已通过、已裁决）时**不能改**，脚本会跳过并说明当前状态；只有 `PENDING_FIX`（待返修）才可更新。
- **锁定字段不可改**：`env_snapshot`、`harness`、`repro_level`（平台侧 `locked_fields` 给出，改别的字段即可）。
- 附件沿用平台的远端文件，**不要**为了返修重新上传轨迹（上传会生成新文件，白占空间）。
- 返修改的是 `records/` 数据文件，**改完要重新生成评价结果**（`cc-solo export`）再走本步，别手改产物 JSON。
- 返修不产生新记录，只升版本号；同一条反复被打回时，每次都要按**新的打回原因**重新整改，别只改一处字。
- 返修不是「改字过关」：**先归类、后批量改、最后复盘**才算走完一步；每轮返修结束都要问一句「这条规则写进自查项了吗」。
