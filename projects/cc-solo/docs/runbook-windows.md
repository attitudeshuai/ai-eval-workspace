# cc-solo 满意度标注 Runbook（Windows）

本 Runbook 是 [runbook.md](runbook.md) 的 Windows 版。流程、指令模板、产物与 Mac 版完全一致，**只有「第 2 步：与模型交互」里操作 Claude Code 的终端命令按 Windows 版 Docker 用法改写**。Windows 版 Docker 的完整使用说明见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)；**从安装 Docker 到导出轨迹**的完整操作见 [WINDOWS_DOCKER_SETUP.md](WINDOWS_DOCKER_SETUP.md)。

配置统一读取 `projects/cc-solo/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 技术细节见 `skills/01-task-create.md` 等 skill 文件；评分表/原因写法速查见 `docs/annotate-guide.md`。

## 与 Mac 版的关键差异（速览）

| 环节 | Mac 版 | Windows 版（本文档） |
|---|---|---|
| 镜像 | `adminfather/benzhi-claude-code:20260909-isolated-git`（固定 tag，勿用 latest） | `nicehey/benzhi-claude-code:1.0`（Windows 侧无新镜像，仅此一个 tag） |
| 启动方式 | `docker run -it`（前台直接进 Claude，启动后 agent 再播种） | `docker run -d`（后台常驻）+ 挂载本机任务副本目录为 `/workspace` |
| 容器入口 | 启动即进入 Claude | `docker exec -it -w /workspace "cc-solo-{任务}" claude` |
| 命令审批 | 镜像**内置** `--dangerously-skip-permissions`，Claude 自动执行命令（无需人工确认） | 默认普通 `claude`（逐条询问）；**可加 `--dangerously-skip-permissions` 免确认**，见第 2 步第 1 条 |
| 退出方式 | Ctrl+D 两次（无 `/exit`） | `/exit` 一次，容器保留 |
| 工作目录 | `/workspace` | `/workspace` |
| 轨迹目录 | `/home/node/.claude/projects/-workspace/` | 相同 |
| 会话恢复 | 不可恢复（一次性容器，哨兵拒绝 `--continue`） | 同题可 `claude --continue` / `--resume` |

> 除第 2 步的终端命令外，其余各步（建任务/出题/单轮录入/五维打分/生成评价结果/提交）与 Mac 版完全一致。第 3~7 步照抄 Mac 版即可。

---

## 通用启动语

```text
cc-solo {项目} {操作}
```

- **generate 用「项目名 + 各类型配额」**：`cc-solo app-12 generate` + 各类型配额（如 `bugfix*5 / codegen*5 / feature*5 / understand*1 / refactor*1 / engineering*1 / test*1`）→ agent 建 N 份任务副本 + 提示词（Windows 下这些副本目录直接作为挂载源，无需复制进容器）。
- **round / score 用「任务名」**（`{项目}-{类型}-{索引}`）：`cc-solo app-12-bugfix-01 round 1`、`cc-solo app-12-bugfix-01 score 1`。
- **export 用 `cc-solo export`**（TODO：最终交付格式未定）。

> 这里的 `cc-solo {项目} {操作}` 是**给 AI agent 的自然语言指令**（runbook 通用缩写），不是容器命令。Windows 容器里**没有** `cc` 快捷入口——进入容器后是手动敲 `claude`。两者不要混淆。

> 任务名 = **副本目录名 = 提示词名 = `{项目}-{类型}-{索引}`**（如 `app-12-bugfix-01`）。**1 任务 = 1 容器**：容器名统一 `cc-solo-{任务}`（如 `cc-solo-app-12-bugfix-01`），容器内工作目录恒为 `/workspace`，题目身份由「容器名 + 挂载目录」承载。同一项目按 7 类任务复制成多份副本，**索引全局累加、两位补零**。类型 slug 对照：`0-1代码生成`→`codegen`、`Feature迭代`→`feature`、`Bug修复`→`bugfix`、`代码理解`→`understand`、`代码重构`→`refactor`、`工程化`→`engineering`、`代码测试`→`test`。
> 副本 = 素材源复制 + 改名；**共用同一个 base commit 快照**；**暂不建每份独立 git、不提交/push**。

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

## ⚠️ 使用前必读

- **一个任务 = 一个会话窗口（≤10 轮）= 一个容器 = 一个本机工作目录；一轮 = 一条数据**。
- **AI 交付文本必须先经去 AI 化**：AI 起草的提示词/评分依据无论练习还是正式，落盘/投递前都须先经 `skills/humanizer-zh` 去 AI 化（练习阶段允许 AI 直接打分、无需人工确认；正式交付再人工复核），并严格按五维模式；人工撰写的原文保持原样。
- 被标注模型跑在 **Claude Code** 里，由用户在终端里操作，本 skill 不代跑。
- Windows 下 Claude Code 跑在 Docker 容器里，**终端命令用 PowerShell 执行**。

## 人工 / agent 分工（一眼看清谁做什么）

| 环节 | 谁做 | 说明 |
|---|---|---|
| 本地 → 容器（挂载任务副本为 `/workspace`，无需 docker cp/chown） | **agent 自动** | Windows 直接挂载，Mac 由 agent 启动后播种 |
| 容器 → 本地（导出轨迹；代码产物已在挂载目录，无需回导） | **agent 自动** | 依赖包按 `.gitignore` 排除/清理 |
| 容器里跟 Claude Code 交互（贴提示词、追加轮次） | **人工** | 唯一需要你操作的环节 |
| 切轮次、写 R0N、五维打分、导出 | **agent 自动** | 你只发指令（`round N`/`score N`） |

> 一句话：你只在容器里跑 Claude Code；其余建副本、挂载、导出轨迹、切片、录入、打分、导出全由 agent 在宿主机直接执行。

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

0. **雷同题红线（第一步必检）**：对照 `docs/annotate-guide.md` §7「不被允许的雷同题」逐项核查素材源项目主题。**命中即中止**，提示用户换素材，不得继续建副本/出题/打快照。
1. 校验仓库存在、工作区干净、`.gitignore` 无泄漏风险（`.env`/密钥/token 已覆盖）；**并校验仓库结构**：素材源是否位于 `source-code/{项目}/`（唯一 git 仓库），任务副本是否按类型分组 `{项目}-{类型}/{项目}-{类型}-{索引}/` 嵌套其下。结构不规范 → 先列「实际结构 vs 规范结构」差异 → **提示用户确认** → 确认后整理成该格式再继续（未确认不移动文件）。
2. **准备远端（一个素材源 = 一个 base commit 快照）**：用 `github_username` + PAT 为**该素材源**新建（或复用）**一个** GitHub 仓库（`cc-solo-{项目}`，如 `cc-solo-app-12`），把本地 origin 指向它；来源仓库仅作内容来源，不向其提交。
3. **打初始快照**：提交一个 baseline commit → push 到**该仓库** → 取**完整 40 位 SHA** 生成 permalink（`https://github.com/<owner>/cc-solo-{项目}/commit/<40sha>`）。**该素材源下所有任务副本共用这同一个快照地址。**
4. 创建 `records/app-12/app-12-codegen/task-info.md`：Repo URL、本地路径、初始环境快照、Harness、Harness版本、操作系统、环境可复现等级（共享字段）；记录目录名 = 任务 ID。轨迹根目录留待首轮 SessionID 回填后按 Harness 定位（Claude Code→本次导出到本机的 `records/{任务}/{任务}-trajectory.jsonl`，其容器内来源为 `/home/node/.claude/projects/-workspace/`）
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
> 与 Mac 版不同：Windows 镜像**没有 `cc` 快捷入口**，用 `docker exec -it -w /workspace "cc-solo-{任务}" claude` 直接进入。
>
> 权限默认**逐条询问**；想和 Mac 一样免确认（自动模式），加 `--dangerously-skip-permissions`，见第 2 步第 1 条。
>
> 容器名统一 `cc-solo-{任务}`（如 `cc-solo-app-12-bugfix-01`），`{任务}` 就是任务 ID；`docker ps -a` 可查。

