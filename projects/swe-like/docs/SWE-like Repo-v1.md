# SWE\-like Repo 出题规范（试行）

项目背景：扩充真实且具有难度的SWE类题目，用于提升Seed模型在SWE类题目上的能力

人员画像：1年以上开发者，有长期使用的开源Repo，且熟悉Vibe Coding

模型与终端： Trae CN \+ Seed Evolving

**不可以从Issues里照抄需求**

# 1\. 出题与运行

1. 选择自己熟悉的开源 Repo，并记录 Repo URL 及固定版本（Commit 或 Tag\-最新）。需求应基于对项目真实使用场景和代码结构的理解独立提出，不得直接照抄 Top Open Issues、热门讨论或既有题目。

2. 提交给 Trae\+Seed 的需求描述长度不限。无需预先指定单元测试、实现模块或技术方案，但应明确目标、适用场景及可观察的预期行为，避免仅描述抽象方向。

3. 使用 Trae\+Seed 单 Prompt 运行；运行过程中不追加人工澄清、任务拆解或引导性提示。需完整记录 Trae Session ID 与有效轮数，确保过程可追溯。

4. 每道题的最终交付内容须包含：真实性与难度说明、可能涉及模块、Verify Rubric、验证产物。上述内容可在出题、运行或复盘阶段补充完善；Verify Rubric 应在作出最终评价前明确，并保持评判口径一致，不得根据模型结果事后调整标准。

---

# 2\. 交付示例 

|字段|示例内容|
|---|---|
|**需求Prompt**|为 Codex 增加一个可选的自动续跑功能：当任务因用量达到上限而终止、且账户存在可用 reset credit 时，自动兑换一次，并在同一 Session 中发起新的 continuation turn；否则保持现有错误提示和手动重置流程。|
|**真实性与难度说明**|长任务触达用量上限后，用户目前需要手动兑换 reset credit 并重新触发任务，容易中断工作流。当前 Codex 已具备额度查询与手动兑换能力，难点在于正确识别可恢复的限额错误、保证兑换与续跑幂等、避免重复提交，并在同一 Session 中安全创建 continuation turn。|
|**可能涉及模块**|App Server 额度接口、TUI 的 /usage 与限额错误处理、任务和 Turn 生命周期、输入队列与 Session 状态、配置项及状态持久化。|
|**Verify Rubric**|① 功能默认关闭，关闭时保持现有行为且不调用兑换接口；② 开启后，收到用量上限错误且存在可用 credit 时，只兑换一次，并在同一 Session 中提交一次 continuation turn；③ reset 和 alreadyRedeemed 视为成功，noCredit、nothingToReset 或调用失败时不得自动续跑；④ 重复错误事件、网络重试或客户端重启不得重复消耗 credit 或重复提交 continuation turn，同一兑换尝试应复用幂等键；⑤ 自动流程失败后保留原 Session，并继续提供 /usage 手动处理入口。|
|**验证产物**|基于 mock backend 的自动化测试与日志：额度查询及兑换调用次数、幂等键、Session ID、Turn 顺序和各分支最终状态；不依赖真实账户具备可用 reset credit。|

真实DeepSWE题目（for reference）

