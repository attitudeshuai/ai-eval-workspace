# Evaluator

基于 Rubric 对指定项目的 Agent 产出进行证据化评估。

## 触发条件

当用户要求评估任务、打分、生成评估报告时调用本技能。

## 工作流程

1. 确认目标项目 ID 与任务 ID。
2. 读取 `projects/<id>/tasks/webdev-task-XXXX/rubric.json`。
3. 读取 SOTA 产物：`sessions/.../projects/<id>/submissions/<task-id>/<agent>/`。
4. 对每个 Rubric 叶节点收集证据：
   - `playwright_assertion`：运行 Playwright 测试
   - `screenshot_review`：检查关键状态截图
   - `dom_assertion`：检查 DOM 结构
   - `unit_test`：运行单元测试
   - `llm_judge`：使用 LLM 评估视觉/交互质量
   - `manual_review`：人工 review
5. 计算加权得分，生成 `report.json` 与 `report.md`。
6. 将证据保存到 `sessions/.../projects/<id>/reports/<task-id>/<agent>/evidence/`。

## 评分规则

- 每个叶节点 0-1 分。
- 最终得分 = Σ(得分 × 权重)。
- 无证据不得分。

## 输出格式

```markdown
# Evaluation Report: <project-id>/webdev-task-XXXX / codex

## 总分
0.82 / 1.00

## 维度得分
| 维度 | 权重 | 得分 |
|---|---|---|
| 功能完整性 | 0.30 | 0.90 |
...

## 详细评估

### r001: ...
- 得分：1.0
- 证据：...

## 主要问题
1. ...

## 建议
1. ...
```

## 注意事项

- 优先使用自动化证据。
- 视觉评估使用 LLM judge 或参考截图对比。
- 记录 agent 典型失败模式。
