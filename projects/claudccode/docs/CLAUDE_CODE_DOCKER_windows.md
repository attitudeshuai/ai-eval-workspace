# Claude Code 使用说明（Windows）

我们使用 Docker，是为了让大家使用相同的 Claude Code 版本、配置和基础运行环境，减少各自安装、配置时出现的差异。使用前，需要先安装并打开 Docker Desktop。

Claude Code 实际运行在你自己电脑上的 Docker 容器中，不是在 Docker Hub 上运行。Docker Hub 只负责提供镜像下载；模型请求通过已配置的网关发送到远端服务。

Docker Desktop 已经打开后，按下面的步骤操作即可。Claude 客户端、网关和模型已经配好；首次创建容器需要邮件中的个人 key。业务项目的语言依赖和数据库等条件仍需按项目准备。

下文用 `/workspace/my-project` 作为容器内工作目录的示例，请替换成实际需要使用的路径。workspace 就是工作目录；新建目录不会自动获取代码，也不会重置已有代码。

整个流程是：**启动容器 → 进入工作目录 → 与 Claude 对话 → 导出轨迹。**

本教程只说明镜像和客户端操作。
## 1. 打开命令窗口

1. 在桌面新建一个文件夹，命名为 `Claude资料`，然后打开它。
2. 点击文件夹窗口顶部的地址栏，输入 `powershell`，按 Enter。
3. 弹出的窗口就是接下来输入命令的地方。每复制一条命令，都按一次 Enter 执行。

后面导出的文件会放在这个 `Claude资料` 文件夹里。

## 2. 启动容器（第一次使用时操作）

如果机器已经配置过镜像，先在 PowerShell 查看现有容器：

```powershell
docker ps -a --format "{{.Names}} | {{.Image}} | {{.Status}}"
```

找到使用 `nicehey/benzhi-claude-code:1.0` 的目标容器后，复用该容器。下文命令里的 `benzhi-claude-code` 都要替换成实际名称。例如容器名是 `benzhi-claude-code-test-20260907`，就统一使用这个名字。确认已有可用容器时，跳过下面的 `docker run`，需要时执行 `docker start 实际容器名`。不要因为示例名称不同而重复创建容器。

没有可用容器时再创建：

复制下面这条命令，把 `xxxxx` 换成邮件中的完整 key，保留两边的英文引号，再按 Enter：

```powershell
docker run -d --name benzhi-claude-code -e "apikey=xxxxx" nicehey/benzhi-claude-code:1.0
```

只复制 key 本身，不要带上 `apikey:`、`model:`、空格或换行。

第一次运行会自动从 Docker Hub 下载镜像。看到下载进度时，等待完成，不要关闭窗口。下载结束后，会出现一长串字母和数字，随后回到可以输入命令的状态。

**这时容器已在后台启动，还没有进入 Claude。继续下一步即可。以后使用已有容器，不需要再次执行 `docker run`。**