### 前置：确保容器可用（首次启动 + 三个踩坑）

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

跑之前先看这三个最常踩的坑，出事按序处理：

- **PIPE 连不上引擎**：报错 `failed to connect to the docker API at npipe://… dockerDesktopLinuxEngine … The system cannot find the file specified`，说明 Docker Desktop 没启动或引擎未就绪。打开 Docker Desktop，等 `docker info` 能返回 `ServerVersion`，确认处于 **Linux 容器模式**，再执行 `docker run`。
- **直连 Docker Hub 拉镜像超时**：报错 `dialing registry-1.docker.io:443 … connection attempt failed`，是国内网络访问 Docker Hub 不通。或在 Docker Desktop 配 `registry-mirrors`，或改用加速地址拉取再打回标准标签，例如 `docker pull docker.1ms.run/nicehey/benzhi-claude-code:1.0` → `docker tag docker.1ms.run/nicehey/benzhi-claude-code:1.0 nicehey/benzhi-claude-code:1.0`。
- **进容器后 Claude 报 `403 key not allowed to access model`**（`can only access models=['…']. Tried to access ark/urm-01`）：镜像固化的模型名与 Key 实际可访问的模型不一致。把上面的 5 个模型环境变量（`$model`）都覆盖成网关允许的完整模型名后重建容器。

