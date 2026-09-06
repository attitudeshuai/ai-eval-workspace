"""有效 TC 统计口径（PostToolUse + tool_use_id 去重）。"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

EXCLUDED = {
    "checkruncommandstatus",
    "getautorunconfig",
    "getconfigurationvalue",
    "getdiagnostics",
    "filediffcount",
    "getdocumentbyuri",
    "applychatsnapshotpatch",
}


def normalize_tool(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", name or "").lower()


def is_excluded(name: str) -> bool:
    norm = normalize_tool(name)
    return norm in EXCLUDED or "checkruncommandstatus" in norm


def event_type(payload: dict) -> str:
    for key in ("hook_event_name", "event_name", "event_type", "type"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def session_id(payload: dict) -> str:
    for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def tool_use_id(payload: dict) -> str:
    for key in ("tool_use_id", "toolUseId", "tool_call_id", "toolCallId"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def tool_name(payload: dict) -> str:
    for key in ("tool_name", "llm_tool_name", "toolName", "tool"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "?"


@dataclass
class SessionStats:
    valid_tc: int = 0
    by_tool: Counter[str] = field(default_factory=Counter)
    post_tool_use_rows: int = 0
    excluded_ids: int = 0


@dataclass
class AggregateStats:
    valid_tc: int = 0
    by_tool: Counter[str] = field(default_factory=Counter)
    by_session: dict[str, SessionStats] = field(default_factory=dict)
    event_counts: Counter[str] = field(default_factory=Counter)


def compute_stats(records: list[dict], session_filter: str | None = None) -> AggregateStats:
    """records 每项: {session_id, event_type, tool_use_id, tool_name}"""
    agg = AggregateStats()
    per_session: dict[str, dict[str, str]] = {}

    for row in records:
        sid = row.get("session_id") or ""
        if session_filter and session_filter not in sid:
            continue
        et = row.get("event_type") or ""
        agg.event_counts[et] += 1
        if et != "PostToolUse":
            continue
        tid = row.get("tool_use_id") or ""
        if not tid:
            continue
        name = row.get("tool_name") or "?"
        bucket = per_session.setdefault(sid or "(unknown)", {})
        bucket[tid] = name

    for sid, id_map in per_session.items():
        ss = SessionStats()
        ss.post_tool_use_rows = len(id_map)
        valid_map: dict[str, str] = {}
        for tid, name in id_map.items():
            if is_excluded(name):
                ss.excluded_ids += 1
            else:
                valid_map[tid] = name
        ss.valid_tc = len(valid_map)
        ss.by_tool = Counter(valid_map.values())
        agg.by_session[sid] = ss
        agg.valid_tc += ss.valid_tc
        agg.by_tool.update(ss.by_tool)

    return agg
