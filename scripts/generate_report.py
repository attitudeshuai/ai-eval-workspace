#!/usr/bin/env python3
"""汇总会话评估结果到 benchmarks/。"""

import argparse
import csv
import json
from pathlib import Path

from utils.helpers import load_toml, project_dir, workspace_root


def get_task_prefix(project_id: str) -> str:
    config_path = project_dir(project_id) / "config.toml"
    if config_path.exists():
        data = load_toml(config_path)
        return data.get("project", {}).get("task_prefix", "task")
    return "task"


def generate_session_report(session_name: str) -> Path:
    session_dir = workspace_root() / "sessions" / session_name
    reports_dir = session_dir / "projects"
    benchmarks_dir = workspace_root() / "benchmarks"
    benchmarks_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for project_dir_path in sorted(reports_dir.glob("*")):
        if not project_dir_path.is_dir():
            continue
        project_id = project_dir_path.name
        prefix = get_task_prefix(project_id)
        for task_dir in sorted(project_dir_path.glob(f"{prefix}-*")):
            task_id = task_dir.name
            for agent_dir in sorted(task_dir.iterdir()):
                if not agent_dir.is_dir():
                    continue
                agent = agent_dir.name
                report_file = agent_dir / "report.json"
                if not report_file.exists():
                    continue
                report = json.loads(report_file.read_text(encoding="utf-8"))
                rows.append({
                    "session": session_name,
                    "project_id": project_id,
                    "task_id": task_id,
                    "agent": agent,
                    "total_score": report.get("total_score", 0),
                })

    # 写入全局 CSV
    csv_path = benchmarks_dir / "global" / "summary.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["session", "project_id", "task_id", "agent", "total_score"])
        if f.tell() == 0:
            writer.writeheader()
        writer.writerows(rows)

    # 按项目写入 CSV
    by_project: dict[str, list[dict]] = {}
    for row in rows:
        by_project.setdefault(row["project_id"], []).append(row)

    for project_id, project_rows in by_project.items():
        project_csv = benchmarks_dir / "by-project" / project_id / "summary.csv"
        project_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(project_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["session", "project_id", "task_id", "agent", "total_score"])
            if f.tell() == 0:
                writer.writeheader()
            writer.writerows(project_rows)

    # 生成全局 leaderboard
    leaderboard = {}
    for row in rows:
        key = row["agent"]
        if key not in leaderboard:
            leaderboard[key] = {"tasks": 0, "total": 0.0}
        leaderboard[key]["tasks"] += 1
        leaderboard[key]["total"] += row["total_score"]

    md = "# Global Leaderboard\n\n"
    md += "| Agent | 任务数 | 平均分 |\n|---|---|---|\n"
    for agent, stats in sorted(
        leaderboard.items(),
        key=lambda x: x[1]["total"] / x[1]["tasks"] if x[1]["tasks"] else 0,
        reverse=True,
    ):
        avg = stats["total"] / stats["tasks"] if stats["tasks"] else 0
        md += f"| {agent} | {stats['tasks']} | {avg:.4f} |\n"

    (benchmarks_dir / "global" / "leaderboard.md").write_text(md, encoding="utf-8")

    return csv_path


def main():
    parser = argparse.ArgumentParser(description="生成会话报告")
    parser.add_argument("--session", required=True, help="会话名称")
    args = parser.parse_args()

    csv_path = generate_session_report(args.session)
    print(f"全局报告已更新: {csv_path}")
    print(f"排行榜: {csv_path.parent / 'leaderboard.md'}")


if __name__ == "__main__":
    main()
