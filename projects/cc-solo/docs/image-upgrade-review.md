# cc-solo 镜像升级影响评估（Mac 20260909 隔离版 / Windows 新版说明书）

> 评估对象：`docs/CLAUDE_CODE_DOCKER_MAC.md`、`CLAUDE_CODE_DOCKER_MAC-v2.md`、`CLAUDE_CODE_DOCKER_windows.md`、`CLAUDE_CODE_DOCKER_windows-v2.md`、`runbook.md`、`runbook-windows.md`
> 证据来源：Docker Hub API / Registry API 实测镜像 manifest 与镜像内 `entrypoint.sh` 原文（不是文档转述），采集时间 2026-09-10 之前。
> 本机 Docker 引擎未启动时写的初稿；**2026-09-10 已补实测**：Windows 镜像与 Mac 隔离镜像的关键行为均已在本机（Windows + Docker Desktop 29.7.2）跑通，结果见第七节。

---

## 一、结论摘要（先看这四条）

1. **数据模型不用改**：任务 = 会话（≤10 轮）、一轮 = 一条数据、五维打分、导出提交表、records/source-code 目录结构，全部与镜像无关，继续有效。
2. **执行模型必须改**：从「**1 个常驻容器 = N 道题 + `cc <题号>` 切目录 + `docker cp` 双向搬代码**」改为「**1 个容器 = 1 道题 + `/workspace` 双向挂载本机目录 + agent 不再搬代码**」。这不是优化选项，是 Mac 新镜像的硬约束（下面第二节）。
3. **最紧急的风险不是"要不要升级"，而是旧 Mac 文档已经失效并会直接骗人**：`adminfather/benzhi-claude-code:latest` 已于 2026-09-09 指向新隔离镜像（与 `:20260909-isolated-git` 同一 digest）。任何人照 `CLAUDE_CODE_DOCKER_MAC.md` 执行 `docker run -d … benzhi-claude-code` + `docker exec … cc 01`，都会失败（**实测**：`-d` 起的容器 5 秒内 `Exited (1)`，日志 `Error: Input must be provided either through stdin or as a prompt argument when using --print`；`cc 01` 被明确拒绝）。这篇旧文档必须立刻归档或加醒目废弃声明。
4. **第二个风险是"Harness 口径"变了**：新 Mac 镜像里的 Claude Code 被裁剪过（工具只剩 Bash/Read/Write/Edit/Glob/Grep、禁斜杠命令、`--safe-mode`、禁记忆/MCP、固定 2.1.197）。它与「Harness = Claude Code」这一提交口径、以及 2026-09-09 之前采集的 Mac 数据**不可直接互比**，尤其影响五维里的「任务规划」（没有 TodoWrite/子代理）。这一条需要评测方裁定，不是我们能自行决定的。

---

## 二、事实核对：镜像层面到底变了什么

### 2.1 镜像清单（Registry 实测）

| 仓库 / tag | 推送时间(UTC) | manifest digest | 说明 |
|---|---|---|---|
| `adminfather/benzhi-claude-code:20260909-isolated-git` | 2026-09-09 08:53 | `sha256:f77014d9…c4d8` | **新隔离镜像**（多架构 amd64+arm64） |
| `adminfather/benzhi-claude-code:latest` | 2026-09-09 08:54 | `sha256:f77014d9…c4d8` | **与上面同一镜像**，`latest` 已漂移 |
| `adminfather/benzhi-claude-code:20260908` | 2026-09-08 05:14 | `sha256:fd9b7e6f…6b4a` | 旧模型镜像（常驻容器 + `cc <题号>`） |
| `adminfather/benzhi-claude-code:20260907` | 2026-09-07 13:13 | `sha256:efa8b12e…2b08` | 旧模型镜像 |
| `nicehey/benzhi-claude-code:1.0` | 2026-09-07 11:20 | `sha256:6857e726…1c96` | **Windows 侧只有这一个 tag，没有新镜像**；镜像基础层构建于 2026-08-25 |

关键判断：

