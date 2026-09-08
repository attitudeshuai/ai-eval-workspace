# Claude Code 使用（Windows：安装 Docker → 运行容器 → 导出轨迹）

> 本文讲 Windows 上 **Claude Code 的 Docker 环境**：从安装 Docker Desktop，到拉镜像、启动容器、进容器交互，最后把对话轨迹导出到本机。标注流程的逐步指令见 [runbook-windows.md](runbook-windows.md)；Docker 排障细节见 [CLAUDE_CODE_DOCKER_windows.md](CLAUDE_CODE_DOCKER_windows.md)。

整个流程一句话：**装 Docker Desktop → 拉镜像并启动容器 → 进容器跑 Claude → 导出轨迹。**

---

## 目录

1. [需要准备的东西](#一需要准备的东西)
2. [第 1 步：安装 Docker Desktop](#二第-1-步安装-docker-desktop)
3. [第 2 步：确认 Linux 容器模式 + 配置镜像加速器](#三第-2-步确认-linux-容器模式--配置镜像加速器)
4. [第 3 步：拉取镜像并启动容器](#四第-3-步拉取镜像并启动容器)
5. [第 4 步：把仓库放进容器 + 进入容器启动 Claude](#五第-4-步把仓库放进容器--进入容器启动-claude)
6. [第 5 步：与 Claude 对话（权限确认 + 会话处理）](#六第-5-步与-claude-对话权限确认--会话处理)
7. [第 6 步：导出轨迹](#七第-6-步导出轨迹)
8. [常见问题（踩坑速查）](#八常见问题踩坑速查)
9. [命令速查卡](#九命令速查卡)

---

## 一、需要准备的东西

- 一台 Windows 电脑（Win10 2004 及以上 / Win11），**CPU 支持虚拟化**（VT-x/AMD-V，BIOS 里开启）。
- 一个 **API Key**，形如 `sk-xxxxxxxxxxxxxxxx`，由管理员单独发放、每人不同。
- 镜像里已固化网关地址和模型默认值；**API Key 等同于密码**，别发群、别进 Git、别截图外传。

> 网关地址、模型名等都已固化在镜像里，无需自己配。仅当你手上的 Key 能访问的模型与镜像默认不一致时，才需要启动时用环境变量覆盖（见第 3 步的「模型覆盖」）。

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

### 4.1 首次启动容器

把下面的 `你的Key` 换成管理员发的 Key（只复制 Key 本身，不要带 `apikey:`、`model:`、空格换行），在 PowerShell 执行：

```powershell
docker run -d --name benzhi-claude-code -e "apikey=你的Key" nicehey/benzhi-claude-code:1.0
```

首次会自动从镜像源拉取（约 1~2GB），看到下载进度等待完成；结束后输出一串容器 ID 即启动成功。

> ⚠️ **模型覆盖（很关键）**：若镜像固化的模型不是你的 Key 可访问的模型（进容器后 `claude` 会报 `403 key not allowed to access model`），启动时把所有模型环境变量一起覆盖成网关允许的模型名。以 `auto_model/urm` 为例：

```powershell
docker run -d --name benzhi-claude-code `
  -e "apikey=你的Key" `
  -e "ANTHROPIC_MODEL=auto_model/urm" `
  -e "ANTHROPIC_DEFAULT_OPUS_MODEL=auto_model/urm" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=auto_model/urm" `
  -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=auto_model/urm" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=auto_model/urm" `
  nicehey/benzhi-claude-code:1.0
```

> 模型名以网关/管理员发放为准。可先 `docker exec benzhi-claude-code printenv ANTHROPIC_MODEL` 看镜像固化值，再决定是否覆盖。

### 4.2 确认容器在运行

```powershell
docker ps
```

应能看到 `benzhi-claude-code` 一行，`STATUS` 为 `Up`。已停止则 `docker start benzhi-claude-code`。

> 若容器名不是 `benzhi-claude-code`（比如 `benzhi-claude-code-test-20260907`），后面所有命令里的 `benzhi-claude-code` 都替换成实际名字。**不要重复创建**，已存在就 `docker start`。

---

## 五、第 4 步：把仓库放进容器 + 进入容器启动 Claude

### 5.1 把本地代码放进容器（首次做该题时）

在 PowerShell 执行（把 `<REPO>` 换成题号 = 仓库目录名，下面用 `html-demo` 示例）：

```powershell
docker exec benzhi-claude-code mkdir -p /workspace/html-demo
docker cp "D:/你的/仓库/路径/html-demo/." benzhi-claude-code:/workspace/html-demo/
docker exec -u root benzhi-claude-code chown -R node:node /workspace/html-demo
```

- 第二条末的 `/.`：**复制目录内容**（否则会把目录本身嵌套成 `/workspace/html-demo/html-demo/`）。
- 第三条 `chown` 把文件归属改为容器内用户 `node`，否则 Claude 只能读不能改（改文件报 `Permission denied`）。连着执行；忘了就补这一条。

### 5.2 进入容器并启动 Claude（每次使用）

```powershell
docker exec -it -w /workspace/html-demo benzhi-claude-code bash
```

看到 `node@…:/workspace/html-demo$` 提示符后，在容器里执行：

```bash
claude
```

首次进入会询问界面主题/是否信任当前目录，选信任即可。

---

## 六、第 5 步：与 Claude 对话（权限确认 + 会话处理）

- **命令审批**：本镜像未启用免确认模式，Claude 每次执行命令/改文件前会询问，**确认后选「允许」**。
- **一题一个会话窗口（一个 SessionID）**：几轮对话必须落在**同一个**会话里。

推荐做法：
1. **不退出**，一个 `claude` 会话里连续发多轮（第 1 轮粘贴首轮提示词，后续直接在同一个会话里发「继续 / 再改成…」），SessionID 不变。
2. **导出轨迹另开一个 PowerShell 窗口**，不用退出 Claude（见第 6 步）。
3. **若确实要退出**：Claude 里 `/exit` → 容器提示符再 `exit`。下次继续时**不要用裸 `claude`**（会新建 SessionID），改用 `claude --continue`（恢复当前目录最近会话，同 SessionID）或 `claude --resume <SessionID>`。

---

## 七、第 6 步：导出轨迹

**推荐在另一个 PowerShell 窗口执行**（与 Claude 会话互不干扰，无需退出 Claude），把容器内的轨迹导出到本机：

```powershell
docker cp benzhi-claude-code:/home/node/.claude/projects/-workspace-html-demo/. "D:/你的/本地/记录目录/html-demo/"
```

- 轨迹目录名：工作目录 `/workspace/html-demo` 对应容器内 `-workspace-html-demo`（工作目录里的非字母数字都替换成横线）。
- **导出时机**：等 Claude 把当前这轮答完、处于等待输入的静止状态再拷（别在它正跑工具时拷）。
- **保留整个文件夹结构**，别只挑一个 JSONL（可能还有子代理记录、工具输出）。

**不确定轨迹目录名**时先列一下：

```powershell
docker exec benzhi-claude-code ls -1 /home/node/.claude/projects
```

导出的轨迹文件交给后续标注流程解析（`jsonl` 里的 `sessionId` 即 SessionID，一条 user 键入 = 一轮）。

---

## 八、常见问题（踩坑速查）

**PIPE 连不上引擎**：`failed to connect to the docker API at npipe://… dockerDesktopLinuxEngine … The system cannot find the file specified`。Docker Desktop 没启动/未就绪。打开 Docker Desktop，等 `docker info` 返回 `ServerVersion`，确认 Linux 容器模式，再执行 `docker run`。

**直连 Docker Hub 拉镜像超时**：`dialing registry-1.docker.io:443 … connection attempt failed`。国内网络访问 Docker Hub 不通。或配了 `registry-mirrors`，或改用加速地址拉取再打回标准标签：

```powershell
docker manifest inspect docker.1ms.run/nicehey/benzhi-claude-code:1.0   # 探测该加速源是否有镜像
docker pull docker.1ms.run/nicehey/benzhi-claude-code:1.0
docker tag docker.1ms.run/nicehey/benzhi-claude-code:1.0 nicehey/benzhi-claude-code:1.0
```

**进容器后 Claude 报 403 key not allowed to access model**：`can only access models=['auto_model/urm']. Tried to access ark/urm-01`。镜像固化模型与 Key 可访问模型不一致。重建容器时把所有模型环境变量覆盖成网关允许的模型（见第 3 步）。

**容器名已被占用（name is already in use）**：容器已创建过，用 `docker start benzhi-claude-code`，不要再 `docker run`。

**Claude 改文件报 Permission denied**：`docker cp` 进来的文件归属不对。补执行 `docker exec -u root benzhi-claude-code chown -R node:node /workspace/html-demo`。

**导出时提示找不到目录**：先确认已在对应工作目录启动 Claude、发过消息（才会生成轨迹），再核对实际轨迹目录名（`docker exec benzhi-claude-code ls -1 /home/node/.claude/projects`）。

---

## 九、命令速查卡

| 用途 | 命令 |
|---|---|
| 首次启动容器（含模型覆盖，推荐） | `docker run -d --name benzhi-claude-code -e "apikey=你的Key" -e "ANTHROPIC_MODEL=auto_model/urm" -e "ANTHROPIC_DEFAULT_OPUS_MODEL=auto_model/urm" -e "ANTHROPIC_DEFAULT_SONNET_MODEL=auto_model/urm" -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=auto_model/urm" -e "CLAUDE_CODE_SUBAGENT_MODEL=auto_model/urm" nicehey/benzhi-claude-code:1.0` |
| 启动已停止的容器 | `docker start benzhi-claude-code` |
| 查看容器 | `docker ps` / `docker ps -a` |
| 把仓库放进容器 | `docker exec benzhi-claude-code mkdir -p /workspace/<REPO>` + `docker cp <本地路径>/. benzhi-claude-code:/workspace/<REPO>/` + `docker exec -u root benzhi-claude-code chown -R node:node /workspace/<REPO>` |
| 进入容器 | `docker exec -it -w /workspace/<REPO> benzhi-claude-code bash` |
| 启动/恢复会话 | `claude`（新）/ `claude --continue`（恢复最近）/ `claude --resume <SessionID>` |
| 导出轨迹 | `docker cp benzhi-claude-code:/home/node/.claude/projects/-workspace-<REPO>/. <本机路径>` |
| 看轨迹目录名 | `docker exec benzhi-claude-code ls -1 /home/node/.claude/projects` |
| 看模型 | `docker exec benzhi-claude-code printenv ANTHROPIC_MODEL` |
| 看版本 | `docker exec benzhi-claude-code claude --version` |
| 删除容器（会丢数据，先导出） | `docker rm -f benzhi-claude-code` |
| 停止容器（数据保留） | `docker stop benzhi-claude-code` |
| 看日志 | `docker logs benzhi-claude-code` |
