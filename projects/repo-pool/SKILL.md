---
name: repo-pool
description: "开源仓库池：按标准从 GitHub 搜索、拉取、去重开源仓库，作为评估项目（code-eval-gsb 等）的出题源码素材。Use when: 拉取 GitHub 仓库, 开源项目搜索, 仓库素材池, 出题源码准备。"
---

# 开源仓库池（Repo Pool）

从 GitHub 按标准搜索、拉取、去重开源仓库，沉淀为评估项目出题用的源码素材池。

## 技能列表

| 序号 | 技能 | 文件 | 说明 |
|:--:|------|------|------|
| 1 | **仓库拉取** | [skills/01-pull-repos.md](skills/01-pull-repos.md) | list 搜候选 → pull 拉取（快照）+ 去重 → status 盘点 |

## 工作流程

```
list 搜索候选 → pull 拉取（--snapshot 快照）→ status 盘点 → 人工 copy 到评估项目
```

- **快照模式（默认）**：只取代码快照（tarball），重 `git init` 成干净 origin 仓，不含外部 remote/历史
- **去重主键**：GitHub `full_name`（owner/repo），先查 manifest 再查本地目录
- **拉取标准**：语言 / star / 活跃度 / 严禁关键词，见 `config.toml [criteria]`
- **不纳入 git**：`repos-manifest.json` 与 `repos/` 均为本地数据，不提交

## 命令

```
python scripts/repo-pool/fetch_repos.py list                  # 按标准搜候选（不 clone）
python scripts/repo-pool/fetch_repos.py pull <owner/repo>     # 快照拉取 + 去重
python scripts/repo-pool/fetch_repos.py status                # 盘点清单/目录一致性
```

## 文档

| 文档 | 说明 |
|------|------|
| [runbook.md](docs/runbook.md) | 逐步操作手册（指令模板） |
| [config.toml](config.toml) | 拉取标准 / 池路径 / 清单路径 |
