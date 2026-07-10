# 评估流程参考

本文档描述在工作台中运行一次评估的参考流程。注意：**这只是参考，不同项目可以完全自定义自己的流程。**

---

## 阶段一：项目准备

1. 使用 `scripts/create_project.py` onboard 新项目（或直接手动创建 `config.toml`）。
2. 在项目中组织自己的任务、prompt、测试、Rubric。
3. 确保项目 `config.toml` 正确填写。

---

## 阶段二：准备任务与运行环境

根据项目自身需求准备：

- 任务说明文档
- 初始代码或环境
- 测试或验收脚本
- 参考截图或数据（如需要）

项目可以自由选择格式，不需要遵循 `webdev-long-horizon` 的模板。

---

## 阶段三：运行 SOTA

```bash
python scripts/run_sota.py \
  --session session-sota-2026-07-001-codex \
  --project <project-id> \
  --task <task-id> \
  --agent codex
```

`run_sota.py` 会为项目创建一个隔离的运行目录：

```text
sessions/session-sota-2026-07-001-codex/
  projects/<project-id>/
    submissions/<task-id>/<agent>/
      source/              # agent 可修改的代码目录
      screenshots/         # 截图
      transcript.md        # 运行轨迹
      ...
```

项目可以在自己的 README 中说明 agent 需要如何运行、测试、提交产物。

---

## 阶段四：评估

```bash
python scripts/evaluate_task.py \
  --session session-sota-2026-07-001-codex \
  --project <project-id> \
  --task <task-id> \
  --agent codex
```

项目自行决定评估方式：

- 使用项目自己的测试脚本
- 使用项目自己的 Rubric
- 使用 LLM judge 或人工 review

工作台只提供评估产物的存放位置：`sessions/<session>/projects/<project-id>/reports/<agent>/`。

---

## 阶段五：汇总

```bash
python scripts/generate_report.py --session session-sota-2026-07-001-codex
```

该命令会：

- 读取会话中所有项目的评估报告。
- 更新 `benchmarks/global/summary.csv` 与 `benchmarks/global/leaderboard.md`。
- 为每个项目更新 `benchmarks/by-project/<project-id>/summary.csv`。

---

## 流程图

```text
onboard 项目 → 准备任务/环境 → 运行 SOTA → 评估 → 汇总基准
```

每个阶段的具体实现由项目自行定义。
