# AI Agent 使用说明

本文件面向在此仓库中工作的 AI Agent。

---

## 核心原则

**本工作台对项目内部结构不做强制要求。** 每个 `projects/<project-id>/` 都是自治的评估项目，可以有自己的任务格式、模板、测试方式和文档。

## 你能做什么

1. **onboard 项目**：使用 `scripts/create_project.py` 在 `projects/` 下创建新项目。
2. **组织项目内容**：根据项目需求自由创建任务、prompt、测试、Rubric、文档等。
3. **运行 SOTA**：使用 `scripts/run_sota.py` 为指定项目创建隔离会话。
4. **评估**：使用 `scripts/evaluate_task.py` 或项目自己的评估方式生成报告。
5. **汇总**：使用 `scripts/generate_report.py` 更新基准。

## 你不能做什么

- 不要假设所有项目都使用 `webdev-long-horizon` 的任务模板。
- 不要修改 `projects/<id>/` 中已冻结任务或参考答案，除非用户明确授权。
- 不要公开发布任务截图、Rubric 或参考来源。

## 工作前必读

- [docs/project-onboarding.md](./docs/project-onboarding.md) — 新项目接入
- [docs/workflow.md](./docs/workflow.md) — 评估流程参考
- [docs/quality-gates.md](./docs/quality-gates.md) — 任务交付质量闸门
- [projects/webdev-long-horizon/OPERATIONAL_WORKFLOW.md](./projects/webdev-long-horizon/OPERATIONAL_WORKFLOW.md) — Web Dev 实操流程
- [projects/webdev-long-horizon/docs/task-template-guide.md](./projects/webdev-long-horizon/docs/task-template-guide.md) — Web Dev 任务模板（仅参考）

## 常用命令

```bash
# onboard 新项目
python scripts/create_project.py --id <project-id> --name "..."

# 运行 SOTA
python scripts/run_sota.py --session <name> --project <id> --task <task-id> --agent codex

# 从远程机器回收 SOTA 产物
python scripts/fetch_remote_results.py --task <task-id> --agent codex --session <name>

# 评估
python scripts/evaluate_task.py --session <name> --project <id> --task <task-id> --agent codex

# 汇总
python scripts/generate_report.py --session <name>
```

## 输出产物位置

- SOTA 产物：`sessions/<session>/projects/<project-id>/submissions/<task-id>/<agent>/`
- 评估报告：`sessions/<session>/projects/<project-id>/reports/<task-id>/<agent>/`
- 全局汇总：`benchmarks/global/`
- 项目汇总：`benchmarks/by-project/<project-id>/`
