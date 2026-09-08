1.提交数据, 这个接口是获取提交数据的表单字段
method: get

url: 
https://swe.jzxhnh.com/api/v1/submissions/form-schema

response:

{
    "code": 0,
    "message": "ok",
    "data": {
        "fields": [
            {
                "field_key": "title",
                "label": "题目名称",
                "group": "基础与仓库信息",
                "type": "text",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 255,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "requirement_prompt",
                "label": "需求 Prompt（原文）",
                "group": "出题内容与产物",
                "type": "textarea",
                "required": true,
                "auto": true,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 20000,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "repo_url",
                "label": "Repo URL",
                "group": "基础与仓库信息",
                "type": "url",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": true,
                "max_length": 512,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "precheck_item_id",
                "label": "需求预检记录",
                "group": "出题内容与产物",
                "type": "precheck_ref",
                "required": false,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "question_type",
                "label": "Type",
                "group": "基础与仓库信息",
                "type": "select",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [
                    "有效轮数 > 100",
                    "有效轮数 < 100 且 效果差",
                    "有效轮数 < 100 且 效果好"
                ],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "submitter_name",
                "label": "提交人",
                "group": "基础与仓库信息",
                "type": "text",
                "required": false,
                "auto": true,
                "builtin": true,
                "locked_on_fix": true,
                "max_length": 64,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "submitted_date",
                "label": "提交日期",
                "group": "基础与仓库信息",
                "type": "date",
                "required": false,
                "auto": true,
                "builtin": true,
                "locked_on_fix": true,
                "max_length": 0,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "commit_ref",
                "label": "原Commit/版本",
                "group": "基础与仓库信息",
                "type": "text",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": true,
                "max_length": 255,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "commit_url",
                "label": "Fork Repo Commit URL",
                "group": "基础与仓库信息",
                "type": "text",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 512,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "primary_language",
                "label": "主要语言",
                "group": "基础与仓库信息",
                "type": "select",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [
                    "Python",
                    "JavaScript/TypeScript",
                    "Rust",
                    "Go",
                    "Java/Kotlin",
                    "C/C++",
                    "C#",
                    "Ruby",
                    "PHP",
                    "Swift/Objective-C",
                    "Dart",
                    "Shell",
                    "其他"
                ],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "task_type",
                "label": "任务类型",
                "group": "出题内容与产物",
                "type": "select",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [
                    "功能新增",
                    "Bug 修复",
                    "测试增强",
                    "重构/性能",
                    "配置/工具链",
                    "其他"
                ],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "authenticity_note",
                "label": "真实性与难度说明",
                "group": "出题内容与产物",
                "type": "textarea",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 10000,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "involved_modules",
                "label": "可能涉及模块",
                "group": "出题内容与产物",
                "type": "textarea",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 10000,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "verify_rubric",
                "label": "Verify Rubric",
                "group": "出题内容与产物",
                "type": "textarea",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 20000,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "artifact_result",
                "label": "产物结果",
                "group": "出题内容与产物",
                "type": "textarea",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 20000,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "seed_model",
                "label": "Seed 模型/版本",
                "group": "运行记录",
                "type": "text",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 128,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "trae_session_id",
                "label": "Trae Session ID",
                "group": "运行记录",
                "type": "text",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": true,
                "max_length": 512,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "trae_session_id_2",
                "label": "Trae Session ID 2",
                "group": "运行记录",
                "type": "text",
                "required": false,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 512,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "effective_rounds",
                "label": "有效轮数",
                "group": "运行记录",
                "type": "number",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "seed_rounds",
                "label": "seed 轮次",
                "group": "运行记录",
                "type": "number",
                "required": false,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "requirement_completed",
                "label": "是否完成需求",
                "group": "运行记录",
                "type": "select",
                "required": true,
                "auto": false,
                "builtin": true,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [
                    "完成",
                    "部分完成",
                    "未完成",
                    "无法判断"
                ],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "x_is_more_than_two_hours",
                "label": "是否超过两小时",
                "group": "运行记录",
                "type": "select",
                "required": true,
                "auto": false,
                "builtin": false,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [
                    "是",
                    "否"
                ],
                "placeholder": "",
                "help_text": "",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "x_artifact_shot",
                "label": "产物截图",
                "group": "出题内容与产物",
                "type": "attachment",
                "required": true,
                "auto": false,
                "builtin": false,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [],
                "placeholder": "",
                "help_text": "上传产物的运行结果截图，支持 png/jpg/gif/webp 等图片格式",
                "required_when": {},
                "validation": {}
            },
            {
                "field_key": "x_trae_trace",
                "label": "Trae 轨迹",
                "group": "运行记录",
                "type": "attachment",
                "required": true,
                "auto": false,
                "builtin": false,
                "locked_on_fix": false,
                "max_length": 0,
                "options": [],
                "placeholder": "",
                "help_text": "上传 Trae 会话的轨迹文件，支持 json/txt/log/md/zip 等格式",
                "required_when": {},
                "validation": {}
            }
        ],
        "schema_version": "e361a4b27c71b68a",
        "submit_frozen": false,
        "frozen_message": "",
        "attachment": {
            "configured": true,
            "max_mb": 20,
            "accept": ".png,.jpg,.jpeg,.gif,.webp,.bmp,.mp4,.webm,.txt,.log,.md,.json,.jsonl,.csv,.yaml,.yml,.patch,.diff,.pdf,.zip,.gz,.tar,.tgz,.7z,.rar,.mov,.xlsx,.docx"
        }
    }
}