- **Mac 有真新镜像**，且 `latest` 已经指过去。本地缓存过旧镜像的人不会自动受影响，`docker pull` 过的人会拿到新版 → 同一期不同人跑的可能是不同镜像，**必须按 digest 记账**。
- **Windows 没有新镜像**：`windows-v2.md` 是同一镜像（2026-09-07 推送的 `1.0`）的"新用法说明书"，改的是用法（挂载本题文件夹、显式传模型、`git safe.directory`），不是镜像行为。因此 Windows 侧不存在"旧命令失效"问题，只是流程要对齐 Mac。

### 2.2 新 Mac 镜像的镜像内配置（从 image config 读出）

| 项 | 旧（20260908 等） | 新（20260909-isolated-git） |
|---|---|---|
| `ENTRYPOINT` | `/usr/local/bin/entrypoint.sh` | 同左 |
| `CMD` | `bash -c "trap … ; sleep infinity & wait"`（**常驻**） | **`["interactive"]`（不常驻，直接进 Claude）** |
| `cc` 脚本 | 完整入口：建 `/workspace/<题号>`、改信任配置、`exec claude --dangerously-skip-permissions` | **77 字节转发壳**：`exec /usr/local/bin/entrypoint.sh "$@"`（题号/恢复一律报错） |
| 模型默认 | `ark/urm-01` | **`auto_model/urm`** |
| Claude Code | `npm i -g @anthropic-ai/claude-code`（不锁版） | **`@2.1.197`（锁版）** |
| 新增 ENV | — | `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`、`CLAUDE_CODE_SAFE_MODE=1`、`DISABLE_AUTOUPDATER=1` |
| 新增 LABEL | — | `org.benzhi.claude.task-mode=isolated-v1` |
| Git 工具链 | 基础层自带 git | 额外装 `git-all git-lfs openssh-client gnupg patch less jq ripgrep procps` + `git lfs install --system` |
| 工作目录 | `WORKDIR /workspace`，各题在 `/workspace/<题号>` | `WORKDIR /workspace`，**容器内恒定 `/workspace`，没有题号概念** |

### 2.3 新 Mac 镜像的 `entrypoint.sh`（镜像内原文，去注释后全文）

```bash
MODE="${1:-interactive}"
[ "$#" -le 1 ] || fail 'Extra arguments are not allowed. Create one fresh container per task.'
case "$MODE" in interactive|print) ;; *) fail 'Use interactive or print. Task numbers and session recovery are not supported.' ;; esac

TOKEN="${apikey:-${APIKEY:-${ANTHROPIC_AUTH_TOKEN:-}}}"
[ -n "$TOKEN" ] || fail 'Missing API key. Pass -e apikey=YOUR_KEY before the image name.'
[ "${HOME:-}" = /home/node ] || fail 'A clean /home/node home is required.'
[ "$(pwd)" = /workspace ] || fail 'The working directory must be /workspace.'

# A stopped container retains its files. Refuse to reuse it for another task.
(set -o noclobber; : > "$HOME/.task-session-started") 2>/dev/null \
  || fail 'This container has already been used. Export results and create a new container.'
mkdir -p "$HOME/.claude/projects"
[ -z "$(find "$HOME/.claude/projects" -mindepth 1 -print -quit)" ] || fail 'The transcript directory must be empty.'
[ ! -e "$HOME/.claude/memory" ] || fail 'A prior memory directory is not allowed.'
[ -z "$(find /workspace -mindepth 1 -print -quit)" ] \
  || fail 'The workspace must be empty when starting a new task. Import code during this session.'

export ANTHROPIC_AUTH_TOKEN="$TOKEN"
unset apikey APIKEY ANTHROPIC_API_KEY NODE_OPTIONS NODE_PATH

ARGS=(
  --safe-mode
  --disable-slash-commands
  --setting-sources ''
  --settings '{"autoMemoryEnabled":false}'
  --strict-mcp-config
  --mcp-config '{"mcpServers":{}}'
  --tools 'Bash,Read,Write,Edit,Glob,Grep'
  --dangerously-skip-permissions
)
[ "$MODE" = print ] && ARGS+=(-p --output-format stream-json --verbose)
exec claude "${ARGS[@]}"
```

---

## 三、新 Mac 镜像的 8 条硬约束 → 对现有 cc-solo 流程逐条影响

