# 交付表单模板（SWE Delivery Form · 24 字段）

> 用于生成 `.tmp/{task-id}-delivery.json`，键名与飞书多维表格字段名**逐字一致**。字段类型与选项以脚本拉取到的表头为准（本模板记录 2026-09 拉取的新表 `FpWUbTe1qa36E2sEFiic0Hnjnxf` / `tblXHYLBoRMAfe5u` 实际 23 字段，另加试标新增字段 `commitUrl`）。
> 表单填写规范见 `docs/内部规范.md`：任何字段不得含 Markdown 标签，去 AI 味。

```json
{
  "题目名称": "<meta.json title>",
  "Type": "<单选：有效轮数 > 100 / 有效轮数 < 100 且 效果差 / 有效轮数 < 100 且 效果好>",
  "提交人": "",  // 不填写：飞书表格该字段有默认值
  "提交日期": "<YYYY-MM-DD，日期字段；若为自动创建时间则脚本跳过>",
  "Repo URL": "<meta.json repo_url>",
  "Commit/版本": "<meta.json commit>",
  "主要语言": "<单选：Go / Python（本轮仅限）>",
  "任务类型": "<单选：功能新增 / Bug 修复 / 测试增强 / 重构/性能 / 配置/工具链 / 其他 / 问题修复>",
  "需求 Prompt（原文）": "<task.md 原文复制，禁止改写>",
  "真实性与难度说明": "<出题交付>",
  "可能涉及模块": "<出题交付>",
  "Verify Rubric": "<verify-rubric.md 原文复制，禁止改写>",
  "产物结果": "<result.md 产物描述>",
  "产物补充材料": "<result.md 材料路径（patch / verifier 日志 / 失败测试列表及轨迹）>",
  "Seed 模型/版本": "<meta.json seed_model>",
  "Trae Session ID": "<run-log.md 原文复制，禁止改写>",
  "Trae Session ID 2": <数字，待确认；默认留空>,
  "有效轮数": <数字，= 模型输出步数（有效 TC 次数）>,
  "seed 轮次": "<文本，待确认；默认留空>",
  "是否完成需求": "<单选：完成 / 部分完成 / 未完成 / 无法判断>",
  "Reviewer": "<review.md 验收人>",
  "是否通过质检": "<单选：通过 / 未通过（题面验收未全部满足）>",
  "备注": "<review.md 收录判定（长程题/难题/不收录）及其他补充>",
  "commitUrl": "<fork 开源 repo 后、模型改完 commit 的 URL；填写规范待同步>"
}
```

## 字段来源速查

| 阶段 | 字段 |
|------|------|
| 出题 | 题目名称、Repo URL、Commit/版本、主要语言、任务类型、需求 Prompt（原文）、真实性与难度说明、可能涉及模块、Verify Rubric、Seed 模型/版本 |
| 运行 | 产物结果、产物补充材料、Trae Session ID、有效轮数（= 模型输出步数）、Trae Session ID 2（待确认）、seed 轮次（待确认）、commitUrl |
| 验收 | Type、是否完成需求、是否通过质检、Reviewer、备注 |
| 人工 | 提交日期（提交人有默认值，不填） |

## 查重与校验

- 脚本按 `config.toml [feishu].dedupe_field`（默认「题目名称」）查重，重复需 `--force`
- 单选字段只能写已有选项，多选值用顿号分隔；脚本对未知键名与非法选项直接报错并列出合法选项
