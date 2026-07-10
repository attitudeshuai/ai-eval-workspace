# 质量闸门

任何任务在交付前必须通过以下全部闸门。任一闸门失败即阻塞交付。

这些闸门目前以人工检查清单为主；自动化辅助命令为：

```bash
python scripts/validate_task.py projects/<project-id>/tasks/<task-id>
```

对于 Web Dev 项目，也可以一次性校验整个项目：

```bash
python scripts/validate_project.py --project <project-id> --tasks
```

---

## 闸门 1：可运行性

- [ ] `starter/` 包含 lockfile（推荐）
- [ ] `npm install && npm run dev` 能在干净环境启动
- [ ] 项目无未声明依赖
- [ ] `README.md` 中启动说明清晰可复现

---

## 闸门 2：任务完整性

- [ ] `task.md` 包含背景、目标、功能、交互、视觉、约束、交付标准
- [ ] `metadata.json` 填写完整且标签合法
- [ ] `assets/` 包含桌面端和移动端参考截图
- [ ] `mock-data/` 提供必要业务数据
- [ ] `README.md` 说明目录结构、启动、测试、限制

---

## 闸门 3：视觉可验收性

- [ ] 高端视觉任务提供参考截图
- [ ] `task.md` 明确高保真区域与风格对齐区域
- [ ] 关键状态（hover、focus、空态、错误态）有截图或明确说明
- [ ] 响应式要求覆盖至少 2 个断点

---

## 闸门 4：Rubric 有效性

- [ ] `rubric.json` 包含合理数量的叶节点
- [ ] 叶节点覆盖功能、交互、视觉、工程、边界、测试等维度
- [ ] 无低价值叶节点（如“页面能打开”）
- [ ] 每个叶节点有明确的 `grader_spec` 和 `evidence_required`
- [ ] 权重之和为 1.0

---

## 闸门 5：可解性

- [ ] 至少一次 SOTA agent 运行记录
- [ ] SOTA 能完成核心链路
- [ ] 任务不是普通 agent 一次即可轻松完成的
- [ ] `sota-run.md` 记录运行时长、消耗、失败点

---

## 闸门 6：无污染风险

- [ ] `task.md` 和 `starter/` 不包含完整答案或关键实现代码
- [ ] SOTA 轨迹/参考答案不随任务一起公开
- [ ] 参考截图已脱敏（无真实品牌、个人信息）
- [ ] 任务未来自公开 benchmark 或包含其完整答案

---

全部通过后，任务状态可更新为 `approved`。