3.产物截图上传
url: https://swe.jzxhnh.com/api/v1/uploads/attachment
method: post

request header:
authority: swe.jzxhnh.com
path: /api/v1/uploads/attachment
scheme:https
content-type: multipart/form-data; boundary=----WebKitFormBoundary64IFsViblWVHoHmV

response body:
{
    "code": 0,
    "message": "附件上传成功",
    "data": {
        "url": "https://bduse-1304520688.cos.ap-beijing.myqcloud.com/form-attachments/11/202609/218d3600d87e6eef6a8d335e_validation.png",
        "name": "validation.png",
        "size": 34887,
        "content_type": "image/png"
    }
}

4.轨迹文件上传
url: https://swe.jzxhnh.com/api/v1/uploads/attachment
method: post

request header:
authority: swe.jzxhnh.com
path: /api/v1/uploads/attachment
scheme:https
content-type: multipart/form-data; boundary=----WebKitFormBoundaryTcAZAY8ADbURLHxH
request body: file stream

response body:
{
    "code": 0,
    "message": "附件上传成功",
    "data": {
        "url": "https://bduse-1304520688.cos.ap-beijing.myqcloud.com/form-attachments/11/202609/4283f6402ed1347e67623eff_trajectory.md",
        "name": "trajectory.md",
        "size": 30839,
        "content_type": "application/octet-stream"
    }
}

4.轨迹文件上传
url: https://swe.jzxhnh.com/api/v1/submissions/create
method: post

request header:
authority: swe.jzxhnh.com
path: /api/v1/submissions/create
scheme:https

requst body:

