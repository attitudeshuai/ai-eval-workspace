# Repo Pool 操作手册

## 前置准备

1. 复制 `projects/repo-pool/secrets-simple.toml` → `projects/repo-pool/secrets.toml`，填入 `github_pat`（可选，建议配置以提升 Search API 额度）。
2. 确认 `config.toml [criteria]` 的拉取标准（语言 / star / 活跃度 / 严禁关键词）符合当期要求。

## 第 1 步：搜候选

```bash
python scripts/repo-pool/fetch_repos.py list
```

按 `[criteria]` 搜索并过滤严禁关键词，输出候选表（不 clone）。人工从中挑选符合当期出题分布的仓库。

## 第 2 步：快照拉取

```bash
python scripts/repo-pool/fetch_repos.py pull itwanger/paicoding \
  --domain 全栈Web应用 --framework "Spring Boot + Vue" --task-types "Feature迭代,Bug修复,重构"
```

- 自动去重（manifest 已有 full_name 会跳过，`--force` 重拉）。
- 快照模式：只取代码快照，重 `git init` 成干净 origin 仓。
- 拉取后写入 `repos-manifest.json`。

## 第 3 步：盘点

```bash
python scripts/repo-pool/fetch_repos.py status
```

报告「正常 / 清单有但目录缺 / 目录有但清单缺（孤儿）」三张表。

## 第 4 步：人工 copy 到评估项目

把池里仓库复制到评估项目 session 的 `source code/` 下，再走该项目的出题流程：

```bash
# 例如接入 code-eval-gsb 0825 期
cp -r sessions/repo-pool/repos/paicoding/paicoding-origin \
      "sessions/code-eval-gsb/session-0825/source code/paicoding/paicoding-origin"
```

然后执行 `code-eval-gsb` 的 `setup` 流程。