|字段|示例内容|
|---|---|
|**需求Prompt**|为 FastAPI 增加可配置的隐式 HEAD 与自动 OPTIONS 能力。<br>在 FastAPI、APIRouter 的构造函数、路由装饰器、api\_route、add\_api\_route 和 include\_router 中增加 auto\_head 与 auto\_options。GET 路由的 auto\_head 默认开启，auto\_options 默认关闭。直接注册在应用上的路由以应用级配置作为最外层默认值；通过 Router 引入的路由，在参数未显式设置时，按照 route → include → router 由近到远采用最近的配置值；显式定义的 HEAD 或 OPTIONS 始终优先。<br>隐式 HEAD 应保留对应 GET 路由的依赖、参数校验、状态码和响应头，但不返回响应体。隐式 OPTIONS 应返回状态码 200 的 JSON，包含 path、按 GET、HEAD、POST、PUT、PATCH、DELETE、OPTIONS、TRACE 排序的 methods，以及与该路径 OpenAPI 定义一致但排除 HEAD 和 OPTIONS 的 operations，并返回 Allow 响应头。同一路径下任一操作启用 auto\_options 时，只生成一个隐式 OPTIONS 响应。<br>公开签名中的新增参数须使用 Annotated\[\.\.\., Doc\(\.\.\.\)\] 风格。新增 ImplicitMethodTrackingMiddleware，只统计隐式 HEAD 与 OPTIONS 的命中并忽略非 HTTP scope；get\_stats\(\) 返回形如 \{完整路径: \{head\_hits: int, options\_hits: int\}\} 的深拷贝，reset\_stats\(\) 清空统计。|
|**真实性与难度说明**|这是 Web 框架中真实的 HTTP 方法语义与路由能力，涉及 app、router、include 和单路由四层配置继承；既要处理显式方法覆盖，又要保持 OpenAPI、CORS、依赖执行、响应头和既有路由行为。改动跨构造接口、路由注册、请求分发、文档生成和中间件，容易产生全局回归。|
|**可能涉及模块**|`fastapi/applications.py`、`fastapi/routing.py`、`fastapi/middleware/methods.py`、OpenAPI 生成、Starlette 路由分发，以及对应测试与文档。|
|**Verify Rubric**|① 参数与默认值：所有要求的公开入口均暴露 auto\_head 和 auto\_options；GET 默认开启隐式 HEAD，自动 OPTIONS 默认关闭。<br>② 配置优先级：直接应用路由采用 app 默认值；引入路由按 route → include → router 解析；显式 HEAD / OPTIONS 始终优先，重复 include 后行为稳定。<br>③ HEAD 行为：复用 GET 的依赖、校验、状态码和响应头，不返回 body，并保留正确的 content\-length。<br>④ OPTIONS 行为：每个 path 最多生成一个隐式 OPTIONS；状态码、JSON 中的 path / methods / operations、方法顺序和 Allow 头均正确，operations 与 OpenAPI 一致且不包含 HEAD / OPTIONS，不破坏 CORS 预检。<br>⑤ 公开接口：新增参数均使用 Annotated\[\.\.\., Doc\(\.\.\.\)\]，可在公开签名和文档表面中检查。<br>⑥ 中间件：只统计隐式命中，忽略显式方法与非 HTTP scope；get\_stats\(\) 返回深拷贝，reset\_stats\(\) 能清零，统计按完整路径隔离。<br>⑦ 回归要求：新增验证通过，Repo 既有测试不得回归。|
|**产物结果**|一次真实回放未通过。主要失败为公开签名文档不完整、OPTIONS 的 PATCH 方法顺序或内容错误、HEAD 丢失 content\-length，以及既有 PATCH / TRACE 路由回归为 405。|
|**验证产物**|`/logs/artifacts/model.patch`、verifier 测试日志、F2P / P2P 统计、失败测试列表及轨迹。|

## 反例：不应收录的伪需求

|反例需求|问题类型|为什么不收录|
|---|---|---|
|为 Claude Code 增加完整 CoT 的自动保存、展示和导出功能。|无法由 Repo 独立实现|若模型服务未通过受支持接口提供完整内部推理，客户端 Repo 无法获取或还原；需求依赖上游模型能力与安全策略变化。|
|为 Codex CLI 增加 side chat，使用户可在不打断主会话时临时提问。|已有功能<br>|Codex CLI 已提供 `/side`（别名 `/btw`），会创建与主聊天记录分离的临时旁聊。属于未查重的重复需求。|
|让 FastAPI 内置 Kubernetes 自动扩缩容控制器，根据接口 QPS 自动创建、扩缩和回收 Deployment 与 Pod。|与 Repo 定位不符|这是部署与集群编排能力，依赖 Kubernetes 控制面和集群权限，不属于 FastAPI Web 框架核心职责；更适合由 HPA、Operator 或独立部署组件实现。|

## Verify Rubric 反例

|Bad Case|问题|
|---|---|
|“功能正常、体验良好、代码质量高。”|判定标准主观，没有可观察行为、输入条件和预期结果，不同质检人无法稳定复现。|
|“必须修改 app\.rs，并新增 AutoResetManager 类。”|无必要地写死文件、类名或实现方案，可能把行为正确的替代实现误判为失败。|
|“使用真实账户耗尽额度，并消耗一次真实 reset credit 验证。”|依赖稀缺或不可访问的外部状态，成本高且难以重复；应允许通过 mock、日志或可控状态验证。|
|“先看模型怎么实现，再补充它没有做到的检查项。”|属于事后倒改标准，无法公平判断。Rubric 可在出题前后完善，但必须在最终判定前固定。|

---

# 3\. 收录标准

|运行结果|是否收录|
|---|---|
|有效轮数 \> 100，效果好或差|收录：长程题|
|有效轮数 ≤ 100，但实现明显差|收录：难题|
|有效轮数 ≤ 100，且实现较好|不收录|



