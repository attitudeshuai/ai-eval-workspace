# tc-hook-kit 接口说明

轻量 Trae Hook 接收端：Trae 触发 Hook → Bridge POST 事件 → 服务端验签入库 → 按口径统计有效 TC。

---

## 快速开始

```bash
# 终端 1：启动接收端（本机或服务器）
bash scripts/tc-hook-kit/tc-hook serve --host 0.0.0.0 --port 8765

# 终端 2：安装 Hook（把 IP+端口 换成接收端地址）
bash scripts/tc-hook-kit/tc-hook install --host 192.168.1.10 --port 8765

# Trae 跑完一题后查数
bash scripts/tc-hook-kit/tc-hook stats
bash scripts/tc-hook-kit/tc-hook stats example-session
```

也可用 `--server` 直接写完整 URL：

```bash
bash scripts/tc-hook-kit/install.sh --server http://192.168.1.10:8765
```

---

## 链路

```text
Trae Agent 执行工具
  → ~/.trae-cn/hooks.json 触发 6 类事件
  → bridge.js 读 stdin，包装 envelope，HMAC 签名
  → POST http://<你的IP>:<端口>/hooks/trae
  → server.py 验签 → SQLite 入库 → 实时统计有效 TC
```

Bridge 永远 **exit 0**，网络失败只写 `/tmp/tc-hook-kit/bridge-errors.log`，不会打断 Agent。

---

## 认证（HMAC 签名）

安装时会在 `~/.tc-hook-kit/config.json` 生成 `hook_secret`。Bridge 与 Server **必须共用同一密钥**。

### 请求头

| Header | 说明 |
| --- | --- |
| `Content-Type` | `application/json` |
| `x-swemarkup-timestamp` | 毫秒时间戳字符串，如 `1725292800123` |
| `x-swemarkup-signature` | `sha256=<hex>` |

### 签名算法

```text
signature = HMAC-SHA256(hook_secret, timestamp + "." + canonical_json(body))
header    = "sha256=" + hex(signature)
```

`canonical_json`：对象 key 递归排序后 JSON 序列化（与 SWEMarkup / bridge.js 一致）。

### 时效

时间戳与服务器相差超过 **5 分钟** 拒绝（401）。

---

## POST `/hooks/trae`

接收一条 Trae Hook 事件。

### 请求体

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "payload": {
    "hook_event_name": "PostToolUse",
    "session_id": "example-user:example-session....",
    "tool_use_id": "call_abc123",
    "tool_name": "Grep",
    "cwd": "/path/to/workspace"
  }
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `event_id` | 是 | Bridge 生成的 UUID，用于幂等去重 |
| `payload` | 是 | Trae 原样 stdin JSON；统计依赖其中的字段 |

`payload` 常用字段：

| 字段 | 统计用途 |
| --- | --- |
| `hook_event_name` | 事件类型；**有效 TC 只看 `PostToolUse`** |
| `session_id` | 按 Session 分组 |
| `tool_use_id` | 去重主键 |
| `tool_name` | 按工具拆分；判断是否排除 |

### 成功响应 `200`

```json
{
  "ok": true,
  "inserted": true,
  "duplicate": false,
  "event_type": "PostToolUse",
  "session_id": "example-user:example-session...",
  "valid_tc": 42
}
```

| 字段 | 说明 |
| --- | --- |
| `inserted` | 首次入库为 `true`；重复 `event_id` 为 `false` |
| `valid_tc` | **当前 Session** 的有效 TC 数（实时计算） |

### 错误响应

| 状态码 | body | 原因 |
| --- | --- | --- |
| 400 | `{"error":"INVALID_JSON"}` |  body 不是 JSON |
| 400 | `{"error":"INVALID_ENVELOPE"}` | 缺少 event_id / payload |
| 401 | `{"error":"INVALID_SIGNATURE"}` | 签名错误或超时 |

### 处理逻辑（服务端）

1. 验签
2. 按 `event_id` 幂等写入 SQLite（重复则跳过）
3. 从 `payload` 提取 `session_id`、`hook_event_name`、`tool_use_id`、`tool_name`
4. 对当前 Session 重算有效 TC 并在响应里返回

---

## GET `/stats`

查询累计统计。

### 查询参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `session_id` | 否 | 子串匹配，如 `example-session` |