详细排障见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)「常见问题」。

1. **进入容器并启动 Claude**：
   ```powershell
   docker exec "cc-solo-$task" git config --global --add safe.directory /workspace

   # 方式 A（默认）：逐条确认权限
   docker exec -it -w /workspace "cc-solo-$task" claude

   # 方式 B（免确认 / 自动模式）：自动执行命令、改文件，不再逐条询问
   docker exec -it -w /workspace "cc-solo-$task" claude --dangerously-skip-permissions
   ```
   第一条是告诉 Git 信任 `/workspace`（避免 `dubious ownership` 报错，每个新容器首次执行一次）。第二条打开 Claude，在 `/workspace`（= 本机任务副本目录）中工作。首次进入可能询问界面主题、显示安全提示、或询问是否信任当前目录（选择信任，路径应为 `/workspace`）。

   > **免确认模式（自动模式）**：容器内是 `node` 非 root 用户，`--dangerously-skip-permissions` 可用（`claude --help` 已确认；等价写法 `--permission-mode bypassPermissions`）。**同一批数据要么全免确认、要么全逐条确认，不要混用**——否则同批 Harness 审批口径不一致，须把实际审批模式记进 `task-info.md`。
   > - **会话中途想切**：`/exit` 退出后带 `--continue` 重进，保留同一 SessionID：`docker exec -it -w /workspace "cc-solo-$task" claude --dangerously-skip-permissions --continue`。
   > - **不想重启会话**的临时手段：弹窗里选 `2. Yes, and don't ask again for …`（只对同类命令生效），或按 `Shift+Tab` 切到自动接受编辑模式（bash 命令仍可能问）。
   > ✅ 已实测：挂载目录在容器内是 `-rwxrwxrwx root root`，`node` 用户可直接新建/追加文件 ⇒ **不需要 `chown`**；但挂载**带 `.git` 的仓库**时，不执行上面那条 `safe.directory` 会报 `fatal: detected dubious ownership in repository at '/workspace'`。详见 [image-upgrade-review.md](image-upgrade-review.md) 第七节。
2. **做本轮对话**（默认推荐：一个 Claude 会话里连续发多轮，不退出）：
   - 第 1 轮：粘贴首轮提示词（见第 1 步产物 / `task-info.md` 的「首轮提示词」），开始对话。
   - 继续下一轮：直接在**同一个** Claude 会话里再发一条消息（如「继续」「再改成…」），SessionID 不变，轮次随之递增。
   - ⚠️ Windows 镜像**默认未启用**免确认：Claude 每次执行命令、创建/修改文件前都会询问，**确认操作内容后选择「允许」**（想改成免确认见第 1 条的「方式 B」）。
