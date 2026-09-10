# 任务信息文件模板（task-info.md）

> 每任务一份，存放**共享的运行环境字段**（同一任务各轮填同一组值）。文件名固定 `task-info.md`（放在 `records/{项目}/{项目}-{类型}/` 下）。
> 使用 `## 字段` 小标题结构，值可多行；导出脚本按 `## ` 切块解析，请勿改动标题文本。

```markdown
# {项目}-{类型}-{索引} 任务信息（运行环境元信息）

## 任务名
{项目}-{类型}-{索引}  （= 副本目录名 = 提示词名 = 容器工作目录名，如 app-12-bugfix-01）

## 项目（素材源）
{项目}  （source-code/{项目}/ 的目录名；一份素材源按类型复制成多份任务副本）

## 任务标题
<一句话说明这题让模型做什么>

## 任务类型
<0-1代码生成 / Feature迭代 / Bug修复 / 代码理解 / 代码重构 / 工程化 / 代码测试；本任务主类型，决定初始快照/埋点策略>

## 标注人
<TPM/专家名>

## 创建日期
<YYYY-MM-DD>

## Repo URL
<https://github.com/<org>/<repo>，去掉 .git>

## 本地路径
<任务副本路径，如 sessions/cc-solo/{SESSION_NAME}/source-code/app-12/app-12-bugfix/app-12-bugfix-01>

## 初始环境快照
<https://github.com/<org>/<repo>/commit/<40位完整SHA>>

## Harness
<Claude Code>

## Harness版本
<客户端版本号，必填>

## 操作系统
<MacOS/Linux / Windows>

## 环境可复现等级
<无外部依赖 / 有外部依赖，未容器化 / 已容器化，可一键起环境>

## SessionID
<整个会话窗口 ID，所有轮同一值；首轮完成后回填>

## 轨迹根目录（轨迹文件）
<Claude Code（容器做，题号 = 任务 ID）→ records/{任务}/{任务}-trajectory.jsonl（来源容器 /home/node/.claude/projects/-workspace-<题号>/<SessionID>.jsonl）；首轮 SessionID 回填后定位>
```

## 字段说明

| 字段 | 说明 |
|------|------|
| 任务名 | `{项目}-{类型}-{索引}`（如 `app-12-bugfix-01`）= 记录目录名 = 副本目录名 = 容器工作目录名 |
| 项目（素材源） | 素材源目录名（`source-code/{项目}/`，如 `app-12`）；一份素材源按类型复制多份任务副本 |
| 初始环境快照 | 会话首轮前的工作区 commit permalink；完整 40 位 SHA；同一任务各轮同一值；不同任务（即使同仓库）各指向自己的 baseline commit |
| Harness/版本/OS/可复现等级 | 运行环境字段；Harness 升级会改 system prompt/工具集，版本必填 |
| SessionID | 首轮完成后由 `02-round-capture` 回填 |
| 轨迹根目录 | Claude Code→`records/{任务}/{任务}-trajectory.jsonl`（嵌套布局写作 `records/{项目}/{任务}/{任务}-trajectory.jsonl`，来自容器导出）；提交表「轨迹文件」列据此生成 |

## 注意事项

- 快照 commit 必须是首轮交互前状态；之后禁止 force-push / rebase 改写。
- 凭据（.env/密钥/token）不进仓库；push 到评测团队可访问远端（设为 public 公开仓库，或至少加协作者）。
- 写中文文件一律用写文件工具（UTF-8）。
