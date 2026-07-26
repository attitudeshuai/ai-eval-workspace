---
name: evaluator
description: 'Evaluate agent submissions against rubric with evidence-based scoring. Use when evaluating tasks, scoring results, generating evaluation reports, 评估, 打分, 评估报告, 评分.'
---

# Evaluator

基于 Rubric 对指定项目的 Agent 产出进行证据化评估，生成加权评分报告。

## When to Use

- 用户要求评估任务结果
- 需要对 agent 产出打分
- 需要生成结构化的评估报告
- SOTA 运行完毕后需要量化评估

## 前置确认

调用前需确认：
- **项目 ID** 与 **任务 ID**
- **Agent 名称**（与 SOTA 运行一致）
- **Session 名称**
- 产物已就位：本地 `sessions/.../submissions/<task-id>/<agent>/` 或远程已回收

## Procedure

### 1. 读取 Rubric

读取 `projects/<project-id>/tasks/<task-id>/rubric.json`，获取评分维度、叶节点、权重。

Rubric 覆盖六维度：
- 功能完整性
- 视觉还原度
- 交互体验
- 代码质量
- 性能
- 边界状态处理

### 2. 定位 SOTA 产物

产物位置：
- **本地运行**：`sessions/<project-id>/<session>/submissions/<task-id>/`
- **远程运行**：需先用 `webdev-task-packer` skill 回收，或使用 `fetch_remote_results.py` 拉回

### 3. 逐项收集证据

对每个 Rubric 叶节点，按类型收集证据：

| 证据类型 | 方法 | 说明 |
|---------|------|------|
| `playwright_assertion` | 运行 Playwright 测试 | 自动化功能验证 |
| `screenshot_review` | 检查关键状态截图 | 对比 `assets/reference/` 参考截图 |
| `dom_assertion` | 检查 DOM 结构 | 验证元素存在性、属性、层级 |
| `unit_test` | 运行单元测试 | 代码级正确性 |
| `llm_judge` | LLM 评估 | 视觉/交互质量主观评估 |
| `manual_review` | 人工 review | 需要人工判断的维度 |

### 4. 运行评估脚本

```bash
python scripts/webdev-long-horizon/evaluate_task.py \
  --session <session-name> \
  --project <project-id> \
  --task <task-id> \
  --agent <agent>
```

### 5. 计算得分

- 每个叶节点得分：0.0 ~ 1.0
- 最终得分 = Σ(叶节点得分 × 权重)
- 无证据不得分

### 6. 生成报告

保存 `report.json` 与 `report.md` 到：
`sessions/<project-id>/<session>/reports/<task-id>/`

证据保存到同级 `evidence/` 目录。

## 输出格式

### report.md

```markdown
# Evaluation Report: <project-id>/<task-id> / <agent>

## 总分
0.82 / 1.00

## 维度得分
| 维度 | 权重 | 得分 |
|---|---|---|
| 功能完整性 | 0.30 | 0.90 |
| 视觉还原度 | 0.25 | 0.75 |
| 交互体验 | 0.20 | 0.85 |
| 代码质量 | 0.10 | 0.80 |
| 性能 | 0.10 | 0.70 |
| 边界状态 | 0.05 | 1.00 |

## 详细评估

### r001: 首页渲染
- 得分：1.0
- 证据类型：screenshot_review
- 证据：截图对比一致，布局正确

### r002: 购物车功能
- 得分：0.5
- 证据类型：playwright_assertion
- 证据：添加商品成功但删除失败，见 test-output/cart-fail.png

## 主要问题
1. 购物车删除功能未实现
2. 移动端布局在 320px 宽度下溢出

## 建议
1. 修复购物车删除 API 调用
2. 添加移动端响应式断点
```

## 注意事项

- 优先使用自动化证据（playwright_assertion、dom_assertion）
- 视觉评估优先使用 LLM judge，辅以参考截图对比
- 记录 agent 典型失败模式，用于后续任务改进
- 评估结果可用于 `generate_report.py` 更新全局基准
