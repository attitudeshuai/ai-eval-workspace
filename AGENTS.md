# AI Agent 使用说明

本文件面向在此仓库中工作的 AI Agent。

---

## 核心原则

**本工作台对项目内部结构不做强制要求。** 每个 `projects/<project-id>/` 都是自治的评估项目。

## 当前项目列表

| 项目 ID | 类型 | 入口 Skill | 说明 |
|---------|------|-----------|------|
| `webdev-long-horizon` | Web 开发评估 | `SKILL.md` | 高难度 Web Dev 长程任务 |
| `pairwise-gsb` | 生图标注 | `skills/gsb-annotator/SKILL.md` | AI 生图 Pairwise GSB 标注 |
| `code-eval-solo` | 代码评估 | `SKILL.md` | 单模型代码能力批量评估 |
| `code-eval-gsb` | 代码评估 | `SKILL.md` | 多模型代码对比评估（GSB） |
| `swe-like` | 代码评估 | `SKILL.md` | SWE-like 长程代码任务题库（Trae+Seed 单 Prompt） |
| `repo-fetcher` | 素材池 | `SKILL.md` | 专门拉取 GitHub 仓库（黑名单记录已用过的仓库，自动跳过） |

## 共享资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 代码评价 Agent | `skills/implementation-reviewer/SKILL.md` | 6 维度全栈代码评价 |
| 去 AI 化 Agent | `skills/humanizer-zh/SKILL.md` | 去除 AI 写作痕迹 |
| 提示词生成 Agent | `skills/prompt-architect/SKILL.md` | 基于源码批量出题 |
| Excel 对比 | `skills/excel-diff/compare_excel.py` | CSV/Excel 列对比 |
| 识图 Agent | `skills/vision/SKILL.md` | 无视觉模型识图（vision.js 调千问/OpenAI 兼容 API） |
| 项目接入指南 | `docs/project-onboarding.md` | 新项目最小接入 |
| 工作台配置 | `config/workspace.toml` | 工作台级元数据 |

## 识图能力

如果底层模型不具备原生识图能力，遇到图片**不要用 Read 工具**，改用：

```bash
node skills/vision/vision.js "<图片路径>" "用中文描述这张图片"
```

网络图片用 `--url` 参数。触发场景：用户分享图片路径（本地或网络 URL）、消息中出现 "Saved attachments:" 并列出图片、用户要求分析/描述/识别图片内容。对每张图片依次执行，拿到所有文字描述后再回复。

配置（Key、模型名）在 `skills/vision/.env`，详见 `skills/vision/SKILL.md`。

## 各项目典型工作流

### code-eval-solo（单模型代码评估）

```
源码准备 → 提示词生成 → Trae 执行 → 分析评价 → 导出 CSV
```

详见 `projects/code-eval-solo/docs/runbook.md`

### code-eval-gsb（多模型对比评估）

```
GitLab clone → GitHub push → 分支创建 → 提示词生成 → Trae 执行 → 轮次评价 → 汇总
```

详见 `projects/code-eval-gsb/docs/runbook.md`

### webdev-long-horizon

详见 `projects/webdev-long-horizon/SKILL.md`

### repo-fetcher（仓库拉取器）

```
list 搜候选 → 写进 wishlist.txt → pull --file 批量拉取 → status 盘点 → blacklist add 标记已用过
```

详见 `projects/repo-fetcher/docs/runbook.md`

## 你不能做什么

- 不要假设所有项目使用同一套任务模板
- 不要修改 `projects/<id>/` 中已冻结任务或参考答案，除非用户明确授权
- 不要提交 `secrets.toml` 到 Git
- 工作数据（`sessions/code-eval-*/` 下的 `source code/` 和 `ai-model-result/`）默认 gitignore，勿提交
- 不要用 PowerShell 的 `Set-Content`/`Get-Content` 改写含中文（非 ASCII）的文本文件——会把 UTF-8 当 GBK 读写导致乱码。改文件内容一律用 write/edit 工具（它们正确处理 UTF-8）

## 工作前必读

- [projects/code-eval-solo/SKILL.md](./projects/code-eval-solo/SKILL.md) — 单模型代码评估入口
- [projects/code-eval-solo/docs/runbook.md](./projects/code-eval-solo/docs/runbook.md) — Solo 操作手册
- [projects/code-eval-solo/docs/structure-example.md](./projects/code-eval-solo/docs/structure-example.md) — 目录结构样例
- [projects/code-eval-gsb/SKILL.md](./projects/code-eval-gsb/SKILL.md) — 多模型代码对比入口
- [projects/code-eval-gsb/docs/runbook.md](./projects/code-eval-gsb/docs/runbook.md) — GSB 操作手册
- [projects/webdev-long-horizon/SKILL.md](./projects/webdev-long-horizon/SKILL.md) — Web Dev 实操流程
- [projects/swe-like/SKILL.md](./projects/swe-like/SKILL.md) — SWE-like 长程代码任务入口
- [projects/repo-fetcher/SKILL.md](./projects/repo-fetcher/SKILL.md) — 仓库拉取器入口（含黑名单）
