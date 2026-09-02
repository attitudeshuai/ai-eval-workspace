# Repo Fetcher 操作手册

## 前置准备

1. 复制 `projects/repo-fetcher/secrets-simple.toml` → `secrets.toml`，填入 `github_pat`（建议配置以提升 Search API 额度）。
2. 确认 `config.toml [criteria]` 的拉取标准（语言 / star / 活跃度 / 严禁关键词）符合当期要求（SWE-like：Go / Python）。

## 第 1 步：搜候选

```bash
python scripts/repo-fetcher/fetch.py list
```

按 `[criteria]` 搜索并过滤：严禁关键词 + 黑名单 + 已拉取。人工从中挑符合当期出题的仓库。

## 第 2 步：写进候选清单

把挑中的仓库（owner/repo，每行一个）追加到 `projects/repo-fetcher/wishlist.txt`：

```text
# ---- Go ----
restic/restic
rclone/rclone

# ---- Python ----
pallets/flask
scrapy/scrapy
```

## 第 3 步：批量拉取

```bash
python scripts/repo-fetcher/fetch.py pull --file projects/repo-fetcher/wishlist.txt
```

- 已拉取（manifest）与黑名单中的自动跳过。
- 单个拉取：`pull <owner/repo>`；强制重拉加 `--force`。

## 第 4 步：盘点

```bash
python scripts/repo-fetcher/fetch.py status
```

报告「正常 / 清单有但目录缺 / 目录有但清单缺（孤儿）」三张表，并标注黑名单中的仓库。

## 第 5 步：记录做题次数 & 生成状态表

同事可能已经在这个仓库上做过题。用 `task` 记录做题次数，用 `table` 生成 `repos.md`：

```bash
python scripts/repo-fetcher/fetch.py task restic/restic 2        # restic 已做 2 题
python scripts/repo-fetcher/fetch.py table                       # 生成 repos.md
```

`repos.md` 表格列：**仓库地址 / 是否做了题 / 做题次数 / 是否在黑名单**。`tasks.txt`、`repos.md` 提交到 Git，供团队同步，避免和同事撞题。

## 第 6 步：用完加黑名单

一个仓库用完（提交满任务 / 不再复用）后，标记为已用过：

```bash
python scripts/repo-fetcher/fetch.py blacklist add <owner/repo>
python scripts/repo-fetcher/fetch.py blacklist list
```

黑名单中的仓库在下次 `list` / `pull` 时自动跳过，避免重复爬取与重复出题。