> 表中第 1、2、4、7 条的行为**已在本机实测确认**（见 7.2：非空挂载被拒、`cc`/`restart` 被哨兵拒绝、`--cap-drop ALL` 下 chown 失败、容器内写文件落到本机挂载目录、启动后播种立即可见）。

| # | 新镜像约束（原文依据） | 现有设计假设 | 影响 | 处理 |
|---|---|---|---|---|
| 1 | `/workspace` 启动时必须为空，错误信息写明 `Import code during this session.` | agent 在人工进入前用 `docker cp` 把任务副本灌进容器 | **播种步骤整段作废**：不能再"先播种后启动" | 改为**启动后、首轮提问前播种**（宿主机直接写入挂载目录），或让模型自行 clone |
| 2 | 容器只能开一次会话：`$HOME/.task-session-started` 哨兵，重复启动即 `fail`；`cc 01` / `--continue` / `--resume` 全部被拒 | 容器常驻、多题共用、可 `--continue` 续轮 | **「一个任务的几轮必须一口气做完」**：退出 Claude 或关窗后该容器不可再用 | runbook 明写"不退出"；会话中断 = 任务终止（已录入轮次仍有效）；建议 `docker run -dit` + `docker attach` 防误关窗 |
| 3 | `CMD ["interactive"]`，不再常驻；`docker run -d` 后没有 sleep 保活 | `docker run -d` 起常驻容器、`docker exec` 反复进出 | 启动方式必须改为 `docker run -it`（前台、占一个终端窗口） | 启动命令改为 `-it`，容器名带任务 ID |
| 4 | 容器内路径恒定 `/workspace`，轨迹目录恒为 `/home/node/.claude/projects/-workspace/` | 「题号 = 任务 ID = 容器工作目录名」，轨迹 `-workspace-<题号>` | 题号机制消失，**轨迹目录不再是区分题目的手段** | 题目身份改由「容器名 = 任务 ID」+「挂载源 = 任务副本目录」承载 |
| 5 | `--tools 'Bash,Read,Write,Edit,Glob,Grep'` | 标准 Claude Code 工具集（含 Task 子代理、TodoWrite、WebFetch 等） | **无子代理、无 TodoWrite、无联网抓取、无 NotebookEdit** → 「任务规划」「交付完整性」两维的难度口径变了 | 需评测方裁定 Harness 字段写法；历史数据不可混比 |
| 6 | `--disable-slash-commands` + `--safe-mode` + `--setting-sources ''` + 空 MCP + 禁记忆 | 正常 Claude Code（有 `/clear`、`/compact`、项目 CLAUDE.md） | 没有 `/exit`（改用 Ctrl+D 两次）；无 `/compact`；不读项目指令文件 | 文档改退出方式；工程化类题若依赖 CLAUDE.md 需重新设计 |
| 7 | 运行参数带 `--cap-drop ALL --security-opt no-new-privileges` | `docker exec -u root … chown -R node:node` 修权限 | **掉全部 capability，连 root 也不能 chown**（chown 需要 CAP_CHOWN） | Mac 侧删除 chown 相关说明与排错项；Mac 靠挂载归属映射即可写 |
| 8 | 单容器可多开（不同 `--name` + 不同空目录） | — | 可并行跑多题 | 作为可选能力记录，不作为默认流程 |

### 关于第 1 条的落地方式（这是最需要定的一件事）

三种播种路径，按推荐度排序：

- **A（推荐，官方口径内）**：人工执行 `docker run -it` → **先不要发消息** → agent 在宿主机把任务副本内容写进挂载目录（`docker inspect` 取挂载源，按 `.gitignore` 排除依赖包）→ agent 报 "READY" → 人工再贴首轮提示词。
  - 优点：不动镜像、可脚本化、产物天然在本机、题面与轨迹干净。
  - 代价：Claude Code 的初始 `<env>` 上下文是在空目录下建立的（系统提示里的 "Is directory a git repo" 等快照信息会偏"空"）。因为我们的任务副本**本来就不带 `.git`**，这个偏差有限；但仍应实测一次（第七节第 1 项）。