3. **（可选）退出会话 + 下次怎么接着做**：如果确实想退出 Claude：
   - `/exit` 一次即回到 PowerShell；**容器保留**（常驻容器，不会随退出销毁）。
   - **下次继续下一轮**（**仅限同一道题**）：进容器后**不要用裸 `claude`**（会新建一个 SessionID，打破「一个任务 = 一个会话窗口」），改用 `claude --continue`（恢复当前目录最近一次会话，同一 SessionID）或 `claude --resume <SessionID>`，命令形如 `docker exec -it -w /workspace "cc-solo-$task" claude --continue`。详见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)「如何恢复历史会话」。
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
4. 判定是否继续：产物不满意（代码漏洞 / 功能未实现 / 实现不合理）→ agent 拆分不满点、生成下一轮提示词（开头「修复bug：」、去口水话、预计改动 ≥2 文件）并写 `-R{NN+1}-prompt.md`；满意则结束，仅过程不满意不生成下一轮提示词。第 10 轮后强制结束本任务

### 产物

```text
records/app-12/app-12-codegen/app-12-codegen-R01.md   # 已填入五维打分与依据
```

---

## 第 5 步：会话结束，开新任务

- 达到 10 轮，或模型达成目标且无需继续时，本任务结束
- 新开 Claude Code 会话窗口与任务目录，重复第 1-4 步：同一项目继续另一种类型用 `app-12-feat`（在生成产物上迭代）/ `app-12-bugfix`（埋点后修复）等新任务 ID；全新项目则用新仓库名（如 `app-13-codegen`）

---

## 第 6 步：生成评价结果文件

> 2026-09-10 起不再导出「正式提交表 CSV」、也不再投递飞书，改为按平台提交表单的字段规范生成**评价结果文件**（一轮 = 一条），后续通过提交接口提交。Mac 与 Windows 完全一致。

### 指令模板

```text
cc-solo export
```

### AI 会执行

1. 如表单字段有变化，先重新抽取规范：`python scripts/cc-solo/extract_submit_fields.py`（→ `docs/submission/fields.json`）
2. 扫描 `{RECORD_DIR}` 全部任务，按 `task-info.md` + 各 `{任务}-R{NN}.md` 合成**24 个提交字段**（任务类型/难度/语言框架、Harness 及版本、操作系统、可复现等级、初始环境快照、User Prompt、SessionID、TurnID、轨迹文件、五维分数与描述、其他问题、轮次排序）
3. 运行质检（表单规范层 + 项目规则层），逐条给出 error / warn
4. 输出：`deliverables/cc-solo/{SESSION_NAME}/评价结果-{SESSION_NAME}-{date}.json`（主产物）+ 同名 `.csv`（人工核对）+ `-质检报告.md`

> ⚠️ **多轮任务的轨迹附件口径（导出前必读）**：同一任务（同一 SessionID）的各轮记录，`轨迹文件` 都指向**同一份最终完整轨迹** `{任务}-trajectory.jsonl`（含该会话全部轮次），各轮靠 `SessionID` + `TurnID` 定位。
> 所以**导出与提交必须在任务会话结束之后执行**——会话还没结束就导出，整份轨迹只含到当时为止的轮次，后面几轮的记录会挂着一份不完整的轨迹。每轮的 `{任务}-R{NN}-trajectory.jsonl` 切片只是打分阶段定位单轮用的中间产物，**不作提交附件**。

```powershell
python scripts/cc-solo/build_eval_result.py
```

### 产物

```text
deliverables/cc-solo/session-0909/评价结果-session-0909-<date>.json
deliverables/cc-solo/session-0909/评价结果-session-0909-<date>.csv
deliverables/cc-solo/session-0909/评价结果-session-0909-<date>-质检报告.md
```

> 常见阻塞项（error，必须修数据后重新生成）：`初始环境快照` 不是 GitHub 40 位 SHA permalink；首轮难度写成「简单」；轨迹文件不存在；五维分数不是 1-5 整数。修的是 `records/` 里的数据文件，不要手改产物。

---

## 第 7 步：提交（提交接口）

> **提交接口 URL 待管理员提供**。拿到后写进 `projects/cc-solo/secrets.toml`：`[submission] submit_url = "…"`（同时填 `cookie`），再执行本步。

### 指令模板

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
- `secrets.toml [submission].cookie` 会过期，401/403 时重新从浏览器复制。
- 时限沿用约定：当天 20:00 前产生的数据当天提交，20:00 之后的次日 14:00 前提交。
- 旧的飞书投递（`append_delivery_feishu.py`）与 CSV 提交表（`export_submit.py`）**已退役**，仅作历史留存。
