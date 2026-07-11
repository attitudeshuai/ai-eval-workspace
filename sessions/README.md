# 评估会话目录

每个子目录代表一次独立的评估会话。会话可以跨项目运行，但产物按项目隔离。

## 会话目录结构

```text
session-*/
  config.toml                              # 会话配置
  prompts/                                 # 生成的 Prompt 文件
  projects/                                # 跨项目产物
    <project-id>/
      submissions/<task-id>/<agent>/       # Agent 运行产物
        source/                            # 修改后的代码
        screenshots/                       # 关键状态截图
        console.log                        # console 输出
        network.log                        # 网络请求记录
        transcript.md                      # 运行轨迹
      reports/<task-id>/<agent>/           # 评估报告
        report.json                        # 结构化评分
        report.md                          # 可读报告
        evidence/                          # 评估证据
  logs/                                    # 会话日志
```

## 创建会话

使用 `scripts/run_sota.py` 或 `scripts/evaluate_task.py` 自动创建。

示例：

```bash
python scripts/run_sota.py \
  --session session-sota-2026-07-001-codex \
  --project webdev-long-horizon \
  --task webdev-task-01 \
  --agent codex
```