- **B（备选）**：首轮让模型自己 `git clone <baseline permalink> .`（镜像内置完整 git）。污染首轮语义、引入网络依赖，不建议作为正式数据路径，可用于应急。
- **C（需向镜像作者提需求）**：请镜像作者提供一个受支持的预置方式（允许非空挂载 / `-e SEED_DIR=` / 启动前 import 钩子）。我们的场景（**固定初始代码 + 本机可见 + agent 编排**）正是新镜像当前明确拒绝的用法，值得反馈。

---

## 四、Windows 侧的事实与判断

| 项 | 事实 | 判断 |
|---|---|---|
| 镜像 | `nicehey/benzhi-claude-code:1.0`（2026-09-07 推送，只有这一个 tag） | **没有新 Windows 镜像**；`windows-v2.md` 是同一镜像的新用法 |
| 容器模型 | `ENTRYPOINT /usr/local/bin/start-container`、`CMD sleep infinity` → 常驻，`docker exec` 进出 | 与 Mac 新镜像相反：Windows **仍可 `docker start` + `claude --continue` 续会话**（已实测 stop→start→exec 正常） |
| 挂载 | v2 文档：把「本题文件夹」挂到 `/workspace`（**允许非空**） | 比 Mac 宽松：**可以直接把任务副本目录挂进去**，连播种这一步都省了（已实测挂载与读写正常） |
| 模型 | 镜像固化 `ark/urm-01`，镜像内 `claude --version` = **2.1.236**（实测） | 必须按 v2 文档显式覆盖 5 个模型 env（否则与 Key 权限不匹配 → 403） |
| 权限 | v2 文档未提 chown；v1 文档要求 `chown -R node:node`（针对 `docker cp` 进去的文件） | ✅ **已实测**：Windows 挂载目录在容器内显示为 `-rwxrwxrwx root root`，`node` 用户可直接新建/追加文件 → **不需要 chown**；但挂载目录里带 `.git` 时会报 `fatal: detected dubious ownership in repository at '/workspace'`，**必须先执行 `git config --global --add safe.directory /workspace`**（实测确认，v2 文档这一步必需） |
| `cc` 命令 | 镜像内有 `/usr/bin/cc` | ⚠️ **那是 gcc 的 C 编译器**（实测 `which cc` → `/usr/bin/cc`），**不是** Claude 入口；写文档时要说清，别让使用者误以为有入口脚本 |
| 轨迹 | cwd = `/workspace` → `/home/node/.claude/projects/-workspace/` | 与 Mac 新镜像一致（都是 `-workspace`），这点反而统一了 |
| 审批 | 普通 `claude`，执行命令前会询问 | 与 Mac 的 `--dangerously-skip-permissions` 行为不一致 → 标注数据天然跨 OS 不同口径，需在 task-info 记录 |

顺带一个可用性提升：`windows-v2.md` 第 3.4 节明确允许"同一项目多道题承接上一题代码"（`01 → 02 → 03`），当前 `runbook.md` 第 5 步只写了"新开任务"，可以考虑把"承接产物"写成 `feature/refactor` 类型的标准变体。

---

## 五、目标执行流程（改写后）

### 5.1 统一后的角色

- **1 任务 = 1 会话 = 1 容器 = 1 本机工作目录**；容器名固定规范 **`cc-solo-{任务}`**（如 `cc-solo-app-12-bugfix-01`）。
- 容器内工作目录恒为 `/workspace`；**容器内容 = 本题任务副本内容**；轨迹恒在 `/home/node/.claude/projects/-workspace/`。
- 人工只做一件事：在容器里跟 Claude Code 对话（**不退出**）。
- agent 做：建副本/快照/出题、播种（Mac）、每轮 `docker cp` 轨迹、切片、录入、打分、导出、收容器。

### 5.2 Mac（每条命令都固定 tag，不用 `latest`）

```bash
TASK="app-12-bugfix-01"
IMAGE="adminfather/benzhi-claude-code:20260909-isolated-git"   # 固定 tag，勿用 latest
RUN_DIR="$HOME/claude-runs/${TASK}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR/workspace"

# ① 人工执行：前台进 Claude（此时目录必须为空）
docker run -it --init --restart=no --name "cc-solo-$TASK" \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$RUN_DIR/workspace,dst=/workspace" \
  -e "apikey=xxxxx" \
  "$IMAGE"
```