镜像来自公开仓库 [nicehey/benzhi-claude-code](https://hub.docker.com/r/nicehey/benzhi-claude-code)，正常情况下不需要登录 Docker Hub。镜像用于 Windows 上的 Linux 容器，架构为 x64。

## 3. 进入工作目录，启动 Claude

在 **Windows PowerShell** 中逐条执行：

```powershell
docker exec benzhi-claude-code mkdir -p /workspace/my-project
docker exec -it -w /workspace/my-project benzhi-claude-code bash
```

`mkdir -p` 在目录不存在时创建目录，已存在时保留其中的文件。`-w` 指定进入容器后的工作目录。

看到提示符类似 `node@一串字符:/workspace/my-project$`，说明已经进入指定目录。输入下面的命令启动 Claude：

```bash
claude
```

首次启动可能会询问界面主题、显示安全提示，或询问是否信任当前目录。用方向键选择，按 Enter 确认；信任提示中的路径应当与实际工作目录一致。

看到 Claude 的输入框后，输入需求并发送。在专门用于练习的目录中，也可以用这句话测试：

> 请创建 hello.py，让它输出“你好，Claude”，然后运行这个文件。

如果 Claude 询问是否允许创建文件或执行命令，确认操作内容后再选择是否允许。

同一容器中的不同工作目录共用运行环境，不会隔离依赖、进程或文件访问权限。

## 4. 退出 Claude，回到 Windows

这里需要退出两次，请按顺序操作。

1. 等 Claude 回答完，在 **Claude 的对话框**中输入下面这条命令，按 Enter：

```text
/exit
```

2. 回到 `node@…:/workspace/my-project$` 这样的**容器提示符**后，再输入下面这条命令，按 Enter：

```bash
exit
```

3. 看到以 `PS` 开头、包含 Windows 路径的提示符，就回到了电脑上的 PowerShell 窗口。

退出对话不会删除容器，代码和记录仍保存在容器里。

## 5. 导出工作目录对应的轨迹

在 **Windows PowerShell** 中执行下面这条命令。不要在 Claude 对话框或容器里执行。

```powershell
docker cp benzhi-claude-code:/home/node/.claude/projects/-workspace-my-project/. ./my-project-traces
```

复制完成后：

1. 回到桌面上的 `Claude资料` 文件夹。
2. 打开 **`my-project-traces`** 文件夹，就能看到 `.jsonl` 轨迹文件，以及可能存在的同名会话文件夹。
3. 需要打包时，右键点击整个 `my-project-traces` 文件夹，选择“压缩为 ZIP 文件”；Windows 10 可选择“发送到 → 压缩(zipped)文件夹”。

**请保留整个文件夹结构，不要只挑一个 JSONL 文件。** 会话文件夹中可能还有子代理记录和工具输出。

这条命令复制 `/workspace/my-project` 对应的轨迹目录。如果在这个工作目录中开过多个会话，记录会一起导出，不会自动筛选为当前会话。

工作目录名称变化时，导出命令也要同步修改。复制前可先查看实际轨迹目录：

```powershell
docker exec benzhi-claude-code ls -1 /home/node/.claude/projects
```

示例中 `/workspace/my-project` 对应 `-workspace-my-project`。实际名称以查询结果为准，不要直接套用示例路径。

## 6. 再次使用已有容器

打开 Docker Desktop，再打开 PowerShell。将下面的容器名和工作目录替换成实际值，逐条执行：

```powershell
docker start benzhi-claude-code
docker exec -it -w /workspace/my-project benzhi-claude-code bash
```

确认提示符中的工作目录正确，再执行：

```bash
claude
```

上述命令使用已存在的工作目录，其中的代码会保留。需要进入另一个目录时，按第 3 步准备相应路径，再修改 `-w` 后的路径。普通 `claude` 命令开启新会话；需要恢复历史会话时，使用下一节的命令。

## 如何恢复历史会话

客户端支持恢复历史会话。打开 Docker Desktop，再按第 1 步打开 PowerShell，逐条执行：

```powershell
docker start benzhi-claude-code
docker exec -it -w /workspace/my-project benzhi-claude-code bash
```

进入后确认路径是原会话的工作目录，再输入：

```bash
claude --continue
```

这会恢复当前工作目录中最近一次的会话。如果同目录启动过多个会话，先核对 SessionID，可使用 `claude --resume 实际SessionID` 指定恢复目标。

恢复会话不需要再次执行 `docker run` 或重新填写 key，也不会自动把工作目录中的文件恢复到历史版本。代码仍以当前目录的实际文件为准。

## 备份容器中的全部代码和轨迹

重新创建容器之前，可以在 Windows PowerShell 中执行下面两条命令，备份全部项目轨迹和 `/workspace` 下的文件：

```powershell
docker cp benzhi-claude-code:/home/node/.claude/projects/. ./all-projects-traces
docker cp benzhi-claude-code:/workspace/. ./all-projects-code
```

这会包含多个工作目录及其会话记录，也包括直接放在 `/workspace` 下的文件。确认备份完整后再处理旧容器。如果之前已有同名备份文件夹，先换一个新的目标文件夹名。保存在其他路径的项目文件需要另行备份。

## 常见问题

**提示容器名字已经被使用（name is already in use）**

说明之前已经创建过容器，先核对目标容器，再使用 `docker start` 启动并进入相应工作目录，不需要再次执行 `docker run`。

**提示容器没有运行（container is not running）**

先执行 `docker start benzhi-claude-code`，再执行进入容器的命令。若仍无法进入，执行 `docker logs benzhi-claude-code` 查看启动错误。

**镜像下载失败，或提示无法连接 Docker**

确认 Docker Desktop 引擎已经启动，并处于 Linux 容器模式。下载超时需要检查访问 Docker Hub 的网络；出现 `toomanyrequests` 时，可登录 Docker Desktop 后重试。

**启动 Docker 后，容器命令仍报「The system cannot find the file specified」（PIPE 连不上引擎）**

报错形如 `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; The system cannot find the file specified`。意思是 `docker` 命令找不到正在运行的引擎，通常是 **Docker Desktop 没启动，或启动了但引擎还没就绪**。

处理：

1. 打开 Docker Desktop，等它启动完成、状态变为 running（Windows 任务栏/托盘图标稳定）。
2. 用 `docker info` 确认能返回 `ServerVersion` 再继续；`docker version` 的 server 段非空即就绪。
3. 确认处于 **Linux 容器模式**（本镜像为 linux/amd64，Windows 上须用 Linux 容器）。
4. 重新执行 `docker run` 即可。

**直连 Docker Hub 拉镜像超时 / 报网络错误**

报错形如 `failed to resolve reference "docker.io/nicehey/benzhi-claude-code:1.0": … dialing registry-1.docker.io:443 … connection attempt failed`，是国内网络直连 Docker Hub 不通的典型表现。

处理（任选其一）：

1. 配置镜像加速器：Docker Desktop → Settings → Docker Engine → 在 JSON 里加 `"registry-mirrors": ["https://docker.1ms.run", "https://docker.xuanyuan.me"]` → Apply & restart。
2. 不改配置，直接用加速地址拉取再打回标准标签：
   ```powershell
   docker manifest inspect docker.1ms.run/nicehey/benzhi-claude-code:1.0   # 先探测该加速源是否有此镜像
   docker pull docker.1ms.run/nicehey/benzhi-claude-code:1.0
   docker tag docker.1ms.run/nicehey/benzhi-claude-code:1.0 nicehey/benzhi-claude-code:1.0
   ```
   之后文档里的 `docker run … nicehey/benzhi-claude-code:1.0` 依然可用。

**进容器后 Claude 报「key not allowed to access model」（403）**

报错形如 `403 key not allowed to access model. This key can only access models=['auto_model/urm']. Tried to access ark/urm-01`。说明镜像里固化的模型名和你的 Key 实际可访问的模型对不上。

处理：重建容器，把所有模型相关环境变量覆盖成网关允许的模型名（以 `auto_model/urm` 为例）：

```powershell
docker rm -f benzhi-claude-code
docker run -d --name benzhi-claude-code `
  -e "apikey=你的Key" `
  -e "ANTHROPIC_MODEL=auto_model/urm" `
  -e "ANTHROPIC_DEFAULT_OPUS_MODEL=auto_model/urm" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=auto_model/urm" `
  -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=auto_model/urm" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=auto_model/urm" `
  nicehey/benzhi-claude-code:1.0
```

模型名以管理员发放为准；可先用 `docker exec benzhi-claude-code printenv ANTHROPIC_MODEL` 看镜像固化值，再决定是否覆盖。

**提示 key 中有换行（Invalid auth token / contains a line break）**

这表示复制 key 时混入了换行或多余内容，请求还没有发出去。例如，报错中的 `contains a line break at character 26` 表示第 26 个字符处有换行。

按下面的步骤重新填写：

1. 如果 Claude 正在重试，先按 `Esc` 停止重试。在 Claude 对话框中输入 `/exit`，按 Enter，回到类似 `node@容器编号:/workspace/my-project$` 的容器提示符。
2. 在**容器内的 Bash 终端**中执行下面这条命令。把引号里的内容替换成正确 key，保留两边的英文单引号；不要在 Windows PowerShell 中执行。

```bash
export apikey='这里替换成完整的单行key'
```

**只复制 key 本身，不要带上 `apikey:`、`model: ark/urm-01`、空格或换行。整条命令应在同一行。** 网关和模型已经在镜像里配好，无需粘贴。

3. 在同一个容器终端中重新启动 Claude，再发送问题：

```bash
claude
```

**这个修复只对当前容器终端及其启动的 Claude 有效。** 退出容器终端后，重新执行 `docker exec` 会使用创建容器时保存的旧 key。

要永久改正，先按“备份容器中的全部代码和轨迹”一节导出轨迹和代码，确认备份完整，再使用正确 key 重新创建容器。仅停止、重启旧容器不会更新 key；不要在备份前删除旧容器。

**Claude 提示 401 或认证失败**

先检查 key 后面是否误粘贴了 `model: ark/urm-01` 等文字。把这些文字放进 `export apikey='…'` 的引号里，会使整个值变成错误的 key。按照上面的临时修复步骤，重新填写只有 key 的单行内容后再试。

如果确认复制正确后仍提示 401，请负责人核对 key 是否有效或过期。更换 key 同样需要注意上面的临时修复与永久改正的区别。

**Claude 提示 429，且显示 No deployments available for selected model**

这是网关暂时没有可用的模型部署。先等待客户端本次自动重试结束，保存报错时间和完整错误。此时重装镜像或改用本机 Claude 不能保证解决问题，也不要自行更换规定的模型。

连续重试仍失败时，导出本次轨迹和代码，向服务负责人反馈模型名称、错误和发生时间，不发送 key。服务恢复后再重试，保留原失败记录；答题场景下如何安排重试见《做题流程》。

**复制轨迹时提示找不到目录**

先确认已经在相应工作目录中启动 Claude、发送过问题，并按第 4 步正常退出。再按第 5 步查询实际轨迹目录，检查复制命令中的路径是否正确。仅创建空目录或启动容器，还不会产生对话轨迹。

**Claude 在容器中提示找不到 docker 命令**

这个镜像提供 Claude 客户端，默认没有容器内 Docker 命令或宿主机 Docker 引擎访问权限。需要验证项目的 Dockerfile 时，应在能够访问 Docker 引擎的环境中，按项目文档执行 `docker build`、`docker run` 等命令。不要把“容器里没有 Docker”当作已经完成镜像构建验证。

**已经启动业务容器，但重启后旧地址无法访问**

使用随机映射端口时，重启后应重新执行 `docker port 业务容器名` 查询地址，不能假定端口保持不变。固定映射端口时也应确认端口未被其他程序占用。这里检查的是业务容器，不是运行 Claude 的容器。

---

统一网关：`https://llm.jzxhnh.com`；统一模型：`ark/urm-01`。不需要另行安装 Claude Code 或填写这些配置。

key 会保存在本机容器配置和输入过的命令中。不要分享带有真实 key 的命令、截图或容器配置，分享轨迹前也应检查是否包含凭据。
