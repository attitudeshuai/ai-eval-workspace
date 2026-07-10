# Task Creator

在指定项目中创建符合规范的高难度长程任务。

## 触发条件

当用户要求创建新任务、设计任务需求、或生成任务骨架时调用本技能。

## 工作流程

1. 确认目标项目 ID（如未指定，询问用户）。
2. 读取 `config/categories.json` 确认可选标签。
3. 使用 `python scripts/create_task.py --project <id>` 生成任务骨架。
4. 填充 `task.md`：背景、目标、功能、交互、视觉、约束、交付标准。
5. 准备 `starter/` 初始项目、`assets/` 参考截图、`mock-data/` 数据。
6. 设计 `rubric.json`（10-20 个叶节点，覆盖六维度）。
7. 填写 `target_states.md` 与 `README.md`。
8. 运行 `python scripts/validate_task.py projects/<id>/tasks/<task-id>` 自检。

## 输出规范

- 任务必须迫使 agent 进入“实现 → 运行 → 观察 → 修复”闭环。
- 必须包含视觉参考截图。
- 必须覆盖至少 4 类关键状态。
- starter 必须能本地启动。

## 禁止事项

- 不得在 task.md 或 starter 中泄露答案。
- 不得依赖外部登录、付费 API、不可控实时数据。
- 不得使用模糊视觉描述（如“高级、现代、美观”）。
