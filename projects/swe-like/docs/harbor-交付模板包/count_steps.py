#!/usr/bin/env python3
"""数一次 TraeX 运行跑了多少 steps，用来自查 task.toml 里的 effective_turns。

计数以 agent step 为单位：一次模型调用记为一个 step。具体到这里：

- 一批工具调用算一个 step，不管这批里有几个调用、是哪些工具
- 没带工具调用的回复也算一个 step，模型调用照样发生了：收尾答复，以及被截断
  或解析失败的响应
- 一次上下文压缩算一个 step，摘要是模型生成的，轨迹文件里不会另外记
- 子代理跑的每一轮都算。派给子代理的活，换个没有派活能力的 harness 就得在主
  循环里自己做完，把一个 40 轮的 spawn_agent 折成 1 个 step 会让不同 harness
  之间没法比。只要主循环的数就加 --no-subagents。

miniswe 用不上这个脚本：mini-swe-agent 的 .traj.json 里
info.model_stats.api_calls 就是它的 step 数。

用法：
  python3 count_steps.py ~/.trae/cli/sessions/2026/09/03/rollout-xxx.jsonl
  python3 count_steps.py <轨迹文件> --show          # 逐个 step 打印
  python3 count_steps.py <轨迹文件> --all-turns     # 统计整个文件而不是最后一轮
  python3 count_steps.py <轨迹文件> --no-subagents  # 只数主循环
  python3 count_steps.py <轨迹文件> --format json

提示：子代理的轨迹是另外的文件，要靠 sessions/ 目录结构才能找到。请直接对
.trae/cli/sessions/ 下的原始文件跑；把文件拷到别处再跑会漏掉子代理的轮数，
脚本检测到这种情况会给出提示。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CALL_SUFFIX = "_call"


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_number, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"第 {line_number} 行不是合法 JSON：{exc.msg}"
                ) from exc
            if not isinstance(item, dict):
                continue
            records.append(item)
    return records


def call_name(item: dict[str, Any]) -> str | None:
    """返回工具调用的名字，不是调用就返回 None。

    工具调用不都是 `function_call`：shell 和 patch 工具是 `custom_tool_call`
    （`exec`、`apply_patch`），`tool_search_call` / `web_search_call` 干脆不带
    名字，这时类型本身就是工具。
    """
    item_type = item.get("type")
    if not isinstance(item_type, str) or not item_type.endswith(CALL_SUFFIX):
        return None

    name = item.get("name")
    if isinstance(name, str) and name:
        return name
    return item_type[: -len(CALL_SUFFIX)]


def item_turn_id(item: dict[str, Any]) -> str | None:
    passthrough = item.get("internal_chat_message_metadata_passthrough")
    if isinstance(passthrough, dict):
        turn_id = passthrough.get("turn_id")
        if isinstance(turn_id, str):
            return turn_id
    return None


def collect_turn_ids(records: list[dict[str, Any]]) -> list[str]:
    """含有用户消息的 turn id，按文件顺序。"""
    turn_ids: list[str] = []

    for record in records:
        record_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue

        if record_type == "history_mutation":
            turn_id = payload.get("turn_id")
            items = payload.get("items")
            if not isinstance(turn_id, str) or not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "message" and item.get("role") == "user":
                    turn_ids.append(turn_id)
                    break
        elif record_type == "response_item":
            if payload.get("type") != "message" or payload.get("role") != "user":
                continue
            turn_id = item_turn_id(payload)
            if turn_id is not None:
                turn_ids.append(turn_id)

    return turn_ids


def is_assistant_message(item: dict[str, Any]) -> bool:
    return item.get("type") == "message" and item.get("role") == "assistant"


def session_meta(path: Path) -> dict[str, Any]:
    """session_meta 载荷，永远是第一条记录。"""
    try:
        with path.open("r", encoding="utf-8") as fh:
            record = json.loads(fh.readline() or "{}")
    except (OSError, json.JSONDecodeError):
        return {}
    if record.get("type") != "session_meta":
        return {}
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else {}


def spawn_parent(meta: dict[str, Any]) -> str | None:
    """父线程 id，只有 `spawn_agent` 建出来的会话才有。

    普通会话的 `source` 是 "cli" 这样的裸字符串，只有被 spawn 出来的才是嵌套对象。
    """
    node: Any = meta.get("source")
    for key in ("subagent", "thread_spawn", "parent_thread_id"):
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node if isinstance(node, str) else None


def sessions_root(path: Path) -> Path | None:
    """这个轨迹文件所在的 `sessions` 目录。

    轨迹存在 `<root>/sessions/YYYY/MM/DD/` 下，子代理的轨迹按它自己的开始日期
    落盘、不跟父会话同一天，所以要搜整棵树而不是只看同级目录。
    """
    for parent in path.parents:
        if parent.name == "sessions":
            return parent
    return None


def subagent_tree(path: Path, thread_id: str | None) -> list[dict[str, Any]]:
    """这个会话派生出来的轨迹文件，任意深度，按开始顺序。"""
    root = sessions_root(path)
    if root is None or not thread_id:
        return []

    by_parent: dict[str, list[dict[str, Any]]] = {}
    for candidate in root.glob("*/*/*/rollout-*.jsonl"):
        if candidate == path:
            continue
        meta = session_meta(candidate)
        parent = spawn_parent(meta)
        if parent is None:
            continue
        by_parent.setdefault(parent, []).append(
            {
                "path": candidate,
                "thread_id": meta.get("id"),
                "agent_path": meta.get("agent_path"),
                "timestamp": meta.get("timestamp"),
            }
        )

    found: list[dict[str, Any]] = []
    queue = [thread_id]
    seen = {thread_id}
    while queue:
        for child in sorted(
            by_parent.get(queue.pop(0), []), key=lambda c: c["timestamp"] or ""
        ):
            child_id = child["thread_id"]
            if child_id in seen:
                continue
            seen.add(child_id)
            found.append(child)
            queue.append(child_id)
    return found


def spawn_turns(records: list[dict[str, Any]]) -> dict[str, str]:
    """每个被 spawn 的 agent 名 -> 派生它的那个 `spawn_agent` 所在的 turn。

    只有按轮统计时才需要：子代理自己的记录带的是它自己的 turn id，说明不了是
    父会话哪一轮派的活。
    """
    mapping: dict[str, str] = {}

    def note(item: dict[str, Any], turn_id: str | None) -> None:
        if item.get("name") != "spawn_agent" or not turn_id:
            return
        try:
            args = json.loads(item.get("arguments") or "{}")
        except json.JSONDecodeError:
            return
        name = args.get("task_name")
        if isinstance(name, str) and name:
            mapping[name.rsplit("/", 1)[-1]] = turn_id

    for record in records:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        if record.get("type") == "history_mutation":
            items = payload.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        note(item, payload.get("turn_id"))
        elif record.get("type") == "response_item":
            note(payload, item_turn_id(payload))
    return mapping


def collect_steps(
    records: list[dict[str, Any]],
    target_turn_id: str | None,
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    current_turn_id: str | None = None
    # 正在拼装的那次模型调用的状态。`open_call` 是没带工具的回复也能被数到的原因：
    # calls 一直是空的，但我们知道确实产生过一次响应。
    open_call = False
    call_turn_id: str | None = None
    call_commit_id: str | None = None
    calls: list[dict[str, Any]] = []
    # 恢复和 fork 出来的会话会重放条目，同一次调用绝不能数两遍。
    seen_call_ids: set[str] = set()

    def flush() -> None:
        nonlocal open_call, call_turn_id, call_commit_id
        if not open_call and not calls:
            return
        turn_id = calls[0]["turn_id"] if calls else call_turn_id
        if target_turn_id is None or turn_id == target_turn_id:
            steps.append(
                {
                    "kind": "tool_batch" if calls else "reply",
                    "turn_id": turn_id,
                    "commit_id": calls[0]["commit_id"] if calls else call_commit_id,
                    "tool_count": len(calls),
                    "tool_names": [call["name"] for call in calls],
                }
            )
        calls.clear()
        open_call = False
        call_turn_id = None
        call_commit_id = None

    def take_call(
        item: dict[str, Any], turn_id: str | None, commit_id: str | None
    ) -> bool:
        """记一次工具调用，跳过重放。返回 True 表示这是个调用条目。"""
        name = call_name(item)
        if name is None:
            return False
        call_id = item.get("call_id") or item.get("id")
        if isinstance(call_id, str):
            if call_id in seen_call_ids:
                return True
            seen_call_ids.add(call_id)
        calls.append({"turn_id": turn_id, "commit_id": commit_id, "name": name})
        return True

    # 老格式里，一个 reasoning 条目或一条 assistant 消息就开启一次模型调用。
    # 连续出现的这类条目合并成一个边界，因为一次响应可以先发若干段 reasoning
    # 再发一条消息，然后才是工具调用。
    prev_was_boundary = False

    for record in records:
        record_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue

        if record_type == "turn_context":
            turn_id = payload.get("turn_id")
            if isinstance(turn_id, str):
                current_turn_id = turn_id
            continue

        if record_type == "compacted":
            # 压缩记录不带 turn_id，算给写这条记录时正在进行的那一轮。
            flush()
            prev_was_boundary = False
            if target_turn_id is None or current_turn_id == target_turn_id:
                steps.append(
                    {
                        "kind": "compaction",
                        "turn_id": current_turn_id,
                        "commit_id": None,
                        "window_number": payload.get("window_number"),
                        "tool_count": 0,
                        "tool_names": [],
                    }
                )
            continue

        if record_type == "history_mutation":
            flush()
            prev_was_boundary = False
            turn_id = payload.get("turn_id")
            if isinstance(turn_id, str):
                current_turn_id = turn_id
            items = payload.get("items")
            if not isinstance(items, list):
                continue
            commit_id = payload.get("commit_id")
            replied = False
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not take_call(item, turn_id, commit_id) and is_assistant_message(
                    item
                ):
                    replied = True
            if calls or replied:
                open_call = True
                call_turn_id = turn_id
                call_commit_id = commit_id
            flush()
            continue

        if record_type != "response_item":
            continue

        if payload.get("type") == "reasoning" or is_assistant_message(payload):
            if not prev_was_boundary:
                flush()
                open_call = True
                call_turn_id = item_turn_id(payload) or current_turn_id
            turn_id = item_turn_id(payload)
            if turn_id is not None:
                current_turn_id = turn_id
                if call_turn_id is None:
                    call_turn_id = turn_id
            prev_was_boundary = True
            continue

        prev_was_boundary = False

        if payload.get("type") == "message":
            # 用户或 developer 消息会终结模型上一次产出。
            flush()
            turn_id = item_turn_id(payload)
            if turn_id is not None:
                current_turn_id = turn_id
            continue

        # 输出紧跟在它对应的调用后面，所以不能让它终结这次调用：
        # 并行调用会和它们的输出交错。
        turn_id = item_turn_id(payload) or current_turn_id
        if take_call(payload, turn_id, None):
            current_turn_id = turn_id
            open_call = True
            if call_turn_id is None:
                call_turn_id = turn_id

    flush()
    return steps


SCOPE_LABEL = {
    "latest_turn": "本次 Prompt（文件里最后一个用户轮）",
    "all_turns": "整个轨迹文件的所有轮",
}


def print_text(path, steps, show, scope, subagents, warning):
    counts = Counter(
        tool_name for step in steps for tool_name in step.get("tool_names", [])
    )
    kinds = Counter(step.get("kind") for step in steps)
    n_sub = sum(agent["steps"] for agent in subagents)

    print("轨迹文件：%s" % path)
    print("统计范围：%s" % SCOPE_LABEL.get(scope, scope))
    print()
    print("steps：%d    <-- task.toml 的 effective_turns 填这个数" % len(steps))
    print(
        "  主循环 %d｜子代理 %d｜工具批次 %d｜纯回复 %d｜上下文压缩 %d"
        % (
            len(steps) - n_sub,
            n_sub,
            kinds["tool_batch"],
            kinds["reply"],
            kinds["compaction"],
        )
    )
    print("  工具调用共 %d 次，用到 %d 种工具" % (sum(counts.values()), len(counts)))

    if counts:
        print("\n工具分布：")
        for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print("  %-28s %d" % (name, count))

    if subagents:
        print("\n子代理：")
        for agent in subagents:
            print("  %s：%d steps" % (agent["agent_path"] or "(未命名)", agent["steps"]))
            print("    %s" % agent["path"])

    if show and steps:
        print("\n逐个 step：")
        for index, step in enumerate(steps, start=1):
            turn_id = step["turn_id"] or "-"
            suffix = "  agent=%s" % step["agent_path"] if step.get("agent_path") else ""
            if step.get("kind") == "compaction":
                window = step.get("window_number")
                print(
                    "  %d. 上下文压缩  turn_id=%s  window_number=%s%s"
                    % (index, turn_id, window if window is not None else "-", suffix)
                )
            elif step.get("kind") == "reply":
                print("  %d. 纯回复  turn_id=%s  tool_count=0%s" % (index, turn_id, suffix))
            else:
                print(
                    "  %d. 工具批次  turn_id=%s  tool_count=%d  tools=%s%s"
                    % (
                        index,
                        turn_id,
                        step.get("tool_count") or 0,
                        ",".join(step.get("tool_names", [])),
                        suffix,
                    )
                )

    if warning:
        print("\n提示：%s" % warning)


def print_json(path, steps, scope, selected_turn_id, subagents, warning):
    counts = Counter(
        tool_name for step in steps for tool_name in step.get("tool_names", [])
    )
    kinds = Counter(step.get("kind") for step in steps)
    n_sub = sum(agent["steps"] for agent in subagents)
    json.dump(
        {
            "trajectory": str(path),
            "scope": scope,
            "turn_id": selected_turn_id,
            "steps": len(steps),
            "steps_main": len(steps) - n_sub,
            "tool_batches": kinds["tool_batch"],
            "replies": kinds["reply"],
            "compactions": kinds["compaction"],
            "subagent_steps": n_sub,
            "subagents": [
                {"agent_path": a["agent_path"], "path": str(a["path"]), "steps": a["steps"]}
                for a in subagents
            ],
            "tool_calls": sum(counts.values()),
            "unique_tools": len(counts),
            "tool_breakdown": dict(sorted(counts.items())),
            "warning": warning,
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="数一次 TraeX 运行跑了多少 steps，用来自查 effective_turns。"
    )
    ap.add_argument("trajectory", help="轨迹 JSONL 文件路径")
    ap.add_argument("--show", action="store_true", help="逐个 step 打印")
    ap.add_argument(
        "--all-turns",
        action="store_true",
        help="统计整个文件，而不是只统计最后一个用户轮",
    )
    ap.add_argument(
        "--no-subagents", action="store_true", help="只数主循环，不含子代理"
    )
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args()

    path = Path(args.trajectory).expanduser()
    if not path.is_file():
        print("错误：找不到文件或不是文件：%s" % path, file=sys.stderr)
        return 1

    try:
        records = iter_jsonl(path)
    except ValueError as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误：读不了 %s：%s" % (path, exc), file=sys.stderr)
        return 2

    if not records:
        print("错误：%s 是空文件，没有可统计的记录。" % path, file=sys.stderr)
        return 2

    user_turn_ids = collect_turn_ids(records)
    if args.all_turns:
        selected_turn_id, scope = None, "all_turns"
    else:
        selected_turn_id = user_turn_ids[-1] if user_turn_ids else None
        scope = "latest_turn"

    steps = collect_steps(records=records, target_turn_id=selected_turn_id)

    warning = None
    subagents: list[dict[str, Any]] = []
    if not args.no_subagents:
        meta = session_meta(path)
        if sessions_root(path) is None:
            # 文件被拷出 sessions/ 目录后就没法按父子关系找到子代理的轨迹了。
            # 静默少算会让 effective_turns 偏小，所以这里必须说出来。
            warning = (
                "这个文件不在 .trae/cli/sessions/ 目录下，找不到子代理的轨迹文件，"
                "上面的 steps 只含主循环。跑过 spawn_agent 的话请直接对 "
                ".trae/cli/sessions/ 下的原始文件重跑一次。"
            )
        else:
            turn_of = spawn_turns(records) if selected_turn_id else {}
            for child in subagent_tree(path, meta.get("id")):
                name = (child["agent_path"] or "").rsplit("/", 1)[-1]
                if selected_turn_id and turn_of.get(name) != selected_turn_id:
                    continue
                child_steps = collect_steps(
                    records=iter_jsonl(child["path"]), target_turn_id=None
                )
                for step in child_steps:
                    step["agent_path"] = child["agent_path"]
                subagents.append(
                    {
                        "agent_path": child["agent_path"],
                        "path": str(child["path"]),
                        "steps": len(child_steps),
                    }
                )
                steps.extend(child_steps)

    if args.format == "json":
        print_json(path, steps, scope, selected_turn_id, subagents, warning)
    else:
        print_text(path, steps, args.show, scope, subagents, warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
