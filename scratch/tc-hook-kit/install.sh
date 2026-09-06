#!/usr/bin/env bash
# 配置 IP+端口，安装 Trae Hook 并写入 Bridge 配置。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BRIDGE="$ROOT/bridge.js"
HOOKS_PATH="${HOOKS_PATH:-$HOME/.trae-cn/hooks.json}"
CONFIG_DIR="${CONFIG_DIR:-$HOME/.tc-hook-kit}"
CONFIG_FILE="$CONFIG_DIR/config.json"
BRIDGE_CONFIG="$CONFIG_DIR/bridge.json"
SAFE_DIR="/tmp/tc-hook-kit"
SIDECAR="$ROOT/bridge.runtime.json"

HOST=""
PORT=""
SERVER_URL=""

usage() {
  cat <<EOF
用法: $(basename "$0") --host <IP或域名> --port <端口>
      $(basename "$0") --server http://192.168.1.10:8765

示例:
  $(basename "$0") --host 192.168.1.10 --port 8765
  $(basename "$0") --server http://127.0.0.1:8765

会先启动接收端（另终端）:
  python3 $ROOT/server.py --host 0.0.0.0 --port 8765
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --server) SERVER_URL="$2"; shift 2 ;;
    --hooks-path) HOOKS_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$SERVER_URL" ]]; then
  if [[ -z "$HOST" || -z "$PORT" ]]; then
    echo "请提供 --host + --port，或 --server URL" >&2
    usage
    exit 1
  fi
  SERVER_URL="http://${HOST}:${PORT}"
fi

if [[ ! -f "$BRIDGE" ]]; then
  echo "未找到 bridge.js: $BRIDGE" >&2
  exit 1
fi

mkdir -p "$CONFIG_DIR" "$SAFE_DIR"
chmod 700 "$CONFIG_DIR"

if [[ -f "$CONFIG_FILE" ]]; then
  HOOK_SECRET="$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['hook_secret'])" 2>/dev/null || true)"
fi
if [[ -z "${HOOK_SECRET:-}" ]]; then
  HOOK_SECRET="$(openssl rand -hex 32)"
fi

python3 - <<PY
import json, os
cfg = {
  "server_url": "$SERVER_URL",
  "hook_secret": "$HOOK_SECRET",
  "data_dir": os.path.expanduser("~/.tc-hook-kit/data"),
}
path = "$CONFIG_FILE"
existing = {}
if os.path.exists(path):
    with open(path) as f:
        existing = json.load(f)
existing.update(cfg)
with open(path, "w") as f:
    json.dump(existing, f, indent=2)
    f.write("\n")
os.chmod(path, 0o600)
PY

BRIDGE_BODY="$(python3 - <<PY
import json
print(json.dumps({
  "server_url": "$SERVER_URL",
  "hook_secret": "$HOOK_SECRET",
  "error_log_path": "$SAFE_DIR/bridge-errors.log",
}, indent=2))
PY
)"

for target in "$BRIDGE_CONFIG" "$SAFE_DIR/bridge.json" "$SIDECAR"; do
  mkdir -p "$(dirname "$target")"
  printf '%s\n' "$BRIDGE_BODY" > "$target"
  chmod 600 "$target"
done

# 合并 hooks.json
mkdir -p "$(dirname "$HOOKS_PATH")"
if [[ -f "$HOOKS_PATH" ]]; then
  cp "$HOOKS_PATH" "${HOOKS_PATH}.bak-$(date +%s)"
fi

python3 - <<PY
import json, os
hooks_path = os.path.expanduser("$HOOKS_PATH")
bridge_path = "$BRIDGE"
bridge_cmd = "node " + json.dumps(bridge_path)
cfg = {"version": 1, "hooks": {}}
if os.path.exists(hooks_path):
    with open(hooks_path) as f:
        cfg = json.load(f)
cfg.setdefault("version", 1)
cfg.setdefault("hooks", {})
events = ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "Notification"]
for event in events:
    cfg["hooks"].setdefault(event, [])
    exists = any(
        isinstance(entry, dict)
        and any(h.get("command") == bridge_cmd for h in entry.get("hooks", []))
        for entry in cfg["hooks"][event]
    )
    if not exists:
        cfg["hooks"][event].append({
            "matcher": "",
            "hooks": [{"type": "command", "command": bridge_cmd, "timeout": 10}],
        })
with open(hooks_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
os.chmod(hooks_path, 0o600)
PY

cat <<EOF

✅ Trae Hook 已安装

  接收端 URL : $SERVER_URL
  Hook 配置  : $HOOKS_PATH
  Bridge     : $BRIDGE
  密钥文件   : $CONFIG_FILE  （server.py 须用同一 secret）

下一步:
  1. 启动接收端（若尚未启动）:
     python3 $ROOT/server.py --host 0.0.0.0 --port ${PORT:-$(python3 -c "from urllib.parse import urlparse; print(urlparse('$SERVER_URL').port or 8765)")}

  2. Trae → 设置 → Hooks，确认 6 类事件命令指向 bridge.js，并设为「自动运行」

  3. 跑完一题后查统计:
     curl -s "$SERVER_URL/stats" | python3 -m json.tool
     curl -s "$SERVER_URL/stats?session_id=<片段>" | python3 -m json.tool

  Bridge 失败日志: $SAFE_DIR/bridge-errors.log
  API 说明: $ROOT/API.md
EOF