```bash
# ② agent 执行（人工先别发消息）：把任务副本播种进挂载目录，排除依赖包
SRC=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}' "cc-solo-$TASK")
rsync -a --exclude-from=.gitignore "<任务副本目录>/" "$SRC/"     # 无 rsync 时用 git ls-files -z | tar -c -T - 打包解包
```

```bash
# ③ 每轮结束：agent 导出轨迹（代码不需要搬，直接在本机挂载目录里）
docker cp "cc-solo-$TASK:/home/node/.claude/projects/-workspace/." \
  "<RECORD_DIR>/{项目}/{项目}-{类型}/{任务}/"

# ④ 任务结束：备份轨迹 → 回导源码到任务副本（供 git diff / 打分审阅）→ 删容器
docker cp "cc-solo-$TASK:/home/node/.claude/projects/-workspace/." "$RUN_DIR/traces"
rsync -a --exclude-from=.gitignore "$SRC/" "<任务副本目录>/"
docker rm "cc-solo-$TASK"
```

要点：**不要加 `--rm`**（轨迹在容器里，退出后容器处于 stopped，仍可 `docker cp`）；**不要 `docker start`/`docker restart`**（哨兵文件会直接拒绝）；**不要在 Mac 上写 `chown`**（cap 已掉）。

### 5.3 Windows

```powershell
$task='app-12-bugfix-01'; $model='<管理员给的完整模型名>'
$taskDir='<任务副本目录>'      # 直接挂它，不需要播种，也不需要回导
docker run -d --name "cc-solo-$task" `
  --mount "type=bind,source=$taskDir,target=/workspace" `
  -e "apikey=<key>" `
  -e "ANTHROPIC_MODEL=$model" -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" `
  nicehey/benzhi-claude-code:1.0

