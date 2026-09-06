# SWE\-like Repo 出题规范（试行）

人员画像：1年以上开发者，有长期使用的开源Repo，且熟悉Vibe Coding

模型与终端：Trae CN（推荐 TraeX）或 mini\-swe\-agent \+ Seed Evolving

交付形态：一题一个 zip，目录名即题目名称，伪Harbor形式交付

**不可以从Issues里照抄需求**

**本批次只收Python和Go语言的题目**

# Changelog

|日期|事项|
|---|---|
|0904|1. 规范与校验脚本新增对Mini\-swe Agent下跑题的支持<br>2. 收录标准从200轮调整至100轮，单价不变<br>3. 新增TraeX steps统计脚本，大家可自行确认轨迹长度|

# 1\. 交付结构

```Bash
<题目名称>/
├── task.toml                 # 底稿字段，见第 2 节
├── instruction.md            # 需求 Prompt 原文
├── environment/
│   └── Dockerfile           # 题目环境，需要包含因需求导致的依赖组件
├── tests/
│   └── nl_rubric.yaml       # 自然语言rubrics
├── solution/                 # 本批允许留空
└── evidence/                 # 一次运行的取证，见第 4 节
    ├── trajectory.jsonl      # Trae IDE 可交 trajectory.md
    ├── model.patch           # Diff Patch
    └── screenshots/          # 证明材料，如截图等
```

1. **task\.toml** 题目的背景信息，键与底稿列一一对应，见第 2 节。填好后用脚本一键回填底稿，见第 7 节，不要自行增删或改名。

2. **instruction\.md** 给模型的需求，写法与反例见第 3 节

