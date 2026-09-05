1.bathes:
method: post

url: https://swe.jzxhnh.com/api/v1/precheck/batches

body:
{"rows":[{"repo_url":"https://github.com/caddyserver/caddy","prompt":"为 reverse_proxy 增加可配置的重试退避与抖动能力。\n\n现状：当上游请求失败且启用了负载均衡重试（lb_try_duration / lb_try_interval / lb_retries）时，每次重试之间都等待固定的 lb_try_interval（未设置时默认 250ms）。上游整体宕机或过载时，大量在途请求会以相同节奏同时发起重试，容易对剩余健康上游或刚恢复的上游造成瞬时冲击。\n\n需求：新增一个可选的 lb_try_backoff 子指令（接受时长，如 lb_try_backoff 1s），启用后每次重试的等待时间按指数增长，并加入一定随机抖动，避免重试风暴；整体仍受 lb_try_duration 约束，超过总时长即停止重试。不配置该指令时，保持现有固定 lb_try_interval 行为不变。\n\n预期行为：\n\n不配置 lb_try_backoff 时，重试间隔保持现状（固定 lb_try_interval，默认 250ms），行为与改动前完全一致\n配置 lb_try_backoff 后，相邻重试之间的等待时间整体递增（后一次不低于前一次），且每次等待带有随机抖动（同一请求多次重试的间隔不完全相同）\n无论退避如何增长，所有重试必须在 lb_try_duration 内完成；到点后不再发起下一次重试\nlb_try_backoff 与 lb_try_interval、lb_retries、lb_retry_match 可同时使用；backoff 只影响重试之间的等待时长，不改变「哪些响应触发重试」的判定\n配置解析与校验：lb_try_backoff 接受与其它时间参数一致的时长语法（如 500ms、2s），非法值报错"},{"repo_url":"https://github.com/caddyserver/caddy","prompt":"为访问日志增加按 header 名脱敏的字段过滤器。\n\n现状：访问日志可以通过字段记录请求/响应头（如 request>headers>Authorization、resp_headers>Set-Cookie 等），其中常含密钥、令牌、会话等敏感信息。目前要脱敏只能删除整个字段，或用 replace / hash 对某个具体字段路径做整体替换，无法按「header 名」精确只处理某个头，且对数组型 header 字段的 replace 并不正确。\n\n需求：新增一个日志字段过滤器（如 caddy.logging.encoders.filter.header），像已有的 query / cookie / set_cookie 过滤器一样，按 header 名（大小写不敏感）对日志里的请求头与响应头字段做 replace / hash / delete 三种动作，只改对应 header 的值，不影响其它 header。\n\n预期行为：\n\n过滤器支持 replace <header名> <替换值>、hash <header名>、delete <header名> 三种动作，可配置多条\n对记录请求头的字段（request>headers、request>headers>... 等）按 header 名匹配，命中则替换 / 哈希 / 删除该 header 的值\n对记录响应头的字段（resp_headers、resp_headers>... 等）同样按 header 名匹配处理\nheader 名匹配大小写不敏感；未命中任何配置的 header 保持原样输出\n作用于数组型 header 字段时能正确处理（替换的是该 header 的值，而非破坏整个字段类型）\n未配置该过滤器时，日志行为与改动前完全一致"},{"repo_url":"https://github.com/caddyserver/caddy","prompt":"为 file_server 的目录浏览增加服务端名称过滤，并让各输出格式一致。\n\n现状：启用 browse 后，HTML 视图通过前端 JS 支持 ?filter= 参数按名称即时过滤，但过滤只发生在浏览器端；通过 Accept: application/json 或 Accept: text/plain 请求目录列表时完全没有过滤能力，HTML 与 JSON、纯文本三种格式的行为不一致。\n\n需求：把名称过滤下沉到服务端，使 sort / order / limit / offset 之外的 filter 参数在 HTML、JSON、纯文本三种输出中一致生效。\n\n预期行为：\n\n请求目录列表时，若带 ?filter=<子串>，只返回名称包含该子串的条目（大小写不敏感）；不带 filter 时返回完整列表\n三种输出（Accept: application/json、text/plain、默认 HTML）都遵循同一过滤结果\nfilter 与 sort / order / limit / offset 可组合：先过滤、再排序、再分页\n过滤不区分文件与目录，按条目名称匹配\n未传 filter 时，三种输出行为与改动前一致"}]}

response:
{
    "code": 0,
    "message": "已提交 3 条，开始检测",
    "data": {
        "batch_id": "caada81f664d45658b299a4427652419",
        "status": "QUEUED",
        "status_label": "排队中",
        "total": 3,
        "done": 0,
        "passed": 0,
        "rejected": 0,
        "failed": 0,
        "canceled": 0,
        "pending": 0,
        "running": 0,
        "error": "",
        "created_at": "2026-09-05T21:30:22+08:00",
        "finished_at": null,
        "finished": false,
        "resumable": false
    }
}