docker exec "cc-solo-$task" git config --global --add safe.directory /workspace
docker exec -it -w /workspace "cc-solo-$task" claude
```

每轮导出（注意容器名换成任务名，路径仍是 `-workspace`）：

```powershell
docker cp "cc-solo-$task:/home/node/.claude/projects/-workspace/." "records\app-12\app-12-bugfix\app-12-bugfix-01\"
```

> ✅ **已实测（Windows）**：挂载目录在容器内是 `-rwxrwxrwx root root`，`node` 用户可直接新建/追加文件 ⇒ **不需要 `chown`**；但挂载**带 `.git` 的仓库**时必须先执行上面那条 `git config --global --add safe.directory /workspace`，否则 `git status` 报 `fatal: detected dubious ownership in repository at '/workspace'`。容器 `stop` → `start` → `exec` 实测正常，可复用。

---

## 六、逐文件改写清单

| 文件 | 现在写的是什么 | 要改成什么 | 优先级 |
|---|---|---|---|
| `docs/CLAUDE_CODE_DOCKER_MAC.md` | 旧镜像用法（`docker run -d` + `cc 01` + `docker cp` 代码 + chown） | **归档**（移 `docs/archive/`）或在顶部加"仅适用于 `20260907`/`20260908` 标签；`latest` 已升级，本文命令会失败" | **P0** |
| `docs/CLAUDE_CODE_DOCKER_MAC.html` | 上面那份的渲染稿 | 同步归档/重新生成 | P1 |
| `docs/CLAUDE_CODE_DOCKER_MAC-v2.md` | 面向"做题"的新镜像说明 | 升格为正式 `CLAUDE_CODE_DOCKER_MAC.md`；补 cc-solo 专用小节（固定 tag、容器命名、播种时机、每轮导出、不可恢复的应对） | **P0** |
| `docs/CLAUDE_CODE_DOCKER_windows.md` | 旧用法（无挂载、`docker cp` 代码、chown） | **归档**，正文让位给 v2 | **P0** |
| `docs/CLAUDE_CODE_DOCKER_windows-v2.md` | 新用法（挂本题文件夹、模型 env、safe.directory） | 升格为正式 `CLAUDE_CODE_DOCKER_windows.md`；补"挂载目录 = 任务副本""轨迹恒为 `-workspace`""模型 env 必传"的强调 | **P0** |
| `docs/WINDOWS_DOCKER_SETUP.md` | 从 0 到导出轨迹的完整引导（旧用法，docker cp + chown） | 按 v2 用法重写或并入 Windows 文档 | P1 |
| `docs/runbook.md` | 第 1 步第 6 项 `docker cp` 播种 + chown；第 2 步 `cc <题号>`；第 3 步 `-workspace-<题号>` 导出；分工表写"agent 自动 chown" | 按 5.2 改写：播种时机后移、容器名 `cc-solo-{任务}`、轨迹路径 `-workspace`、删 chown、补"不退出/不可恢复"红线 | **P0** |
| `docs/runbook-windows.md` | 差异表把 Windows 描述为"无 cc、手动 claude、需确认"；第 1/2/3 步与 Mac 同构 | 按 5.3 改写：镜像/入口/审批三行保留，其余对齐"1 容器 = 1 任务 + 挂载任务副本"；轨迹目录 `-workspace` | **P0** |
| `SKILL.md` | 数据模型段写"容器工作目录名 = 任务名 = `/workspace/<题号>`"；目录结构段落 | 改为"容器 = 任务；`/workspace` = 本题副本内容；轨迹恒 `/home/node/.claude/projects/-workspace/`"；新增「镜像与 Harness 口径」小节（镜像 tag+digest、隔离模式、工具裁剪） | **P0** |
| `skills/01-task-create.md` | 第 53、94、156 行：容器说明与轨迹来源 `-workspace-<题号>` | 同步新路径；补"记录镜像 tag + manifest digest + 隔离模式" | P1 |
| `skills/02-round-capture.md` | 第 45、50–59、88–89、97 行：轨迹目录、导出命令、代码回导 | 轨迹目录改 `-workspace`；导出命令容器名用任务名；Mac/Windows 均**无需代码回导**（已在挂载目录） | **P0** |
| `templates/task-info.md` | 轨迹根目录字段写 `-workspace-<题号>` | 改路径；建议新增「镜像 / 镜像摘要 / 隔离模式（工具集）」字段 | P1 |
| `config.toml` | `[trajectory]` 注释、`[harness]` 注释 | 注释按新路径与新镜像；可加 `[container] image_mac / image_windows / container_name_prefix` | P1 |
| `secrets-simple.toml` | `claude_code_version_mac = "2.1.197"`（已与新镜像一致）、`windows = "2.1.236"` | Mac 无需改；Windows 用容器内 `claude --version` 复核 | P2 |
| `docs/structure-example.md` | "同一容器，结构镜像 `source-code`"、路径映射表 | 改为「每题一容器、`/workspace` = 副本内容」；映射表补"容器名 / 挂载源"列 | P1 |
| `skills/03-score-annotate.md` | 读 `records/.../<任务>-trajectory.jsonl`、读副本 git diff | 逻辑不变；若采纳 Harness 口径变更，需在依据里记录隔离模式 | P2 |
| `skills/04-export-submit.md` | 五维 + 轨迹附件投递 | 不变（Harness 版本字段的写法取决于评测方裁定） | P2 |
| `README.md` / `AGENTS.md` | 概览与项目表 | 一句话同步镜像/流程变化；AGENTS.md 的 cc-solo 工作流一行可改为"任务初始化 → 每题一容器交互 → 单轮录入 → 五维打分 → 导出" | P2 |

---

## 七、实测结果与待验证项

测试环境：本机 Windows + Docker Desktop 29.7.2（Linux 容器 / x86_64），2026-09-10。

### 7.1 已实测通过（Windows 镜像 `nicehey/benzhi-claude-code:1.0`）

| # | 结论 | 证据 |
|---|---|---|
| 1 | **可以把本机目录直接挂载为 `/workspace`，且容器内能看到已有文件** | `docker inspect` 显示 `Type=bind`、`Destination=/workspace`、`RW=true`；容器内 `ls -la /workspace` 列出挂载的 `existing.txt`、`src/` |
| 2 | **挂载文件对 `node` 用户可写，不需要 chown** | 挂载文件在容器内为 `-rwxrwxrwx root root`；`node` 用户新建 `/workspace/new.txt`（owner `node:node`）与追加写入均成功 |
| 3 | **挂载带 `.git` 的仓库必须先 `git config --global --add safe.directory /workspace`** | 全新容器内直接 `git status` → `fatal: detected dubious ownership in repository at '/workspace'`；执行 safe.directory 后正常 |
| 4 | 镜像内版本与 ENV | `claude --version` = `2.1.236`；`git version 2.39.5`；`ANTHROPIC_MODEL=ark/urm-01`、`CLAUDE_CONFIG_DIR=/home/node/.claude` 等 ENV 实际生效 |
| 5 | **常驻容器可复用** | `docker stop` → `docker start` → `docker exec` 均正常（与 Mac 隔离镜像相反） |
| 6 | `/usr/bin/cc` 是 gcc 的 C 编译器，不是 Claude 入口 | `which cc` → `/usr/bin/cc` |

### 7.2 已实测通过（Mac 隔离镜像 `adminfather/benzhi-claude-code:20260909-isolated-git`）

本地拉取后的 digest 与 Hub 一致（`sha256:f77014d9…c4d8`；直连 Docker Hub 过慢，最终经 `docker.1ms.run` 加速源拉取——注意 `docker.xuanyuan.me` 报 `toomanyrequests`）。

| # | 结论 | 证据（实测原文） |
|---|---|---|
| 1 | **非空挂载被直接拒绝** | `The workspace must be empty when starting a new task. Import code during this session.`（容器直接退出）⇒ Mac 不能"先播种后启动" |
| 2 | **空目录可启动；`docker run -dit`（后台 TTY）也能正常跑起 Claude** | `docker ps` 显示 Up；`ps -A` 可见 `claude --safe-mode --disable-slash-commands --setting-sources  --settings {"autoMemoryEnabled":false} --strict-mcp-config --mcp-config {"mcpServers":{}} --tools Bash,Read,Write,Edit,Glob,Grep --dangerously-skip-permissions`；日志有 "Bypass Permissions mode" 警告 |
| 3 | **启动后播种（宿主机写入挂载目录）容器内立刻可见** | 宿主机写入 `README.md`、`src/main.py` 后，容器内 `ls -la /workspace` 立即列出且 `cat` 成功 ⇒ 5.2 的 A 方案成立 |
| 4 | **容器内写文件会落到本机挂载目录（双向）** | 容器内 `echo hello > /workspace/seeded.txt`（rc=0）后，宿主机目录里出现 `seeded.txt` |
| 5 | **`chown` 不可用** | `docker exec -u root … chown node:node /workspace/seeded.txt` → `chown: changing ownership of '…': Operation not permitted`（rc=1）⇒ Mac 文档里的 chown 步骤必须删除 |
| 6 | **没有可用的 `docker exec` 入口** | `docker exec <c> cc` → `This container has already been used. Export results and create a new container.` |
| 7 | **停止后无法重启会话** | `docker stop` + `docker start` → 容器 `Exited (1)`，日志末行同样是 `This container has already been used. …` |
| 8 | **stopped 容器仍可 `docker cp` 轨迹目录** | `docker cp <c>:/home/node/.claude/projects <本机目录>` 成功（未发生真实对话时目录为空，符合"没对话就没轨迹"） |
| 9 | 版本与 ENV | `claude --version` = `2.1.197`；容器内 ENV 含 `CLAUDE_CODE_SAFE_MODE=1`、`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`、`DISABLE_AUTOUPDATER=1`、`ANTHROPIC_MODEL=auto_model/urm` |
| 10 | **旧文档的 `docker run -d` 用法直接失败** | `docker run -d …`（无 TTY）→ 容器 `Exited (1)`，日志 `Error: Input must be provided either through stdin or as a prompt argument when using --print`（无 TTY 时 Claude Code 转入 print 模式并因无输入报错） |

### 7.3 仍未实测（不影响流程结论）

| # | 项 | 说明 |
|---|---|---|
| 1 | `docker attach` 的 Ctrl-P Ctrl-Q 脱离按键 | 本会话无 TTY，无法注入按键；但 `-dit` 下 Claude 正常运行已确认，风险主要在 attach 客户端一侧 |
| 2 | 真实会话产生的轨迹内容与文件名 | 需要有效 Key 走完一轮；路径已由 entrypoint（`mkdir -p "$HOME/.claude/projects"`）与 `WORKDIR /workspace` 确定 |
| 3 | 工具裁剪对模型行为的实际影响强弱 | 工具集已由启动参数 `--tools Bash,Read,Write,Edit,Glob,Grep` 确证，剩余的是"影响多大"，属口径问题 |
| 4 | `print` 模式用于内部批量试跑 | 入口支持 `print`（追加 `-p --output-format stream-json --verbose`），可留作内部参考 |
| 5 | 容器内 git 推远端（凭据 / host key） | 镜像含 git-all / git-lfs / openssh / gnupg，但不内置任何账号与凭据 |

---

## 八、需要向镜像作者 / 评测方确认的问题

**给镜像作者（Windows 镜像作者 + Mac 镜像作者）**

1. **能否提供受支持的"预置代码"方式**（允许启动时非空挂载 / `-e SEED_DIR=` / 启动前 import 钩子）？现在的"`/workspace` 必须为空 + Import code during this session"与"固定初始代码 + 本机可见 + agent 编排"的标注场景直接冲突（见第三节第 1 条与 A/B/C 三条路径）。
2. `latest` 已指向隔离镜像，能否保证以后 `latest` 语义稳定？我们打算**全部改用固定 tag + digest**记账，确认无异议。
3. Windows 侧是否会出隔离版与日期 tag？目前只有 `1.0`，无法区分"同一 tag 下的新旧构建"，且默认模型仍是 `ark/urm-01`。
4. 会话"不可恢复"是硬约束还是可放开？≤10 轮的标注会话一旦误关窗即报废，成本很高。
5. `--tools 'Bash,Read,Write,Edit,Glob,Grep'` 是否可配置？若可放开 `Task`/`TodoWrite`，标注口径更接近"标准 Claude Code"。

**给评测方（口径裁定）**

6. Harness 字段怎么写：`Claude Code` + 版本 `2.1.197`，是否要注明隔离模式（`isolated-v1`，工具集受限）？
7. 2026-09-09 之前采集的 Mac 数据与之后的数据**能否混在同一批提交**？（镜像、工具集、斜杠命令、模型默认值都变了）
8. 五维中「任务规划」在无 TodoWrite/子代理的环境下如何自洽（是否调整该维度的判据）。

---

## 九、风险与缓解

| 风险 | 说明 | 缓解 |
|---|---|---|
| 会话中断即报废 | Mac 新镜像不可 `--continue`，误关窗/误 Ctrl+C = 该任务无法继续（**已实测**：`stop` 后再 `start` 直接被哨兵拒绝） | 每轮结束就导出轨迹（已录入轮次不丢，最多损失当前轮）；建议 `-dit` + `attach` 包裹（`-dit` 下 Claude 正常运行已实测）；`task-info.md` 备注"会话提前终止" |
| 旧文档误导 | `latest` 已升级，旧 Mac 文档的命令会失败 | 立刻归档旧 Mac 文档（P0），所有命令固定 tag |
| 数据可比性 | 09-09 前后 Harness/镜像不同 | 每条数据记镜像 digest + 隔离模式；必要时分批提交 |
| 依赖包污染 | 挂载后模型 `npm install` 直接写进本机副本/运行目录 | 播种与回导都按 `.gitignore` 排除；任务结束后清理 `node_modules`/`.venv` 等 |
| 容器堆积 | 每题一容器、且必须保留到导出完成 | 导出确认后 `docker rm`；agent 用 `docker ps -a --filter name=cc-solo-` 盘点 |
| Key 泄漏 | Key 出现在启动命令与容器配置中 | 不截图、不共享命令；分享前脱敏 |

---

## 十、一页速查（改完之后应当长这样）

```text
1 任务 = 1 会话 = 1 容器（cc-solo-{任务}）= 1 本机工作目录
容器内：/workspace（= 本题副本内容）  轨迹：/home/node/.claude/projects/-workspace/
Mac    ：docker run -it …:20260909-isolated-git  → 启动后播种 → 不退出 → 每轮 cp 轨迹 → rm
Windows：docker run -d + 挂载任务副本 + 5 个模型 env → exec claude → 每轮 cp 轨迹 → stop/rm
不用：cc <题号>、chown、docker cp 代码、docker start 续跑、latest
```