3. **environment/Dockerfile: **使用`public.ecr.aws/x8v8d7g8/mars-base:latest`作为基线image，同时进行Git操作以及依赖安装，需要注意因为需求导致的新增依赖也需要打包至dockerfile中。骨架见下方代码块，完整样例见 [deep\-swe fastapi 题](https://github.com/datacurve-ai/deep-swe/blob/main/tasks/fastapi-implicit-head-options/environment/Dockerfile)

```Docker
FROM public.ecr.aws/x8v8d7g8/mars-base:latest
WORKDIR /app

# BASE_SHA 必须与 task.toml 的 base_commit 完全一致（40 位完整 SHA）
ARG REPO_URL=
ARG BASE_SHA=
RUN git clone "$REPO_URL" . \
 && DEFAULT="$(git remote show origin | sed -n 's/.*HEAD branch: //p')" \
 && git checkout -B "$DEFAULT" "$BASE_SHA" \
 && git remote remove origin \
 && for b in $(git for-each-ref --format='%(refname:short)' refs/heads | grep -vx "$DEFAULT"); do git branch -D "$b" || true; done \
 && for t in $(git tag); do git merge-base --is-ancestor "$t" HEAD 2>/dev/null || git tag -d "$t"; done \
 && git reflog expire --expire=now --all \
 && git gc --prune=now

# 装本仓库依赖，含本题需求新增的依赖；能钉版本就钉，避免上游漂移让老题构建失败
# Python:  RUN pip install --no-cache-dir -e ".[all]"
# Go:      RUN go mod download

CMD ["bash"]
```

4. **tests/nl\_rubric\.yaml** 承载自然语言判分标准，格式见第 5 节。至少各包含 1 条 `f2p`（原本做不对、新需求下应该做对）和 1 条 `p2p`（原本就能做对、新需求下也应该做得对），整体不少于 5 条。

5. **solution/** 本批允许留空

6. **evidence/** 一次运行的取证：Trae 轨迹、diff patch 和截图等补充材料，生成方式见第 4 节

# 2\. task\.toml 与底稿字段

task\.toml 只承载下表 16 个键，填好后用脚本一键回填底稿，见第 7 节；不要自行增删或改名。除 `submitter` 外，每个键对应一个底稿列。

|task\.toml 键|底稿列|说明|
|---|---|---|
|`title`|题目名称|与 zip 目录名一致|
|`submitter`|不回填|底稿「提交人」是人员列，脚本不回填；请在底稿里圈自己|
|`submit_date`|提交日期|YYYY\-MM\-DD|
|`language`|主要语言|本批次只可填 Python、Go|
|`task_type`|任务类型|功能新增、Bug 修复、测试增强、重构/性能、配置/工具链、其他|
|`repo_url`|Repo URL||
|`base_commit`|Commit/版本|40 位完整 SHA，须与 Dockerfile 的 ARG BASE\_SHA 一致|
|`realism_and_difficulty`|真实性与难度说明|真实性与难度证明写在这里|
|`modules`|可能涉及模块||
|`trae_session_id`|Trae Session ID|harness 填 miniswe 时可留空|
|`effective_turns`|有效轮数|整数（有效 TC 口径）；Trae CN/Trae 用 Hook 取有效 TC，TraeX 用 count\_steps\.py 自查，miniswe 取轨迹里的 api\_calls，见第 7 节|
|`harness`|Harness|Trae、TraeX、miniswe|
|`seed_model`|Seed 模型/版本||
|`requirement_met`|是否完成需求|完成、部分完成、未完成、无法判断|
|`run_result`|产物结果|逐条对应 rubric，每条一行：rubric id \+ 通过 / 未通过 \+ 未通过时的原因|
|`notes`|备注|可留空|

```TOML
title       = "FastAPI 可配置的隐式 HEAD 与自动 OPTIONS"
submitter   = "ABC"
submit_date = "2026-09-03"
language    = "Python"
task_type   = "功能新增"
repo_url    = "https://github.com/fastapi/fastapi"
base_commit = "11614be9021aa4ac078d4d0693a8b5250a1010d8"

realism_and_difficulty = """
这是 Web 框架中真实的 HTTP 方法语义与路由能力，涉及 app、router、include 和单路由四层配置继承；
既要处理显式方法覆盖，又要保持 OpenAPI、CORS、依赖执行、响应头和既有路由行为。改动跨构造接口、
路由注册、请求分发、文档生成和中间件，容易产生全局回归。
"""

modules = "fastapi/applications.py、fastapi/routing.py、fastapi/middleware/methods.py、OpenAPI 生成、Starlette 路由分发，以及对应测试与文档"

trae_session_id = "0197f2c18d3a4b6e9c512f7ab0e4d9c3"
effective_turns = 137
harness         = "TraeX"
seed_model      = "Seed Evolving"
requirement_met = "未完成"

run_result = """
1 通过
2 通过
3 未通过 HEAD 响应丢失 content-length
4 未通过 OPTIONS 的方法顺序与 operations 内容错误
5 未通过 新增参数未用 Annotated[..., Doc(...)]，公开签名文档不完整
6 通过
7 未通过 既有 PATCH / TRACE 路由回归为 405
"""

notes = ""
```

底稿另有 7 列不在 task\.toml 里。前 3 列由脚本从包内文件回填，后 4 列由质检填写，提交人都不需要管。

|底稿列|来源|说明|
|---|---|---|
|需求 Prompt（原文）|包内 `instruction.md`|全文回填，不得截断或改写|
|Verify Rubric|包内 `tests/nl_rubric.yaml`|按 id 顺序拼接，每条前缀 \[f2p\] / \[p2p\]|
|交付包（zip）|整题 zip|唯一的附件列，整包上传，不再单独传 Dockerfile 或 evidence|
|Reviewer|质检填写|复核人姓名|
|静态内容是否通过质检|质检填写|通过 / 不通过|
|题目是否可运行|质检填写|通过 / 不通过|
|质检备注|质检填写|质检结论的补充说明|

# 3\. instruction\.md（需求 Prompt）

给模型的唯一输入，同时回填底稿「需求 Prompt（原文）」列。长度不限；无需预先指定单元测试、实现模块或技术方案，但应明确目标、适用场景及可观察的预期行为，避免仅描述抽象方向。

**去 AI 化（红线，全程自动）**：本题目**所有自然语言产物**——instruction.md、nl_rubric 每条 text、task.toml 文本字段（真实性与难度说明、产物结果、notes）、底稿交付字段——全程自动套 `skills/humanizer-zh/SKILL.md`：**每步产物一写出来就立即过**，不做「最后统一补」。正文为平实自然语言，禁用「」（直角引号）、——（双破折号）、反引号、加粗滥用，不用 Markdown 标签与 -/* 列表符号；命中即改，不允许保留。

```Markdown
为 Codex 增加一个可选的自动续跑功能：当任务因用量达到上限而终止、且账户存在可用 reset credit 时，自动兑换一次，并在同一 Session 中发起新的 continuation turn；否则保持现有错误提示和手动重置流程。
```

```Markdown
为 FastAPI 增加可配置的隐式 HEAD 与自动 OPTIONS 能力。

在 FastAPI、APIRouter 的构造函数、路由装饰器、api_route、add_api_route 和 include_router 中增加 auto_head 与 auto_options。GET 路由的 auto_head 默认开启，auto_options 默认关闭。直接注册在应用上的路由以应用级配置作为最外层默认值；通过 Router 引入的路由，在参数未显式设置时，按照 route → include → router 由近到远采用最近的配置值；显式定义的 HEAD 或 OPTIONS 始终优先。

隐式 HEAD 应保留对应 GET 路由的依赖、参数校验、状态码和响应头，但不返回响应体。隐式 OPTIONS 应返回状态码 200 的 JSON，包含 path、按 GET、HEAD、POST、PUT、PATCH、DELETE、OPTIONS、TRACE 排序的 methods，以及与该路径 OpenAPI 定义一致但排除 HEAD 和 OPTIONS 的 operations，并返回 Allow 响应头。同一路径下任一操作启用 auto_options 时，只生成一个隐式 OPTIONS 响应。

公开签名中的新增参数须使用 Annotated[..., Doc(...)] 风格。新增 ImplicitMethodTrackingMiddleware，只统计隐式 HEAD 与 OPTIONS 的命中并忽略非 HTTP scope；get_stats() 返回形如 {完整路径: {head_hits: int, options_hits: int}} 的深拷贝，reset_stats() 清空统计。
```

## 反例：不应收录的伪需求

|反例需求|问题类型|为什么不收录|
|---|---|---|
|为 Claude Code 增加完整 CoT 的自动保存、展示和导出功能。|无法由 Repo 独立实现|若模型服务未通过受支持接口提供完整内部推理，客户端 Repo 无法获取或还原；需求依赖上游模型能力与安全策略变化。|
|为 Codex CLI 增加 side chat，使用户可在不打断主会话时临时提问。|已有功能|Codex CLI 已提供 `/side`（别名 `/btw`），会创建与主聊天记录分离的临时旁聊。属于未查重的重复需求。|
|让 FastAPI 内置 Kubernetes 自动扩缩容控制器，根据接口 QPS 自动创建、扩缩和回收 Deployment 与 Pod。|与 Repo 定位不符|这是部署与集群编排能力，依赖 Kubernetes 控制面和集群权限，不属于 FastAPI Web 框架核心职责；更适合由 HPA、Operator 或独立部署组件实现。|

# 4\. 运行与取证

1. 用 Trae CN（推荐 TraeX）或 mini\-swe\-agent \+ Seed Evolving 运行，**单 Prompt 单轮提交**；运行过程中不追加人工澄清、任务拆解或引导性提示。

2. 记录 Trae Session ID 与有效轮数，填入 task\.toml；harness 为 miniswe 时无 Trae 会话，session id 留空。轨迹按 harness 取其一，三者有其一即可：TraeX 取 `.trae/cli/sessions/` 下本次会话的轨迹文件，放 `evidence/trajectory.jsonl`；Trae IDE 导出会话记录，放 `evidence/trajectory.md`；miniswe 提交 mini\-swe\-agent 的 `.traj.json`，放 `evidence/trajectory.json`（运行时加 `-o evidence/trajectory.json` 可直接写入，否则默认落在全局配置目录的 `last_mini_run.traj.json`，运行结束时终端会打印实际路径）。

3. 运行结束后在仓库根目录生成 patch，放到 `evidence/model.patch`。diff 基准必须是 task\.toml 里登记的 `base_commit`，不得使用 HEAD\~1、默认分支或其他基准。

4. 每题只交**一次**运行的取证。截图等补充材料放 `evidence/screenshots/`，`evidence/` 随整题 zip 一并打包，通过底稿「交付包（zip）」列上传。

```Bash
BASE_COMMIT="填 task.toml 里的 base_commit（40 位完整 SHA）"
git add -A
git diff --binary --cached "$BASE_COMMIT" > evidence/model.patch
```

---

# 5\. nl\_rubric\.yaml

颗粒度与出题规范里的 Verify Rubric 一致：每条一句自然语言，只额外标 `type`。不拆到字段级，也不写死文件名、类名或实现方案，整体不少于 5 条。

```YAML
rubrics:
  - id: 1
    type: p2p
    text: 功能默认关闭，关闭时保持现有行为且不调用兑换接口。

  - id: 2
    type: f2p
    text: 开启后，收到用量上限错误且存在可用 credit 时，只兑换一次，并在同一 Session 中提交一次 continuation turn。

  - id: 3
    type: f2p
    text: reset 和 alreadyRedeemed 视为成功，noCredit、nothingToReset 或调用失败时不得自动续跑。

  - id: 4
    type: f2p
    text: 重复错误事件、网络重试或客户端重启不得重复消耗 credit 或重复提交 continuation turn，同一兑换尝试应复用幂等键。

  - id: 5
    type: f2p
    text: 自动流程失败后保留原 Session，并继续提供 /usage 手动处理入口。
```

```YAML
rubrics:
  - id: 1
    type: f2p
    text: 参数与默认值：所有要求的公开入口均暴露 auto_head 和 auto_options；GET 默认开启隐式 HEAD，自动 OPTIONS 默认关闭。

  - id: 2
    type: f2p
    text: 配置优先级：直接应用路由采用 app 默认值；引入路由按 route → include → router 解析；显式 HEAD / OPTIONS 始终优先，重复 include 后行为稳定。

  - id: 3
    type: f2p
    text: HEAD 行为：复用 GET 的依赖、校验、状态码和响应头，不返回 body，并保留正确的 content-length。

  - id: 4
    type: f2p
    text: OPTIONS 行为：每个 path 最多生成一个隐式 OPTIONS；状态码、JSON 中的 path / methods / operations、方法顺序和 Allow 头均正确，operations 与 OpenAPI 一致且不包含 HEAD / OPTIONS，不破坏 CORS 预检。

  - id: 5
    type: f2p
    text: 公开接口：新增参数均使用 Annotated[..., Doc(...)]，可在公开签名和文档表面中检查。

  - id: 6
    type: f2p
    text: 中间件：只统计隐式命中，忽略显式方法与非 HTTP scope；get_stats() 返回深拷贝，reset_stats() 能清零，统计按完整路径隔离。

  - id: 7
    type: p2p
    text: 回归要求：新增验证通过，Repo 既有测试不得回归。
```

## Verify Rubric 反例

|Bad Case|问题|
|---|---|
|“功能正常、体验良好、代码质量高。”|判定标准主观，没有可观察行为、输入条件和预期结果，不同质检人无法稳定复现。|
|“必须修改 app\.rs，并新增 AutoResetManager 类。”|无必要地写死文件、类名或实现方案，可能把行为正确的替代实现误判为失败。|
|“使用真实账户耗尽额度，并消耗一次真实 reset credit 验证。”|依赖稀缺或不可访问的外部状态，成本高且难以重复；应允许通过 mock、日志或可控状态验证。|
|“先看模型怎么实现，再补充它没有做到的检查项。”|属于事后倒改标准，无法公平判断。Rubric 可在出题前后完善，但必须在最终判定前固定。|

# 6\. 收录要求

|运行结果|是否收录|
|---|---|
|有效轮数 \> 100|收录：长程题|
|有效轮数 ≤ 100，且「是否完成需求」为 部分完成 / 未完成 / 无法判断|收录：难题|
|有效轮数 ≤ 100，且「是否完成需求」为 完成|不收录|

**不收录的题不计酬。**收录判据只看上表这两列，运行完即可自行判断本题是否收录，不需要等质检结论。

# 7\. 一键回填底稿【Demo】

task\.toml 填好后由脚本回填底稿，无需手工录入。`toml2base.py` 从交付包提取 17 列写入一条记录，并将整题 zip 上传至「交付包（zip）」列，合计 18 列；「提交人」是人员列，请自行在底稿里圈人，其余 4 列由质检填写。附件里另有 `count_steps.py`，用于自查 `effective_turns`。模板包与脚本见下方附件，解压后将 `请改成题目名称` 目录重命名为本题题目名称。

[harbor\-交付模板包\.zip](Images_attachments/harbor-交付模板包.zip)

环境要求：Python 3；`pip install pyyaml tomli`（Python 3\.11 及以上无需 tomli）；安装 lark\-cli 并完成 `lark-cli auth login`；具备本底稿的编辑权限。以上任一项缺失，脚本会明确指出缺失项。

```Bash
# 体检，不写库
python3 toml2base.py --dry-run 题目目录

# 体检通过后写入底稿
python3 toml2base.py 题目目录
```

`count_steps.py` 用于自查 `effective_turns`。计数以 agent step 为单位，一次模型调用记为一个 step：一批工具调用无论包含几个调用均记为一个，未附带工具调用的收尾回复记为一个，一次上下文压缩记为一个，子代理（`spawn_agent`）执行的轮数一并计入。脚本须对 `.trae/cli/sessions/` 下的原始轨迹运行——子代理的轨迹为独立文件，依赖该目录结构定位，轨迹拷入 `evidence/` 后无法关联，计数将偏小，此时脚本会输出提示。miniswe 无需使用本脚本，其 step 数取 `.traj.json` 中 `info.model_stats.api_calls`。

```Bash
# TraeX：对 .trae/cli/sessions/ 下的原始轨迹跑
python3 count_steps.py ~/.trae/cli/sessions/2026/09/03/rollout-xxx.jsonl

# 想看每一步都是什么
python3 count_steps.py <轨迹文件> --show
```

体检逐列输出结果，任一列不通过即中止，不写入任何内容，并指出列名、缺失项与合法取值。同一题重跑为更新原记录，不会重复建行。

此外，若题目是本地项目、无远程 `repo_url`/`Fork Repo Commit URL`，或环境未装 `lark-cli`/未 `auth login`、底稿「需求预检记录」需先走预检，则脚本无法直接回填。此时改为在交付包生成 `docs/底稿必填字段.md`，把底稿**必填字段**的值按「基础与仓库信息 / 出题内容与产物 / 运行记录」整理成表，由提交人逐字段复制；截图、轨迹、预检记录由提交人自行在底稿处理。

下列情况一律退回，提交前应自行体检：

- 必需文件缺失或为空：task\.toml、instruction\.md、environment/Dockerfile、tests/nl\_rubric\.yaml、evidence/model\.patch

- evidence/trajectory\.jsonl、trajectory\.json 与 trajectory\.md 全都不存在或全为空

- harness 填 Trae 或 TraeX 却没填 trae\_session\_id

- evidence/screenshots/ 为空

- task\.toml 的 title 与交付包目录名不一致

- 单选列取值不在底稿选项内（以底稿实时选项为准）

- base\_commit 与 environment/Dockerfile 的 ARG BASE\_SHA 不一致

- task\.toml 含规范外的键，或键名大小写不符

- rubric 少于 5 条、type 不为 f2p / p2p、id 重复，或无 f2p 条目

- 产物结果未逐条对应 rubric，或与「是否完成需求」矛盾

- instruction\.md 或 rubric 中残留 \<……\> 占位

