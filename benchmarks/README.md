# 基准汇总

本目录保存跨项目、跨会话的评估汇总与排行榜。

## 文件说明

```text
benchmarks/
├── global/
│   ├── summary.csv        # 所有项目汇总
│   └── leaderboard.md     # 全局 Agent 排行榜
└── by-project/
    └── <project-id>/
        ├── summary.csv    # 项目级汇总
        └── leaderboard.md # 项目级排行榜
```

## 更新方式

```bash
python scripts/generate_report.py --session <session-name>
```

该命令会追加当前会话结果到：

- `benchmarks/global/summary.csv`
- `benchmarks/by-project/<project-id>/summary.csv`

并重新生成对应的 `leaderboard.md`。
