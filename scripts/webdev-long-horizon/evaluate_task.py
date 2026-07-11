#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""基于 Rubric 评估 Agent 提交。"""

import argparse
from datetime import datetime
from pathlib import Path

from utils.helpers import find_task_dir, load_json, save_json, workspace_root


def evaluate(session_name: str, project_id: str, task_id: str, agent: str, model: str = "gpt-5.6-sol") -> Path:
    session_dir = workspace_root() / "sessions" / session_name
    task_dir = find_task_dir(project_id, task_id)
    if task_dir is None:
        raise FileNotFoundError(f"找不到任务: {task_id}")
    submission_dir = session_dir / "projects" / project_id / "submissions" / task_id / agent
    report_dir = session_dir / "projects" / project_id / "reports" / task_id / agent
    evidence_dir = report_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    rubric = load_json(task_dir / "rubric.json")

    dimension_scores = []
    total_score = 0.0

    for dim in rubric.get("dimensions", []):
        dim_weight = dim.get("weight", 0)
        dim_score = 0.0
        leaves = []
        for leaf in dim.get("leaves", []):
            leaf_weight = leaf.get("weight", 0)
            score = 0.0  # 默认待评估
            leaves.append({
                "id": leaf.get("id"),
                "criterion": leaf.get("criterion"),
                "weight": leaf_weight,
                "score": score,
                "grader_spec": leaf.get("grader_spec"),
                "evidence_required": leaf.get("evidence_required"),
                "notes": "待人工或自动化评估",
            })
            dim_score += score * leaf_weight

        dimension_scores.append({
            "id": dim.get("id"),
            "name": dim.get("name"),
            "weight": dim_weight,
            "score": dim_score,
            "leaves": leaves,
        })
        total_score += dim_score * dim_weight

    report = {
        "project_id": project_id,
        "task_id": task_id,
        "agent": agent,
        "session": session_name,
        "total_score": round(total_score, 4),
        "dimensions": dimension_scores,
        "notes": "本报告为模板，需根据实际证据填充各叶节点得分。",
    }

    save_json(report_dir / "report.json", report)

    # 生成 markdown 报告
    md = f"# Evaluation Report: {project_id}/{task_id} / {agent}\n\n"
    md += f"**总分**: {total_score:.2f} / 1.00\n\n"
    md += "## 维度得分\n\n"
    md += "| 维度 | 权重 | 得分 |\n|---|---|---|\n"
    for dim in dimension_scores:
        md += f"| {dim['name']} | {dim['weight']:.2f} | {dim['score']:.2f} |\n"

    md += "\n## 详细评估\n\n"
    for dim in dimension_scores:
        md += f"### {dim['name']} (权重 {dim['weight']:.2f})\n\n"
        for leaf in dim["leaves"]:
            md += f"- **{leaf['id']}**: {leaf['criterion']}\n"
            md += f"  - 得分: {leaf['score']}\n"
            md += f"  - grader: `{leaf['grader_spec']}`\n"
            md += f"  - 证据: {', '.join(leaf['evidence_required'])}\n\n"

    (report_dir / "report.md").write_text(md, encoding="utf-8")

    # 更新任务目录的 sota-run.md（追加方式，不覆盖用户手动调整的内容）
    update_sota_run(task_dir, project_id, session_name, agent, model, total_score)

    return report_dir


def update_sota_run(task_dir: Path, project_id: str, session: str, agent: str, model: str, total_score: float) -> None:
    """追加一条 SOTA 运行记录到任务目录的 sota-run.md，不覆盖用户手动调整的内容。"""
    sota_run_path = task_dir / "sota-run.md"

    record = f"""## Run: {session}

- Agent: {agent}
- Model: {model}
- Date: {datetime.now().isoformat()}
- Total Score: {total_score:.4f} / 1.00
- Report: `sessions/{session}/projects/{project_id}/reports/{task_dir.name}/{agent}/`

"""

    if sota_run_path.exists():
        content = sota_run_path.read_text(encoding="utf-8")
        # 避免同一 session 重复追加
        if f"## Run: {session}" in content:
            return
        sota_run_path.write_text(content.rstrip() + "\n\n" + record, encoding="utf-8")
    else:
        header = f"# SOTA Run Records: {task_dir.name}\n\n"
        sota_run_path.write_text(header + record, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="评估 Agent 提交")
    parser.add_argument("--session", required=True, help="会话名称")
    parser.add_argument("--project", required=True, help="项目 ID")
    parser.add_argument("--task", required=True, help="任务 ID")
    parser.add_argument("--agent", default="codex", help="Agent 名称")
    parser.add_argument("--model", default="gpt-5.6-sol", help="模型名称，默认 gpt-5.6-sol")
    args = parser.parse_args()

    report_dir = evaluate(args.session, args.project, args.task, args.agent, args.model)
    print(f"评估报告已生成: {report_dir}")


if __name__ == "__main__":
    main()
