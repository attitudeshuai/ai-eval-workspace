# Claude Code 使用说明（Windows）

这份说明介绍如何在 Windows 电脑上在Docker中使用 Claude Code。你只需要打开 Docker Desktop，准备好管理员提供的 key 和完整 model 名称，然后按顺序完成“准备本题文件夹、创建本题容器、开始对话、取出轨迹”这几个步骤。

**一道题使用一个独立文件夹和一个新容器。** 同一道题中断后可以继续使用自己的容器；换一道题时，必须新建文件夹和容器。每题复用同一个干净镜像，不需要重新安装 Claude Code。代码和导出的轨迹放在哪个盘，由你自己选择。

> 📌 **本文是 cc-solo 标注的 Windows 现行用法**。旧版（不挂载宿主目录、用 `docker cp` 把代码搬进容器再 `chown`）说明已归档到 [archive/CLAUDE_CODE_DOCKER_windows.md](archive/CLAUDE_CODE_DOCKER_windows.md)；镜像升级的影响评估见 [image-upgrade-review.md](image-upgrade-review.md)。注意：**Windows 侧镜像没有换**，仍是 `nicehey/benzhi-claude-code:1.0`，换的是用法。
>
> **标注场景的额外约定：**
>
> - **容器名 = 任务名**：本文示例的 `benzhi-claude-01` 请改为 `cc-solo-{任务}`（如 `cc-solo-app-12-bugfix-01`），后续所有命令同步替换。
> - **挂载的就是任务副本**：`--mount "type=bind,source=<…\source-code\{项目}\{项目}-{类型}\{任务}>,target=/workspace"`。容器内容 = 任务副本内容，因此**不需要 `docker cp` 把代码放进容器，也不需要把代码回导** —— 模型改完的产物直接就在本机副本目录里。
> - **模型 env 必传 5 个**：镜像固化的模型名（`ark/urm-01`）可能与 Key 权限不匹配（否则报 403 `key not allowed to access model`）。
> - **依赖包会写进本机副本目录**：模型执行 `npm install`/`pip install` 后产物直接落在本机；按 `.gitignore` 排除，任务结束后清理，别把依赖提交进快照。
> - `chown` 只在容器内改文件报 `Permission denied` 时才需要补一条（`docker exec -u root "cc-solo-{任务}" chown -R node:node /workspace`），不再作为标准步骤。
> - **审批模式（可对齐 Mac）**：默认普通 `claude` 会逐条询问；加 `--dangerously-skip-permissions` 即免确认，与 Mac 镜像内置的免确认口径一致（等价 `--permission-mode bypassPermissions`）。同一批数据须统一，并把实际审批模式记进 `task-info.md`。
> - 轨迹目录恒为 `/home/node/.claude/projects/-workspace/`（工作目录就是 `/workspace`），导出命令见第五节；第二题导出只需换容器名与保存名。



## 快速开始

如果你以前用过 Docker，可以按下面三步操作。如果是第一次接触，建议跳到“需要准备的东西”，按后面的详细步骤往下做。

**1. 准备本题文件夹，创建本题容器。**

先在自己选择的位置新建本题文件夹，例如 `01`。有现成代码就放入本题需要的代码和附件；从零开始开发则保持为空。打开 `01` 文件夹，在资源管理器的地址栏输入 `powershell`，按 Enter。不要从包含全部题目的总文件夹打开窗口。

执行 `Get-Location`，确认显示的是本题文件夹。下面前三行分别填写本题的容器名、key 和 model；容器名不能与其他题目重复。其余配置会自动引用这些值：

```powershell
$containerName = 'benzhi-claude-01'
$apiKey = '这里填写本次使用的key'
$model = 'ark/urm-01'

docker run -d --name $containerName `
  --mount "type=bind,source=$($PWD.Path),target=/workspace" `
  -e "apikey=$apiKey" `
  -e "ANTHROPIC_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" `
  nicehey/benzhi-claude-code:1.0

docker ps --filter "name=$containerName"
```