{"title":"caddy-06","repo_url":"https://github.com/caddyserver/caddy","precheck_item_id":559,"question_type":"有效轮数 > 100","commit_ref":"62a72977e58c87fad7e7726c18b58f10c653f2d3","commit_url":"https://github.com/attitudeshuai/caddy/commit/acd21f8bc00c9ab0e70578dde751a664f3304de4","primary_language":"Go","task_type":"功能新增","authenticity_note":"真实使用场景：Caddy 配置热重载、上游地址变化或主动下线某个上游时，现有 Cleanup 路径直接关闭空闲连接或删除主机，不等待在途请求完成，导致被排空上游上的在途请求断连、客户端 502。生产环境要求零停机重载与平滑摘除上游，这是常见的真实缺口。难点：为静态上游新增排空状态机（活动、排空、已排空三个阶段），并让它与负载均衡选择、重试联动（排空或已移除的上游不再作为候选）；在热路径上保证并发安全与原子状态；与 Handler.Cleanup、配置 reload、DNS/健康变化交织；H2 连接池按上游维度隔离流与连接复用；排空等待不阻塞整体 reload；默认关闭保证向后兼容。跨 transport、handler 生命周期、admin 状态、配置重载与健康变化多个层面。","involved_modules":"modules/caddyhttp/reverseproxy/httptransport.go（连接池与 Cleanup 排空）、reverseproxy.go（Handler 生命周期与在途计数联动）、hosts.go（上游状态）、selectionpolicies.go 与 retries（排除排空上游）、caddyfile.go（排空配置解析）、admin.go（状态暴露）、对应测试","verify_rubric":"[p2p] 1: 未启用排空时，连接复用与清理路径行为与现状一致，既有转发不回归。\n[f2p] 2: 上游进入排空状态后，选择策略不再把该上游作为新请求候选，重试也不落到该上游。\n[f2p] 3: 排空状态下该上游在途请求在配置的等待时长内正常完成，时长到后强制关闭，不提前断连造成失败。\n[f2p] 4: 配置重载或主动下线该上游时先排空再释放，期间新请求平滑转到其它上游，无连接被硬切而报错。\n[f2p] 5: 连接池按上游维度隔离 HTTP/2 流与连接复用，不同上游不共享连接，可配置最大空闲连接数与空闲超时。\n[p2p] 6: 非法配置（非法时长、与既有 keep-alive 冲突的字段）在配置加载阶段报错。\n[p2p] 7: 新增验证通过，caddy 既有测试（尤其 reverseproxy 相关）不得回归。","artifact_result":"1 未通过 编译失败（upstreampool.go:200 h.Pool undefined），无法验证未启用时的行为\n2 未通过 编译失败，排空状态排除未实现\n3 未通过 编译失败，排空等待未实现\n4 未通过 编译失败，重载排空未实现\n5 未通过 编译失败，连接池隔离未实现\n6 未通过 编译失败，非法配置校验无法验证\n7 未通过 编译失败，回归无法验证","seed_model":"Seed Evolving","trae_session_id":"4478767930023012:6f49a33d44a660b881f8b028545fe8ca_6a9ed6aa1c62b23d2b6df105.6a9ed6af1c62b23d2b6df108.6a9ed6aa1c62b23d2b6df106:TraeCode CN.3.3.95.no_sid.no_ppe.T(2026/9/7 23:22:23)","effective_rounds":157,"requirement_completed":"未完成","x_is_more_than_two_hours":"是","x_artifact_shot":"https://bduse-1304520688.cos.ap-beijing.myqcloud.com/form-attachments/11/202609/218d3600d87e6eef6a8d335e_validation.png","x_trae_trace":"https://bduse-1304520688.cos.ap-beijing.myqcloud.com/form-attachments/11/202609/4283f6402ed1347e67623eff_trajectory.md"}

response body:
{
    "code": 0,
    "message": "提交成功，已开始初检",
    "data": {
        "id": 410,
        "title": "caddy-06",
        "question_type": "有效轮数 > 100",
        "repo_url": "https://github.com/caddyserver/caddy",
        "primary_language": "Go",
        "task_type": "功能新增",
        "effective_rounds": 157,
        "status": "PENDING_QC",
        "status_label": "待初检",
        "current_version": 1,
        "reject_reason": "",
        "editable": false,
        "deletable": false,
        "qc_cancelable": false,
        "created_at": "2026-09-08T08:39:47+08:00",
        "submitted_date": "2026-09-08T08:39:47+08:00",
        "updated_at": "2026-09-08T08:39:47+08:00"
    }
}