2. check batchs
method: get:

url: https://swe.jzxhnh.com/api/v1/precheck/batches/caada81f664d45658b299a4427652419

response:
{
    "code": 0,
    "message": "ok",
    "data": {
        "batch": {
            "batch_id": "caada81f664d45658b299a4427652419",
            "status": "RUNNING",
            "status_label": "执行中",
            "total": 3,
            "done": 0,
            "passed": 0,
            "rejected": 0,
            "failed": 0,
            "canceled": 0,
            "pending": 3,
            "running": 0,
            "error": "",
            "created_at": "2026-09-05T21:30:22+08:00",
            "finished_at": null,
            "finished": false,
            "resumable": false
        },
        "items": [
            {
                "id": 163,
                "queue_position": 27,
                "duration_ms": 0,
                "row_no": 1,
                "batch_id": "caada81f664d45658b299a4427652419",
                "repo_url": "https://github.com/caddyserver/caddy",
                "prompt_excerpt": "为 reverse_proxy 增加可配置的重试退避与抖动能力。\n\n现状：当上游请求失败且启用了负载均衡重试（lb_try_duration / lb_try_interval / lb_retries）时，每次重试之间都等待固定的 lb_",
                "status": "PRECHECK_PENDING",
                "status_label": "待检测",
                "difficulty": "",
                "difficulty_total": 0,
                "reject_kind": "",
                "reject_label": "",
                "reject_detail": "",
                "requires_recheck": false,
                "appeal_status": "none",
                "appeal_status_label": "未申诉",
                "appeal_count": 0,
                "passed_by_appeal": false,
                "consumed_submission_id": 0,
                "recheck_count": 0,
                "recheck_requested_at": null,
                "policy_version": "2026-09-05.precheck-v4",
                "appealable": false,
                "rerunnable": false,
                "deletable": false,
                "error": "",
                "created_at": "2026-09-05T21:30:22+08:00",
                "updated_at": "2026-09-05T21:30:22+08:00"
            },
            {
                "id": 164,
                "queue_position": 28,
                "duration_ms": 0,
                "row_no": 2,
                "batch_id": "caada81f664d45658b299a4427652419",
                "repo_url": "https://github.com/caddyserver/caddy",
                "prompt_excerpt": "为访问日志增加按 header 名脱敏的字段过滤器。\n\n现状：访问日志可以通过字段记录请求/响应头（如 request>headers>Authorization、resp_headers>Set-Cookie 等），其中常含密钥、令牌、会",
                "status": "PRECHECK_PENDING",
                "status_label": "待检测",
                "difficulty": "",
                "difficulty_total": 0,
                "reject_kind": "",
                "reject_label": "",
                "reject_detail": "",
                "requires_recheck": false,
                "appeal_status": "none",
                "appeal_status_label": "未申诉",
                "appeal_count": 0,
                "passed_by_appeal": false,
                "consumed_submission_id": 0,
                "recheck_count": 0,
                "recheck_requested_at": null,
                "policy_version": "2026-09-05.precheck-v4",
                "appealable": false,
                "rerunnable": false,
                "deletable": false,
                "error": "",
                "created_at": "2026-09-05T21:30:22+08:00",
                "updated_at": "2026-09-05T21:30:22+08:00"
            },
            {
                "id": 165,
                "queue_position": 29,
                "duration_ms": 0,
                "row_no": 3,
                "batch_id": "caada81f664d45658b299a4427652419",
                "repo_url": "https://github.com/caddyserver/caddy",
                "prompt_excerpt": "为 file_server 的目录浏览增加服务端名称过滤，并让各输出格式一致。\n\n现状：启用 browse 后，HTML 视图通过前端 JS 支持 ?filter= 参数按名称即时过滤，但过滤只发生在浏览器端；通过 Accept: appl",
                "status": "PRECHECK_PENDING",
                "status_label": "待检测",
                "difficulty": "",
                "difficulty_total": 0,
                "reject_kind": "",
                "reject_label": "",
                "reject_detail": "",
                "requires_recheck": false,
                "appeal_status": "none",
                "appeal_status_label": "未申诉",
                "appeal_count": 0,
                "passed_by_appeal": false,
                "consumed_submission_id": 0,
                "recheck_count": 0,
                "recheck_requested_at": null,
                "policy_version": "2026-09-05.precheck-v4",
                "appealable": false,
                "rerunnable": false,
                "deletable": false,
                "error": "",
                "created_at": "2026-09-05T21:30:22+08:00",
                "updated_at": "2026-09-05T21:30:22+08:00"
            }
        ]
    }
}