最后一条命令会显示容器状态。找到本题容器，确认 `STATUS` 列中有 `Up`，再进行下一步。请将创建命令作为完整的多行命令粘贴；行末的反引号用于连接下一行，后面不要添加空格。

**2. 进入本题容器里的 Claude。**

下面以容器 `benzhi-claude-01` 为例。如果你使用了其他容器名，后面的进入、导出、启动和停止命令都要替换成实际名称。在 PowerShell 中逐条执行：

```powershell
docker exec benzhi-claude-01 git config --global --add safe.directory /workspace

# 默认：逐条确认权限
docker exec -it -w /workspace benzhi-claude-01 claude

# 免确认（自动模式）：跳过全部权限询问，行为与 Mac 镜像一致
docker exec -it -w /workspace benzhi-claude-01 claude --dangerously-skip-permissions
```

默认 `claude` 会在每次执行命令/改文件前询问；加 `--dangerously-skip-permissions`（等价 `--permission-mode bypassPermissions`）即免确认。已经开着的会话想切换：`/exit` 后用 `claude --dangerously-skip-permissions --continue` 重进，SessionID 不变。

出现 Claude 的输入框后，就可以输入本题需求。换题时，新建文件夹 `02`，在 `02` 中重新完成第 1 步，使用新容器名 `benzhi-claude-02` 并填写本次 key 和 model，再进入新容器。每个容器内的工作目录都保持 `/workspace`。

**3. 退出 Claude，取出轨迹。**

对话结束后，在 Claude 中输入 `/exit`。接着，在所有题目代码文件夹以外选一个位置保存轨迹。打开这个保存位置，在地址栏输入 `powershell` 并按 Enter，然后逐条执行：

```powershell
$exportDir = Join-Path (Get-Location).Path ("题01-轨迹-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
docker cp benzhi-claude-01:/home/node/.claude/projects/-workspace/. "$exportDir"
```

确认命令没有报错、保存位置中已出现轨迹文件夹后，继续在这个 PowerShell 窗口中执行：

```powershell
Compress-Archive -LiteralPath "$exportDir" -DestinationPath "$exportDir.zip"
Invoke-Item .
```

最后一条命令会打开保存位置。打开 ZIP，确认原始 JSONL 和相关子文件夹已包含在内，再按要求提交。先保留本题容器，导出成功前不要删除。第二题导出时改用容器 `benzhi-claude-02` 和保存名称 `题02-轨迹-`，容器内的轨迹路径不变。有关轨迹内容和异常情况，见第五章。



## 目录

