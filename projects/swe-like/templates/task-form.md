# 出题表单模板（SWE Task Form）

> 用于生成 `tasks/{task-id}/task.md`、`meta.json`、`verify-rubric.md`。需求必须独立提出，不照抄 Issues、热门讨论或既有题目。

## task.md（需求 Prompt 原文）

```markdown
为 <Repo 名> 增加/修复/重构……：<一句话目标>。

<场景与现状>：<真实使用场景、当前行为与痛点>。

<预期行为>：<可观察的预期行为，输入 → 输出，含边界情况>。

<非目标/约束>：<明确不做什么、不可破坏的既有行为>。
```

## meta.json

```json
{
  "task_id": "swe-{repo}-{序号}",
  "title": "题目名称",
  "repo_url": "https://github.com/<owner>/<repo>",
  "commit": "固定 Commit 或 Tag",
  "language": "主要语言（单选：Python / JavaScript/TypeScript / Rust / ...）",
  "task_type": "任务类型（单选：功能新增 / Bug 修复 / 测试增强 / 重构/性能 / 配置/工具链 / 其他 / 问题修复）",
  "seed_model": "Seed 模型/版本（默认 config.toml [run].model）"
}
```

> 注：提交人不写入 meta.json，飞书表格「提交人」字段有默认值，无需填写。

## verify-rubric.md

```markdown
# Verify Rubric

> 验收前固定，评判口径一致，不得根据模型结果事后调整标准。

① <可观察行为 + 输入条件 + 预期结果>
② <…>
③ <…>

<!-- 每条都应能被不同质检人稳定复现 -->
```

## 交付内容（供 task.md 或配套文档使用）

| 字段 | 内容 |
|------|------|
| 需求 Prompt | 上述 task.md 原文 |
| 真实性与难度说明 | 真实使用场景 + 难点所在（正确识别/幂等/避免重复/状态安全等） |
| 可能涉及模块 | 涉及的核心模块、接口、生命周期、状态持久化等 |
| Verify Rubric | 上述 verify-rubric.md |
| 验证产物 | 基于 mock/日志/可控状态的自动化测试与日志；不依赖稀缺外部状态 |

## 反例自查清单（存在任一即不收录）

- [ ] 需求是否无法由 Repo 独立实现？（依赖上游模型能力/安全策略 → 不收录）
- [ ] 需求是否已是 Repo 既有功能？（未查重 → 不收录）
- [ ] 需求是否与 Repo 定位不符？（超出框架/工具核心职责 → 不收录）
- [ ] Verify Rubric 是否主观不可复现？（“功能正常、体验良好”→ 需改写）
- [ ] Verify Rubric 是否写死文件/类名/实现方案？（行为正确的替代实现会被误判）
- [ ] Verify Rubric 是否依赖稀缺或不可访问的外部状态？（真实账户/真实额度 → 应允许 mock/日志）
