# 任务信息文件模板（task-info.md）

> 每任务目录一份，存放**共享的会话/运行环境字段**（同一会话各轮填同一组值）。文件名固定 `task-info.md`。
> 使用 `## 字段` 小标题结构，值可多行；导出脚本按 `## ` 切块解析，请勿改动标题文本。

```markdown
# {REPO} 任务信息（会话元信息）

## 任务 ID
{REPO}  （= 仓库目录名，如 solocc-0001）

## 任务标题
<一句话说明这题让模型做什么>

## 首轮任务类型
<0-1代码生成 / Feature迭代 / Bug修复 / 代码理解 / 代码重构 / 工程化 / 代码测试>

## 标注人
<TPM/专家名>

## 创建日期
<YYYY-MM-DD>

## Repo URL
<https://github.com/<org>/<repo>，去掉 .git>

## 本地路径
<工作区路径，如 sessions/claudccode/{SESSION_NAME}/repos/solocc-0001>

## 初始环境快照
<https://github.com/<org>/<repo>/commit/<40位完整SHA>>

## Harness
<Claude Code / Codex CLI>

## Harness版本
<客户端版本号，必填>

## 操作系统
<MacOS/Linux / Windows>

## 环境可复现等级
<无外部依赖 / 有外部依赖，未容器化 / 已容器化，可一键起环境>

## SessionID
<整个会话窗口 ID，所有轮同一值；首轮完成后回填>

## 轨迹根目录（轨迹文件）
<按哪个 CLI 做的分行：Codex CLI → ~/.codex/sessions/<SessionID>；Claude Code（容器做，题号 = 仓库目录名）→ records/{REPO}/{REPO}-trajectory.jsonl（来源容器 /home/node/.claude/projects/-workspace-<题号>/<SessionID>.jsonl）；首轮 SessionID 回填后定位>
```

## 字段说明

| 字段 | 说明 |
|------|------|
| 任务 ID | 仓库目录名（`repos/<repo>` 的目录名，如 `solocc-0001`）= 记录目录名；同仓库多窗口用后缀区分 |
| 初始环境快照 | 会话首轮前的工作区 commit permalink；完整 40 位 SHA；同一任务各轮同一值 |
| Harness/版本/OS/可复现等级 | 运行环境字段；Harness 升级会改 system prompt/工具集，版本必填 |
| SessionID | 首轮完成后由 `02-round-capture` 回填 |
| 轨迹根目录 | 轨迹目录须与 Harness 对应分行（Codex CLI→`~/.codex/sessions`、Claude Code→`records/{REPO}/{REPO}-trajectory.jsonl`，来自容器导出）；提交表「轨迹文件」列据此生成 |

## 注意事项

- 快照 commit 必须是首轮交互前状态；之后禁止 force-push / rebase 改写。
- 凭据（.env/密钥/token）不进仓库；push 到评测团队可访问远端。
- 写中文文件一律用写文件工具（UTF-8）。