1. [需要准备的东西](#一需要准备的东西)
2. [第 1 步：启动容器](#二第-1-步启动容器)
3. [第 2 步：进入对话](#三第-2-步进入对话)
4. [第 3 步：与 Claude 对话](#四第-3-步与-claude-对话)
5. [第 4 步：取出轨迹文件](#五第-4-步取出轨迹文件)

## 一、需要准备的东西

### 1. 确认 Docker Desktop 已打开

请让 Docker Desktop 保持运行。本文不再介绍安装过程，后面会直接创建容器。

操作时会用到两个输入位置：**Docker 命令粘贴到 Windows PowerShell，任务需求输入到 Claude。** 每一步都会说明该在哪里输入；如何打开 PowerShell，下一章会具体介绍。

### 2. 准备本次的 key 和 model

打开管理员发来的消息，分别找到 key 和完整 model 名称。复制 key 时只选中 key 那一串字符，不要把前面的 `apikey:`、后面的模型名称或换行一起复制进去。model 也要单独填写完整，例如 `ark/urm-01`，不要加上 `model:` 前缀。

每次创建容器都会明确填写这两项。以后收到新 key 或新 model，就在下一次创建命令的 `$apiKey`、`$model` 两行中替换。不要自行猜测模型名称，新 key 也需要有调用该模型的权限。



### 3. 了解代码和轨迹分别存在哪里

你可以先建一个总文件夹，再在里面给每道题各建一个任务文件夹。例如，总文件夹叫 `claude-workspace`，里面放 `01`、`02`。总文件夹仅用于你整理文件，不交给任何一道题的容器使用。放在哪个盘、叫什么名字，都可以自己决定。

**一个任务文件夹就是一个 workspace，也就是 Claude 做这道题时使用的工作目录。** 本文用 `01`、`02` 演示操作，它们只是文件夹名称，并不对应某份已有的题目。

```text
本机 claude-workspace/01/  <-> 容器 benzhi-claude-01 的 /workspace
本机 claude-workspace/02/  <-> 容器 benzhi-claude-02 的 /workspace
```

创建容器后，本题文件夹会与本题容器里的 `/workspace` 连在一起，这就叫“目录映射”。例如，本机 `01` 中的文件只交给 `benzhi-claude-01`，Claude 修改它后，你在本机也能立即看到结果，不需要来回复制。两个容器里的 `/workspace` 名字相同，实际对应不同的本机文件夹。

为避免跨题读取历史内容，每题都从本文指定的镜像新建容器，不挂载个人主目录、Claude 配置目录、Codex 的 skills 目录或其他题目的目录，也不共用保存 Claude 状态的数据卷。不要把做过题的容器另存为镜像后用于新题。只放入题目规定的资料；如果调用方主动把经验写进题面，容器隔离本身无法阻止这种传入。

删除文件也是一样的：Claude 删除了任务文件夹里的代码，本机的那份也会被删除。因此，重要代码要提前备份，或者用 Git 保存版本。

对话轨迹的保存方式与代码不同。轨迹留在容器内部，需要在做完题后用 `docker cp` 取出来，第五章会介绍具体操作。只停止容器不会丢失轨迹，但删除容器前一定要先导出。

另外，选择代码文件夹的位置，只决定代码存在哪个盘。镜像和容器内部文件存在哪里，仍由 Docker Desktop 的存储设置决定。

## 二、第 1 步：启动容器

### 1. 选择保存代码的位置

先准备本题专用的文件夹，再从这个文件夹创建容器。请按下面的顺序操作：

1. 打开文件资源管理器，找到你想保存代码的位置。D 盘、E 盘或其他本地磁盘都可以。
2. 可以先建一个名为 `claude-workspace` 的总文件夹，再在里面新建本题文件夹 `01`；也可以直接在其他位置新建 `01`。路径中不要使用逗号。
3. 双击打开本题文件夹 `01`，放入本题需要的初始代码和附件。从零开发则保持为空。不要停留在包含所有题目的总文件夹。
4. 点击窗口上方显示路径的地址栏，输入 `powershell`，再按 Enter。注意是地址栏，不是旁边的搜索框。
5. PowerShell 窗口打开后，输入下面的命令，再按 Enter：

```powershell
Get-Location
```

命令会显示当前所在的文件夹。请核对它是不是本题的 `01` 文件夹；如果不是，关闭这个 PowerShell 窗口，回到正确的文件夹，重新按第 4 项打开。不要把另一道题已使用的文件夹当作新题目录。

### 2. 填写容器名、key 和 model，创建容器

保持刚才的 PowerShell 窗口打开。先修改下面前三行：`$containerName` 填本题的新容器名，`$apiKey` 填本次 key，`$model` 填管理员提供的完整 model 名称。本文使用 `benzhi-claude-01` 和 `ark/urm-01` 演示；更换模型时只需修改 `$model` 这一处。

把下面内容完整粘贴到 PowerShell 执行。保留英文引号和行末反引号，反引号后面不能有空格：

```powershell
$containerName = 'benzhi-claude-01'
$apiKey = '这里填写本次使用的key'
$model = 'ark/urm-01'

docker run -d --name $containerName `
  --mount "type=bind,source=$($PWD.Path),target=/workspace" `
  -e "apikey=$apiKey" `
  -e "ANTHROPIC_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" `
  nicehey/benzhi-claude-code:1.0
```

命令中的 `$($PWD.Path)` 会自动使用刚才核对过的文件夹路径，不用手动填写盘符或用户名。保留外面的英文引号，路径里有中文或空格时也可以使用。

五个模型配置项都引用 `$model`，会一起覆盖镜像中的主模型、Opus/Sonnet/Haiku 别名和子代理默认模型，避免只换了主模型而其他调用仍使用旧默认值。不要把这些配置行删减成只传 `model=...`，现有镜像不识别这个简写。

第一次运行需要下载镜像，可能要等几分钟。等命令执行完、窗口重新出现可以输入命令的提示符后，再输入下面这一行，检查容器是否已经启动：

```powershell
docker ps --filter "name=$containerName"
```

在结果中找到本题容器。如果它的 `STATUS` 列显示 `Up`，说明容器启动成功，可以继续往下做；这一步还不能证明 key 和 model 可以正常请求网关。如果找不到容器，或者出现报错，先按第七章排查。

**每道新题都执行一次创建流程。** 换题时，从新的题目文件夹打开 PowerShell，使用新的容器名，并重新核对 key 和 model。三个 PowerShell 变量只存在于当前窗口，另开窗口时需要重新填写；容器创建后会保存当时传入的配置。

### 3. 检查 Docker 是否用对了文件夹

在 PowerShell 中执行：

```powershell
docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' benzhi-claude-01
```

结果中应该只有本题需要的目录映射：箭头左边是本题的 `01` 文件夹，右边是 `/workspace`。如果左边是所有题目的总文件夹，或者出现了 Claude 配置、其他题目等不应共享的目录，先按第七章“本机文件没有出现在容器里”处理。

Docker 会记住这个位置。以后可以从其他地方打开 PowerShell 来进入本题容器，但请保留本题文件夹原来的位置，不要直接移动或重命名它。后文以 `benzhi-claude-01` 为例，使用其他容器名时请同步替换。

## 三、第 2 步：进入对话

### 1. 检查本题资料

完成第二章后，本题文件夹和容器都已创建。回到资源管理器，打开本题的 `01` 文件夹，检查准备交给 Claude 的资料。

如果这次是从零开发，`01` 保持为空即可。如果要修改已有项目，放入题目要求的 README、源码、配置文件，以及需要保留的 `.git` 等资料。打开 `01` 后，应该能直接看到项目文件，而不是还要再进入一层同名项目文件夹。

不要把以前做题产生的 memory、skills、聊天轨迹、参考答案或个人配置混入本题资料，尤其要检查隐藏目录和项目内的 `.claude`、`.agents`、`.codex`。题目正式提供的指令或配置应按题目要求保留，不能仅凭文件名一律删除。

复制重要代码前，先做好备份或保存 Git 提交。如果不想用 `01`，也可以另起名字，建议使用英文字母、数字和短横线。每道新题都要建一个新文件夹和新容器，即使几道题属于同一个项目，也要分开。

### 2. 进入 Claude

在 Windows PowerShell 中逐条执行：

```powershell
docker exec benzhi-claude-01 git config --global --add safe.directory /workspace
docker exec -it -w /workspace benzhi-claude-01 claude
```

第一条命令是告诉 Git，本题工作目录可以信任，避免之后出现 `dubious ownership` 报错。每个新容器首次使用时执行一次即可。如果仓库还在更深一层的文件夹里，处理方法见第七章。

第二条命令会打开 Claude，让它在本题容器的 `/workspace` 中工作，对应本机的 `01`。第一次进入新容器时，可能会让你选择主题、确认是否信任当前文件夹。确认显示的路径是 `/workspace`，再按提示选择。出现对话输入框后，就可以按下一章发送需求了。

如果使用其他容器名，只替换命令中的 `benzhi-claude-01`，容器内的 `/workspace` 不随本机文件夹名称改变。`-w` 只是指定容器内工作目录，不能更换挂载的本机目录，也不能把旧容器变成新题容器。

### 3. 换任务时怎么操作

做完当前任务后，在 Claude 中输入 `/exit`，按第五章导出并检查本题轨迹。然后在 PowerShell 执行 `docker stop benzhi-claude-01`，停止本题容器，先保留它作为备份。

在本机 `01` 旁边新建 `02`，不要把它建到 `01` 里面。放入下一题规定的代码和附件；从零开发则保持为空。打开 `02`，从地址栏启动 PowerShell，执行 `Get-Location` 确认位置，再填写下一题的配置并创建新容器：

```powershell
$containerName = 'benzhi-claude-02'
$apiKey = '这里填写本次使用的key'
$model = 'ark/urm-01'

docker run -d --name $containerName `
  --mount "type=bind,source=$($PWD.Path),target=/workspace" `
  -e "apikey=$apiKey" `
  -e "ANTHROPIC_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_OPUS_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_SONNET_MODEL=$model" `
  -e "ANTHROPIC_DEFAULT_HAIKU_MODEL=$model" `
  -e "CLAUDE_CODE_SUBAGENT_MODEL=$model" `
  nicehey/benzhi-claude-code:1.0

docker ps --filter "name=$containerName"
```

确认新容器状态为 `Up`，并按第二章检查目录映射后，再逐条执行：

```powershell
docker exec benzhi-claude-02 git config --global --add safe.directory /workspace
docker exec -it -w /workspace benzhi-claude-02 claude
```

第二题使用 `benzhi-claude-02` 内的 `/workspace`，对应本机 `02`，有自己独立的 Claude 配置和会话记录。不要进入 `benzhi-claude-01` 做第二题，也不要把第一题的 `.claude` 配置或数据卷接到新容器。

两个容器复用同一个基础镜像，但各自保存运行中安装的软件和产生的本地状态。第一题临时安装的软件不会自动出现在第二题容器中，需要按新题项目要求准备。保持只挂载本题目录，才能避免把其他题目的文件带进来。

### 4. 同一个项目有多道题，应该怎么做

同一项目有多道题，也使用不同的本机文件夹和容器。只有题目明确要求承接上一题代码时，才把需要的代码转移过去；独立题目应从本题规定的初始版本开始。

例如，你围绕同一个网站连续做三道题，可以这样安排：

- `01`：从零开发网站，保留第一题完成时的代码。
- `02`：从第一题的代码开始，修复登录问题。
- `03`：从第二题的代码开始，增加搜索功能。

**承接代码不等于承接旧容器或历史经验。** 以上面的第二题为例，按下面的顺序操作：

1. 第一题完成后，在 Claude 中输入 `/exit`。按第五章导出第一题的轨迹，并保存好代码；如果项目使用 Git，先提交当前结果。
2. 执行 `docker stop benzhi-claude-01`，保留第一题容器。在本机新建空的 `02`，不要覆盖 `01`。
3. 只把第二题需要的代码和资料复制到 `02`；需要保留 `.git` 时按题目要求保留。同时检查隐藏文件和目录，避免复制上一题自动生成的 memory、skills、参考答案、个人规则或轨迹。题目正式要求的配置照常保留。
4. 打开 `02`，从地址栏启动 PowerShell，按上一节创建 `benzhi-claude-02`，填写本次 key 和 model，检查映射并进入新容器。
5. 直接发送第二题的完整需求，例如：“请阅读当前项目，修复以下登录问题……”，并写清复现步骤和预期结果。不要使用 `--continue` 或 `--resume` 接着做另一道题。
6. 第二题完成后，按第五章导出它的轨迹。导出命令使用容器 `benzhi-claude-02`，保存名称使用 `题02-轨迹-`；容器内的路径仍是 `/home/node/.claude/projects/-workspace`。

这样，`01` 留下第一题代码，`02` 从题目允许的代码继续开发，两题的配置和对话记录分别留在各自容器里。修改 `02` 不会自动更新 `01`。

准备第三题时，新建 `03` 和 `benzhi-claude-03`，按同样的方法准备允许的资料并开始新对话。只有继续做同一道题时，才返回它原来的容器，并按需要使用 `--continue`。

## 四、第 3 步：与 Claude 对话

### 1. 发送需求

进入 Claude 后，在底部的输入框中写下你希望它完成的任务，按 Enter 发送。比如，想让它写一个简单脚本，可以这样说：

```text
请在当前目录创建 hello.py，运行后输出 Hello，并执行它确认结果。
```

上面这句话仅用于演示。正式做题时，请直接发送实际题目，不要先在这道题的文件夹里试聊，以免把测试对话混入正式轨迹。

Claude 工作时可能询问是否允许修改文件或执行命令。看清它准备做什么，再按界面提示确认。

想看生成的代码，直接在本机打开这道题的文件夹即可。文件已经保存在那里，不需要再从容器复制一遍。

### 2. 退出对话

等待本次回答结束，在 Claude 输入框中输入：

```text
/exit
```

按 Enter 后，Claude 会关闭，你会回到 Windows PowerShell。到这里就已经退出对话了，不需要再输入 `exit`。本题容器仍在后台运行，可以导出轨迹或继续这道题；不能用于另一道题。

### 3. 下次进入或继续会话

需要返回第一题时，打开 Docker Desktop 和 Windows PowerShell，执行：

```powershell
docker start benzhi-claude-01
docker exec -it -w /workspace benzhi-claude-01 claude
```

这两条命令会启动第一题原来的容器，并在其 `/workspace` 中打开一次新对话，之前的代码仍然保留。返回第二题时改用 `benzhi-claude-02`，目录仍是 `/workspace`。

如果你想接着上一次的对话往下做，先确保容器已经启动，再用下面这条命令进入：

```powershell
docker exec -it -w /workspace benzhi-claude-01 claude --continue
```

如果这个文件夹里有多次历史对话，想自己选择恢复哪一次，可以执行：

```powershell
docker exec -it -w /workspace benzhi-claude-01 claude --resume
```

这里恢复的是本题的对话记录，代码仍然是文件夹里当前的版本。正式做题时，还要遵守任务对对话轮次的要求；换题必须另建文件夹和容器，从新对话开始。



## 五、第 4 步：取出轨迹文件

### 1.  结束对话，选择导出位置

1. 等 Claude 回答结束后，在它的输入框中输入 `/exit`，按 Enter。
2. 打开资源管理器，在自己想用的磁盘上新建一个保存轨迹的文件夹。请把它放在所有题目代码文件夹以外，不要再挂载给其他题目的容器。
3. 打开这个新文件夹，在地址栏输入 `powershell`，按 Enter。
4. 执行 `Get-Location`，确认显示的是刚才选好的轨迹保存位置。

后面的命令会把轨迹保存到这里。你从哪个文件夹打开这个 PowerShell 窗口，轨迹就导出到哪个文件夹。

### 2. 查看轨迹目录

在 Windows PowerShell 中执行：

```powershell
docker exec benzhi-claude-01 ls -1 /home/node/.claude/projects
```

查看第一题的具体文件：

```powershell
docker exec benzhi-claude-01 ls -lht /home/node/.claude/projects/-workspace
```

本机文件夹名称不影响本文的默认轨迹路径。如果曾从 `/workspace` 的子目录另开 Claude，会产生其他项目记录目录，请用第一条命令查看，并一并导出属于本题的记录。只有实际产生过对话才会有轨迹。查看命令需要容器处于运行状态；已经停止时，可以先启动本题容器查看，`docker cp` 本身也可以从停止的容器复制文件。

### 3. 取出当前题目的轨迹

假设要取出的是 `01` 的轨迹，继续在刚才打开的 PowerShell 窗口中逐条执行：

```powershell
$exportDir = Join-Path (Get-Location).Path ("题01-轨迹-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
docker cp benzhi-claude-01:/home/node/.claude/projects/-workspace/. "$exportDir"
```

第一条命令准备本次导出的文件夹名称，第二条命令把轨迹复制进去。成功后，你选择的保存位置中会多出一个类似 `题01-轨迹-20260908-153000` 的文件夹。名字带有导出时间，方便与之前的记录区分。

要导出第二题，改两处：保存名称中的 `题01-轨迹-` 改成 `题02-轨迹-`，第二条命令中的容器名改成 `benzhi-claude-02`。容器内的 `-workspace` 路径保持不变。

如果上一节发现本题还有其他项目记录目录，应把它们分别复制到 `$exportDir` 下不同的子文件夹，避免同名文件覆盖；不要遗漏子代理记录或关联的工具输出文件。

