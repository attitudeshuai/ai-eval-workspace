#!/usr/bin/env python3
"""轻量 Trae Hook 接收端：收事件、验签、统计有效 TC。"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from tc_stats import (
    AggregateStats,
    compute_stats,
    event_type,
    session_id,
    tool_name,
    tool_use_id,
)

BEIJING = timezone.utc  # 存储用 ISO；展示可另加 +8


def canonical_json(value: Any) -> str:
    if value is None or not isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(v) for v in value) + "]"
    obj = value
    return (
        "{"
        + ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + canonical_json(obj[k])
            for k in sorted(obj.keys())
        )
        + "}"
    )


def sign_envelope(secret: str, timestamp: str, body: dict) -> str:
    digest = hmac.new(
        secret.encode(),
        f"{timestamp}.{canonical_json(body)}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, timestamp: str | None, signature: str | None, body: dict) -> bool:
    if not timestamp or not signature or not timestamp.isdigit():
        return False
    if abs(time.time() * 1000 - int(timestamp)) > 5 * 60_000:
        return False
    expected = sign_envelope(secret, timestamp, body)
    return hmac.compare_digest(expected, signature)


def default_config_path() -> Path:
    return Path.home() / ".tc-hook-kit" / "config.json"


def default_data_dir() -> Path:
    return Path.home() / ".tc-hook-kit" / "data"


class EventStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "events.sqlite3"
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hook_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_id TEXT NOT NULL UNIQUE,
                  session_id TEXT NOT NULL DEFAULT '',
                  event_type TEXT NOT NULL DEFAULT '',
                  tool_use_id TEXT,
                  tool_name TEXT,
                  payload_json TEXT NOT NULL,
                  received_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hook_events_session ON hook_events(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hook_events_type ON hook_events(event_type)"
            )

    def insert(self, event_id: str, payload: dict) -> bool:
        sid = session_id(payload)
        et = event_type(payload)
        tid = tool_use_id(payload) or None
        tname = tool_name(payload) if tid else None
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
        with self._lock, sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO hook_events
                      (event_id, session_id, event_type, tool_use_id, tool_name, payload_json, received_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (event_id, sid, et, tid, tname, json.dumps(payload, ensure_ascii=False), now),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def list_records(self, session_filter: str | None = None) -> list[dict]:
        query = "SELECT session_id, event_type, tool_use_id, tool_name FROM hook_events"
        params: tuple = ()
        if session_filter:
            query += " WHERE session_id LIKE ?"
            params = (f"%{session_filter}%",)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "session_id": r[0],
                "event_type": r[1],
                "tool_use_id": r[2] or "",
                "tool_name": r[3] or "?",
            }
            for r in rows
        ]

    def stats(self, session_filter: str | None = None) -> AggregateStats:
        return compute_stats(self.list_records(session_filter), session_filter)


class Handler(BaseHTTPRequestHandler):
    store: EventStore
    hook_secret: str

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _send_json(self, code: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/health":
            self._send_json(200, {"ok": True, "service": "tc-hook-kit"})
            return

        if parsed.path == "/stats":
            session_filter = (qs.get("session_id") or [None])[0]
            stats = self.store.stats(session_filter)
            sessions = {}
            for sid, ss in stats.by_session.items():
                sessions[sid] = {
                    "valid_tc": ss.valid_tc,
                    "by_tool": dict(ss.by_tool.most_common()),
                    "post_tool_use_ids": ss.post_tool_use_rows,
                    "excluded_ids": ss.excluded_ids,
                }
            self._send_json(
                200,
                {
                    "valid_tc": stats.valid_tc,
                    "session_id_filter": session_filter,
                    "by_session": sessions,
                    "by_tool": dict(stats.by_tool.most_common()),
                    "event_counts": dict(stats.event_counts),
                    "rule": "PostToolUse + tool_use_id 去重，排除轮询/配置/补丁类工具",
                },
            )
            return

        if parsed.path == "/sessions":
            stats = self.store.stats()
            self._send_json(
                200,
                {
                    "sessions": sorted(stats.by_session.keys()),
                    "count": len(stats.by_session),
                },
            )
            return

        self._send_json(404, {"error": "NOT_FOUND"})

    def do_POST(self) -> None:
        if self.path != "/hooks/trae":
            self._send_json(404, {"error": "NOT_FOUND"})
            return

        body = self._read_json()
        if body is None:
            self._send_json(400, {"error": "INVALID_JSON"})
            return

        timestamp = self.headers.get("X-Swemarkup-Timestamp") or self.headers.get("x-swemarkup-timestamp")
        signature = self.headers.get("X-Swemarkup-Signature") or self.headers.get("x-swemarkup-signature")
        if not verify_signature(self.hook_secret, timestamp, signature, body):
            self._send_json(401, {"error": "INVALID_SIGNATURE"})
            return

        event_id = body.get("event_id")
        payload = body.get("payload")
        if not isinstance(event_id, str) or not isinstance(payload, dict):
            self._send_json(400, {"error": "INVALID_ENVELOPE"})
            return

        inserted = self.store.insert(event_id, payload)
        sid = session_id(payload)
        stats = self.store.stats(None)
        session_stats = None
        if sid:
            for key, ss in stats.by_session.items():
                if sid in key or key in sid:
                    session_stats = ss
                    break

        self._send_json(
            200,
            {
                "ok": True,
                "inserted": inserted,
                "duplicate": not inserted,
                "event_type": event_type(payload),
                "session_id": sid,
                "valid_tc": session_stats.valid_tc if session_stats else stats.valid_tc,
            },
        )


def load_or_create_secret(config_path: Path, secret_arg: str | None) -> str:
    if secret_arg:
        return secret_arg
    if config_path.exists():
        cfg = json.loads(config_path.read_text())
        if cfg.get("hook_secret"):
            return cfg["hook_secret"]
    secret = secrets.token_hex(32)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(config_path.read_text()) if config_path.exists() else {}
    cfg["hook_secret"] = secret
    config_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    config_path.chmod(0o600)
    print(f"已生成 hook_secret 并写入 {config_path}", file=sys.stderr)
    return secret


def main() -> int:
    parser = argparse.ArgumentParser(description="Trae Hook 轻量接收端")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0")
    parser.add_argument("--port", type=int, default=8765, help="监听端口，默认 8765")
    parser.add_argument("--secret", help="HMAC 密钥；省略则从 ~/.tc-hook-kit/config.json 读取或自动生成")
    parser.add_argument("--data-dir", type=Path, default=default_data_dir(), help="事件存储目录")
    parser.add_argument("--config", type=Path, default=default_config_path(), help="配置文件路径")
    args = parser.parse_args()

    secret = load_or_create_secret(args.config, args.secret)
    store = EventStore(args.data_dir)
    Handler.store = store
    Handler.hook_secret = secret

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}" if args.host != "0.0.0.0" else f"http://127.0.0.1:{args.port}"
    print(f"tc-hook-kit 接收端已启动: {url}", file=sys.stderr)
    print(f"  POST {url}/hooks/trae", file=sys.stderr)
    print(f"  GET  {url}/stats", file=sys.stderr)
    print(f"  GET  {url}/health", file=sys.stderr)
    print(f"  数据目录: {args.data_dir}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
