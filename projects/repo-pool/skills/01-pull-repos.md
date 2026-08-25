---
name: repo-pool-pull-repos
description: "仓库拉取：按标准从 GitHub 搜索候选仓库、快照拉取并去重、盘点池内仓库。Use when: repo-pool list/pull/status, 拉取 GitHub 仓库, 仓库去重。"
---

# 仓库拉取（list / pull / status）

> 配置从 `../config.toml` 读取（`[criteria]` 标准 + `[paths]` 路径），`secrets.toml` 提供 github_pat（可选）。
> 脚本：`scripts/repo-pool/fetch_repos.py`（仅标准库，Python 3.11+）

## 功能概述

- `list`：按 `[criteria]` 用 GitHub Search API 搜候选，过滤严禁关键词，输出候选表（**不 clone**）
- `pull`：快照拉取单个仓库到池里，去重后写入 manifest
- `status`：核对 manifest 与本地目录一致性

**本技能不负责**：把仓库安装到评估项目 session（由人手动 copy）。

## 命令

| 命令 | 说明 |
|------|------|
| list | 搜索候选仓库（多语言各翻 `max_pages` 页，按 stars 降序） |
| pull `<owner/repo>` [--domain D] [--framework F] [--task-types "A,B"] [--force] | 快照拉取 + 去重 + 写 manifest |
| status | 报告重复 / 缺失 / 孤儿 |

## 执行流程

### list
1. 对 `[criteria].languages` 逐个构造 query：`language:{lang} stars:>{min_stars} pushed:>{date}`。
2. 逐页拉取 Search API 结果，客户端过滤严禁关键词（匹配 name / description / topics）。
3. 输出候选表：full_name / stars / language / description / topics。
4. 不 clone、不写文件。

### pull `<owner/repo>`
1. 解析 owner/repo，`GET /repos/{owner}/{repo}` 取元数据（default_branch、stars、language、pushed_at、clone_url）。
2. 命中严禁关键词 → 打印警告（仍继续，因为是你明确指定的仓库）。
3. **去重**：manifest 已有 full_name → 跳过（`--force` 重拉）；`repos/<repo>/` 目录已存在 → 提示后覆盖。
4. **快照拉取**：下载 `codeload` tarball → 解压 → 放到 `repos/<repo>/<repo>-origin/` → `git init` + 首次 commit。
5. 写 manifest（domain / framework / task_types 用传入参数，缺省留空）。
6. 输出本地路径，提示「人工 copy 到评估项目 session 的 source code/」。

### status
1. 读 manifest，逐条核对 `repos/<repo>/<repo>-origin/` 是否存在且含 `.git`。
2. 扫描 `repos/` 下目录，反向核对是否有 manifest 记录。
3. 输出三张表：正常 / 清单有但目录缺 / 目录有但清单缺（孤儿）。

## 路径规则

```
# 仓库池（快照，干净 origin 仓）
{pool_root}/<repo>/<repo>-origin/

# 去重清单（本地，不提交）
{manifest}                                     # repos-manifest.json
```

## 去重逻辑

| 检查 | 命中时 |
|------|--------|
| manifest 已有 `full_name` | 跳过（`--force` 重拉） |
| `repos/<repo>/` 目录已存在 | 提示可能重复，确认后覆盖 |

## 注意事项

1. 快照默认丢弃原 git 历史 / remote，只留代码快照，重新 init 为干净 origin 仓，便于后续推送到自己的 GitHub。
2. github_pat 放在 `secrets.toml`（Search API 认证后额度更高）；未配置则走未认证额度。
3. `repos/` 与 `repos-manifest.json` 不提交 git。
4. 拉下来的仓库最终要**人工 copy** 到评估项目（如 `code-eval-gsb`）的 `source code/` 下再出题。
