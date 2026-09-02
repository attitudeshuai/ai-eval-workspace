---
name: repo-fetcher
description: "仓库拉取器：从 GitHub 搜索、快照拉取、去重开源仓库；黑名单记录已用过的仓库，搜索与拉取自动跳过。Use when: 拉取 GitHub 仓库, 仓库搜索, 仓库黑名单, 出题源码准备。"
---

# 仓库拉取器（Repo Fetcher）

专门从 GitHub 搜索、快照拉取、去重开源仓库，作为评估项目（SWE-like 等）的出题源码素材池。核心能力：

- **搜索**（`list`）：按标准搜候选，排除黑名单（已用过）与已拉取（manifest）。
- **拉取**（`pull`）：快照拉取单个或从清单批量拉取，黑名单 / manifest 自动去重。
- **黑名单**（`blacklist`）：`add` 标记「已经用过」的仓库，之后搜索与拉取自动跳过。
- **进度追踪**（`task` / `table`）：记录每个仓库做题次数，生成 `repos.md` 状态表（仓库地址 / 是否做了题 / 次数 / 是否在黑名单）。

## 命令

```bash
python scripts/repo-fetcher/fetch.py list                                   # 搜候选（不 clone）
python scripts/repo-fetcher/fetch.py pull <owner/repo>                      # 拉取单个
python scripts/repo-fetcher/fetch.py pull --file projects/repo-fetcher/wishlist.txt   # 批量拉取清单
python scripts/repo-fetcher/fetch.py blacklist add <owner/repo>             # 标记已用过
python scripts/repo-fetcher/fetch.py blacklist remove <owner/repo>          # 移出黑名单
python scripts/repo-fetcher/fetch.py blacklist list                         # 查看黑名单
python scripts/repo-fetcher/fetch.py task <owner/repo> <次数>                # 记录做题次数（0 清除）
python scripts/repo-fetcher/fetch.py table                                   # 生成 repos.md 状态表
python scripts/repo-fetcher/fetch.py status                                  # 盘点一致性
```

## 关键文件

| 文件 | 说明 |
|------|------|
| `config.toml` | 拉取标准（语言/star/活跃度/严禁关键词）、路径、搜索参数 |
| `wishlist.txt` | 候选仓库清单（owner/repo 每行一个，`#` 注释） |
| `blacklist.txt` | 黑名单：**已经用过**的仓库（搜索/拉取自动跳过） |
| `tasks.txt` | 做题次数记录（owner/repo + 次数） |
| `repos.md` | 生成的仓库状态表（仓库地址 / 是否做了题 / 次数 / 黑名单） |
| `secrets.toml` | `github_pat`（本地，不提交；从 `secrets-simple.toml` 复制） |

## 工作流程

```
list 搜候选 → 人工挑 → 写进 wishlist.txt → pull --file 批量拉取 → task 记录做题次数 → table 生成状态表 → 用完后 blacklist add
```

- **黑名单语义**：黑名单 = 已经用过的仓库（一个 Repo 最多 3 条数据，用完即加黑名单），下次搜索/拉取不再出现。
- **去重**：manifest 记录已拉取；`pull` 命中 manifest 或黑名单都会跳过。
- **快照模式**：只取代码快照（tarball），重 `git init` 成干净 origin 仓，不含外部 remote/历史。
- **进度追踪**：`task <owner/repo> <次数>` 记录做题次数（同事可能已经做了一部分）；`table` 生成 `repos.md`，一眼看清哪些仓库做过题、做了几次、是否黑名单。
- `wishlist.txt`、`blacklist.txt`、`tasks.txt`、`repos.md` 提交到 Git；`repos/` 与 `repos-manifest.json` 为本地数据，不提交。

## 文档

- [docs/runbook.md](docs/runbook.md) — 逐步操作手册
