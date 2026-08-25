# repo-pool: 开源仓库池（GitHub Repo Pool）

按标准从 GitHub 搜索、拉取、去重开源仓库，作为评估项目（`code-eval-gsb` 等）出题源码素材池。

## 定位

- 只负责「找仓库 → 拉取 → 去重 → 盘点」，不涉及出题/评价。
- 拉下来的仓库由人**手动 copy** 到评估项目的 `source code/` 下再出题。

## 快速开始

```bash
# 1. 配置（可选，建议配置以提升 Search API 额度）
cp projects/repo-pool/secrets-simple.toml projects/repo-pool/secrets.toml   # 填入 github_pat

# 2. 搜候选（不 clone）
python scripts/repo-pool/fetch_repos.py list

# 3. 快照拉取 + 去重
python scripts/repo-pool/fetch_repos.py pull itwanger/paicoding --domain 全栈Web应用 --framework "Spring Boot + Vue"

# 4. 盘点
python scripts/repo-pool/fetch_repos.py status
```

## 目录结构

```
projects/repo-pool/                    # 配置 + 技能 + 文档（提交 git）
├── config.toml                        # [criteria] 拉取标准 + [paths] 池/清单路径
├── SKILL.md
├── skills/01-pull-repos.md
├── docs/runbook.md
├── secrets-simple.toml
└── README.md

scripts/repo-pool/fetch_repos.py       # list / pull / status 脚本（提交 git）

sessions/repo-pool/                    # 工作数据（不提交 git）
├── repos-manifest.json                # 去重清单（本地）
└── repos/<repo>/<repo>-origin/        # 拉下来的仓库池
```

## 拉取标准（config.toml [criteria]）

- 后端语言：Java / C# / Python
- 最低 star、最近活跃天数
- 严禁关键词（对齐 0825 众测方案附录「严禁出题清单」）

## 多人协作

- `secrets.toml` 各人本地一份，不提交。
- `repos-manifest.json` 与 `repos/` 是本地数据，不纳入 git；多人各自拉取时靠本地 manifest 各自去重。
