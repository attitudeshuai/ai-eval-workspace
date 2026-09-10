# Claude Code 使用（Windows：安装 Docker → 运行容器 → 导出轨迹）

> 本文讲 Windows 上 **Claude Code 的 Docker 环境**：从安装 Docker Desktop，到拉镜像、启动容器、进容器交互，最后把对话轨迹导出到本机。**本文的容器用法已更新为「一道题一个容器 + 挂载本题文件夹」**（容器名 `cc-solo-{任务}`，挂载目录即工作目录 `/workspace`，不再 `docker cp` 代码、不写 chown）。标注流程的逐步指令见 [runbook-windows.md](runbook-windows.md)；Docker 排障细节见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)。

整个流程一句话：**装 Docker Desktop → 拉镜像并启动容器 → 进容器跑 Claude → 导出轨迹。**

---

## 目录

1. [需要准备的东西](#一需要准备的东西)
2. [第 1 步：安装 Docker Desktop](#二第-1-步安装-docker-desktop)
3. [第 2 步：确认 Linux 容器模式 + 配置镜像加速器](#三第-2-步确认-linux-容器模式--配置镜像加速器)
4. [第 3 步：拉取镜像并启动容器](#四第-3-步拉取镜像并启动容器)
5. [第 4 步：进入容器启动 Claude（挂载目录 = 工作目录）](#五第-4-步进入容器启动-claude挂载目录--工作目录)
6. [第 5 步：与 Claude 对话（权限确认 + 会话处理）](#六第-5-步与-claude-对话权限确认--会话处理)
7. [第 6 步：导出轨迹](#七第-6-步导出轨迹)
8. [常见问题（踩坑速查）](#八常见问题踩坑速查)
9. [命令速查卡](#九命令速查卡)

---

## 一、需要准备的东西

- 一台 Windows 电脑（Win10 2004 及以上 / Win11），**CPU 支持虚拟化**（VT-x/AMD-V，BIOS 里开启）。
- 一个 **API Key**，形如 `sk-xxxxxxxxxxxxxxxx`，由管理员单独发放、每人不同。
- 镜像里已固化网关地址和模型默认值；**API Key 等同于密码**，别发群、别进 Git、别截图外传。

> 网关地址等已固化在镜像里，但**模型名必须用 5 个环境变量显式覆盖**为你 Key 可访问的完整模型名（见第 3 步）——否则可能报 `403 key not allowed to access model`。

---

## 二、第 1 步：安装 Docker Desktop

1. 到官网下载 Windows 安装包：**https://www.docker.com/products/docker-desktop/**（选 Windows 版 `Docker Desktop Installer.exe`）。
2. 双击安装程序，按提示下一步（保持默认勾选即可，含「Use WSL 2 instead of Hyper-V」）。
3. 安装完成后，从开始菜单启动 **Docker Desktop**。
4. 首次启动可能提示**启用 WSL2** 或要求**重启电脑**，按提示操作。
   - 若提示 WSL 未安装/未启用，可在 PowerShell（管理员）执行 `wsl --install` 后重启。
   - 确认 BIOS 里虚拟化（VT-x / AMD-V）已开启，否则 Docker 无法启动。
5. 启动后等右上角/托盘图标稳定，状态显示 running。

**确认安装成功**，打开 PowerShell 执行：

```powershell
docker version
```

**client / server 两段都能显示版本号即成功**（`server` 为空说明引擎还没就绪，回去等 Docker Desktop 启动完）。再进一步：

```powershell
docker info
```

能返回 `ServerVersion` 就绪了。

> 若报 `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; The system cannot find the file specified`，说明 **Docker Desktop 没启动或引擎未就绪**，回到本步启动它并等 `docker info` 出结果。

---

## 三、第 2 步：确认 Linux 容器模式 + 配置镜像加速器

### 3.1 Linux 容器模式

本镜像是 Linux 容器（linux/amd64），Docker Desktop 默认就是 Linux 容器模式。若不小心切到了 Windows 容器模式，点托盘 Docker 图标 → 若显示「Switch to Linux containers」则点击切换。

### 3.2 国内网络镜像加速器（强烈建议先配）

直连 Docker Hub 在国内通常很慢或超时。在 Docker Desktop 配置镜像加速器：

1. 点托盘 Docker 图标 → **Settings** → **Docker Engine**。
2. 在右侧 JSON 的大括号内加 `registry-mirrors`，保存形如：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

> ⚠️ JSON 语法：各项间英文逗号，最后一项后不能有逗号。语法错 Docker 会标红拒绝保存。只新增 `registry-mirrors`，原有内容别删。

3. 点 **Apply & restart**，等 Docker 重启完成。

---

## 四、第 3 步：拉取镜像并启动容器

### 4.1 准备本题文件夹（挂载源）

每道题一个文件夹、一个容器。在本题文件夹里放入需要的代码和附件（从零开发则保持为空），然后在资源管理器地址栏输入 `powershell` 打开窗口，执行 `Get-Location` 确认当前就在本题文件夹内。**这个文件夹会被挂载为容器的 `/workspace`，Claude 直接在其中工作。**

### 4.2 启动容器（挂载本题文件夹 + 5 个模型 env）

填好三处：`$task` 填任务名（容器名会是 `cc-solo-$task`，如 `cc-solo-app-12-bugfix-01`），`$apiKey` 填管理员发的 Key，`$model` 填管理员给的完整模型名。在 PowerShell 执行：

```powershell
$task='app-12-bugfix-01'
$apiKey='你的Key'
$model='管理员给的完整模型名'

docker run -d --name "cc-solo-$task" `
  --mount "type=bind,source=$($PWD.Path),target=/workspace" `
  -e "apikey=$apiKey" `
  -e "ANTHROPIC_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" `
  nicehey/benzhi-claude-code:1.0

docker ps --filter "name=cc-solo-$task"
```

- `--mount` 把当前 PowerShell 所在文件夹（本题文件夹）挂载为容器的 `/workspace`。**挂载的就是模型工作目录**：Claude 改的文件直接落回本机，**不需要 `docker cp` 把代码放进容器，也不需要把代码回导**。
- **5 个模型 env 必须一起传**，覆盖镜像固化的模型名，避免与 Key 权限不匹配报 `403 key not allowed to access model`。
- 第一次运行会自动下载镜像（约 1~2GB），看到下载进度等待完成。最后一条 `docker ps` 里找到本题容器、`STATUS` 为 `Up` 即成功。

### 4.3 确认容器在运行与挂载正确

```powershell
docker ps
docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' "cc-solo-$task"
```

`docker inspect` 结果里应只有一条映射：箭头左边是本题文件夹，右边是 `/workspace`。如果左边是所有题目的总文件夹，或出现了不该共享的目录，先按第八章「本机文件没有出现在容器里」处理。

> 容器名统一 `cc-solo-{任务}`，每题一个、互不重复；同题中断后可用 `docker start "cc-solo-$task"` 续用。**换题必须新建文件夹和容器**，不要拿旧容器做别的题。

---

## 五、第 4 步：进入容器启动 Claude（挂载目录 = 工作目录）

挂载已经由第 3 步的 `--mount` 完成（本题文件夹 ↔ 容器 `/workspace`），**无需再把代码放进容器**。在 PowerShell 逐条执行：

```powershell
docker exec "cc-solo-$task" git config --global --add safe.directory /workspace
docker exec -it -w /workspace "cc-solo-$task" claude
```

- 第一条告诉 Git 信任 `/workspace`，避免 `dubious ownership` 报错；每个新容器首次执行一次即可。
- 第二条打开 Claude，在容器 `/workspace`（= 本机本题文件夹）里工作。首次进入会询问界面主题/是否信任当前目录，选信任即可（确认路径是 `/workspace`）。

---

## 六、第 5 步：与 Claude 对话（权限确认 + 会话处理）

- **命令审批**：默认未启用免确认模式，Claude 每次执行命令/改文件前会询问，**确认后选「允许」**。
- **想开免确认（自动模式）**：进入时加 `--dangerously-skip-permissions` —— `docker exec -it -w /workspace "cc-solo-$task" claude --dangerously-skip-permissions`（容器内是 `node` 非 root，可用）。同一批数据要么全开、要么全不开；已经开着的会话可 `/exit` 后用 `claude --dangerously-skip-permissions --continue` 重进，SessionID 不变。
- **一题一个会话窗口（一个 SessionID）**：几轮对话必须落在**同一个**会话里。

推荐做法：
1. **不退出**，一个 `claude` 会话里连续发多轮（第 1 轮粘贴首轮提示词，后续直接在同一个会话里发「继续 / 再改成…」），SessionID 不变。
2. **导出轨迹另开一个 PowerShell 窗口**，不用退出 Claude（见第 6 步）。
3. **若确实要退出**：Claude 里 `/exit` 一次即回到 PowerShell，**容器保留**（常驻容器，不会随退出销毁）。下次继续**同一道题**时，进容器后**不要用裸 `claude`**（会新建 SessionID），改用 `claude --continue`（恢复当前目录最近会话，同 SessionID）或 `claude --resume <SessionID>`。

---

## 七、第 6 步：导出轨迹

**推荐在另一个 PowerShell 窗口执行**（与 Claude 会话互不干扰，无需退出 Claude），把容器内的轨迹导出到本机记录目录：

```powershell
docker cp "cc-solo-$task:/home/node/.claude/projects/-workspace/." "records\app-12\app-12-bugfix\app-12-bugfix-01\"
```

- 轨迹目录恒为 `/home/node/.claude/projects/-workspace/`（工作目录就是 `/workspace`），**与题号无关**；换题只换容器名 `cc-solo-$task` 和保存目录。
- **导出时机**：等 Claude 把当前这轮答完、处于等待输入的静止状态再拷（别在它正跑工具时拷）。
- **保留整个文件夹结构**，别只挑一个 JSONL（可能还有子代理记录、工具输出）。

**不确定轨迹目录名**时先列一下：

```powershell
docker exec "cc-solo-$task" ls -1 /home/node/.claude/projects
```

导出的轨迹文件交给后续标注流程解析（`jsonl` 里的 `sessionId` 即 SessionID，一条 user 键入 = 一轮）。

> **代码不需要回导**：模型改的代码已在本机挂载的本题文件夹里。任务结束后只需按 `.gitignore` 清理模型新装的依赖包（`node_modules`/`.venv`/`__pycache__` 等），别把依赖提交进快照。

---

## 八、常见问题（踩坑速查）

**PIPE 连不上引擎**：`failed to connect to the docker API at npipe://… dockerDesktopLinuxEngine … The system cannot find the file specified`。Docker Desktop 没启动/未就绪。打开 Docker Desktop，等 `docker info` 返回 `ServerVersion`，确认 Linux 容器模式，再执行 `docker run`。

**直连 Docker Hub 拉镜像超时**：`dialing registry-1.docker.io:443 … connection attempt failed`。国内网络访问 Docker Hub 不通。或配了 `registry-mirrors`，或改用加速地址拉取再打回标准标签：

```powershell
docker manifest inspect docker.1ms.run/nicehey/benzhi-claude-code:1.0   # 探测该加速源是否有镜像
docker pull docker.1ms.run/nicehey/benzhi-claude-code:1.0
docker tag docker.1ms.run/nicehey/benzhi-claude-code:1.0 nicehey/benzhi-claude-code:1.0
```

**进容器后 Claude 报 403 key not allowed to access model**：`can only access models=['auto_model/urm']. Tried to access ark/urm-01`。镜像固化模型与 Key 可访问模型不一致。重建容器时把 5 个模型环境变量都覆盖成网关允许的完整模型名（见第 3 步）。

**容器名已被占用（name is already in use）**：同名容器已创建过。同题继续用 `docker start "cc-solo-$task"`；换题请用新的 `$task` 和新的挂载文件夹，不要拿旧容器做别的题。

**本机文件没有出现在容器里 / Claude 看不到题目文件**：检查挂载是否指向本题文件夹：`docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' "cc-solo-$task"`，确认左边是本题文件夹、右边是 `/workspace`。

**Claude 改文件报 Permission denied**：挂载目录的文件归属不对（少见）。仅在实测报错时才补：`docker exec -u root "cc-solo-$task" chown -R node:node /workspace`，不作为标准步骤。

**导出时提示找不到目录**：先确认已在 `/workspace` 启动 Claude、发过消息（才会生成轨迹），再核对实际轨迹目录（`docker exec "cc-solo-$task" ls -1 /home/node/.claude/projects`）。

---

## 九、命令速查卡

| 用途 | 命令 |
|---|---|
| 启动本题容器（挂载 + 5 模型 env） | `docker run -d --name "cc-solo-$task" --mount "type=bind,source=$($PWD.Path),target=/workspace" -e "apikey=你的Key" -e "ANTHROPIC_MODEL=$model" -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" nicehey/benzhi-claude-code:1.0` |
| 启动已停止的容器（同题） | `docker start "cc-solo-$task"` |
| 查看容器 | `docker ps` / `docker ps -a` |
| 进入 Claude | `docker exec "cc-solo-$task" git config --global --add safe.directory /workspace` + `docker exec -it -w /workspace "cc-solo-$task" claude` |
| 启动/恢复会话（同题） | `claude`（新）/ `claude --continue`（恢复最近）/ `claude --resume <SessionID>` |
| 导出轨迹 | `docker cp "cc-solo-$task:/home/node/.claude/projects/-workspace/." "records\app-12\app-12-bugfix\app-12-bugfix-01\"` |
| 看轨迹目录名 | `docker exec "cc-solo-$task" ls -1 /home/node/.claude/projects` |
| 看模型 | `docker exec "cc-solo-$task" printenv ANTHROPIC_MODEL` |
| 看版本 | `docker exec "cc-solo-$task" claude --version` |
| 删除容器（会丢轨迹，先导出） | `docker rm -f "cc-solo-$task"` |
| 停止容器（数据保留） | `docker stop "cc-solo-$task"` |
| 看日志 | `docker logs "cc-solo-$task"` |