### 响应 `200`

```json
{
  "valid_tc": 120,
  "session_id_filter": null,
  "by_session": {
    "example-user:example-session...": {
      "valid_tc": 120,
      "by_tool": {
        "RunCommand": 39,
        "Grep": 28,
        "Read": 27,
        "Edit": 18,
        "TodoWrite": 6,
        "Glob": 2
      },
      "post_tool_use_ids": 138,
      "excluded_ids": 18
    }
  },
  "by_tool": { "RunCommand": 39, "Grep": 28 },
  "event_counts": {
    "SessionStart": 1,
    "UserPromptSubmit": 1,
    "PreToolUse": 250,
    "PostToolUse": 250,
    "Stop": 1
  },
  "rule": "PostToolUse + tool_use_id 去重，排除轮询/配置/补丁类工具"
}
```

| 字段 | 说明 |
| --- | --- |
| `valid_tc` | 有效 TC 总数（过滤后） |
| `by_session` | 每个 Session 的拆分 |
| `post_tool_use_ids` | 去重前的 PostToolUse ID 数 |
| `excluded_ids` | 命中排除表的 ID 数 |
| `event_counts` | 各事件类型行数（含 Pre/Post 重复） |

### 有效 TC 口径

1. 只认 `PostToolUse`
2. 按 `tool_use_id` 去重（**不按工具名去重**）
3. 排除：`checkRunCommandStatus`、`getAutoRunConfig`、`getConfigurationValue`、`getDiagnostics`、`fileDiffCount`、`getDocumentByUri`、`applyChatSnapshotPatch`

---

## GET `/sessions`

```json
{
  "sessions": ["example-user:example-session..."],
  "count": 1
}
```

---

## GET `/health`

```json
{
  "ok": true,
  "service": "tc-hook-kit"
}
```

---

## 自实现接收端要点

若不用自带的 `server.py`，自行实现 HTTP 服务时：

1. **必须**实现相同的 HMAC 验签，否则 Bridge 会被 401（Bridge 不会重试，事件丢失）
2. **必须**对 `event_id` 幂等，Trae 可能重复触发
3. **必须**持久化 `PostToolUse` 的 `tool_use_id` + `tool_name` + `session_id`
4. 统计时只数 `PostToolUse`，按上文口径去重与排除
5. 响应尽量快（< 4s），Bridge 超时 4 秒

最小伪代码：

```python
def on_post_hooks_trae(body, headers):
    verify_hmac(headers, body, hook_secret)
    payload = body["payload"]
    save_event(body["event_id"], payload)  # INSERT OR IGNORE
    if payload["hook_event_name"] == "PostToolUse":
        upsert_tool(payload["tool_use_id"], payload["tool_name"], payload["session_id"])
    valid_tc = count_valid_tc(session_id=payload.get("session_id"))
    return {"ok": True, "valid_tc": valid_tc}
```

---

## 文件位置

| 路径 | 说明 |
| --- | --- |
| `~/.tc-hook-kit/config.json` | server_url、hook_secret |
| `~/.tc-hook-kit/bridge.json` | Bridge 读取 |
| `/tmp/tc-hook-kit/bridge.json` | 沙箱 fallback |
| `~/.tc-hook-kit/data/events.sqlite3` | 事件库 |
| `/tmp/tc-hook-kit/bridge-errors.log` | Bridge 投递失败 |
| `~/.trae-cn/hooks.json` | Trae Hook 注册 |

---

## 常见问题

**Q: 局域网另一台机器装 Hook，接收端放本机？**  
A: `install --host <接收端局域网IP> --port 8765`，接收端 `serve --host 0.0.0.0` 并放行防火墙。

**Q: stats 一直是 0？**  
A: 查 `/tmp/tc-hook-kit/bridge-errors.log`；Trae Hooks 是否自动运行；secret 是否一致。

**Q: 和 SWEMarkup 工作台能共用吗？**  
A: 不建议同时装两套 Bridge 到同一 `hooks.json` 事件（会双 POST）。二选一，或手动合并两条 command。

**Q: cloud_agent 本地 Hook 很少？**  
A: 接收端只能统计 Hook 实际上报的事件。缺 PostToolUse 时用 `scripts/count-valid-tc.py` 核 `agent-hooks.log` 补数。
