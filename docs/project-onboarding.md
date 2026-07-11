# 新项目接入指南

本工作台对项目内部结构不做强制要求。每个项目只需一个 `config.toml` 即可被工作台识别，其余内容由项目自行决定。

---

## 最小接入要求

一个项目只需要：

```text
projects/<project-id>/
  config.toml
  README.md
```

其中 `config.toml` 至少包含：

```toml
[project]
id = "my-project"
name = "我的评估项目"
description = "评估 agent 在某某场景下的能力"
```

完成这一步后，工作台就能识别该项目，并可以为其创建会话、汇总基准。

---

## 可选：定义项目自己的结构

项目可以根据自身需求自由扩展目录。例如：

```text
projects/my-project/
  config.toml
  README.md
  tasks/              # 自定义任务格式
  prompts/            # 自定义 prompt 模板
  rubrics/            # 自定义评分标准
  tests/              # 自定义测试
  docs/               # 项目专属文档
```

工作台不会强制检查这些目录的结构，除非项目主动调用对应的校验脚本。

---

## 示例：使用 Web Dev 任务模板

如果项目希望复用 `webdev-long-horizon` 的任务模板，可以：

1. 将 `projects/webdev-long-horizon/templates/` 复制到自己项目下。
2. 在 `config.toml` 中配置 `task_prefix = "xxx-task"`。
3. 若复用 webdev-long-horizon 任务模板，使用 `python scripts/webdev-long-horizon/create_task.py --project <id>` 创建任务。

但这完全是可选的。其他项目可以用完全不同的任务组织方式。

---

## 项目配置字段参考

```toml
[project]
id = "my-project"                    # 项目唯一标识
name = "我的评估项目"                 # 显示名称
description = "..."                  # 描述
owner = "..."                        # 负责人
created_at = "2026-07-10T00:00:00Z"  # 创建时间
task_prefix = "my-task"              # 可选，任务 ID 前缀

[paths]
tasks_dir = "tasks"                  # 可选，任务目录相对路径
templates_dir = "templates"          # 可选，模板目录
# task_source = "sources"            # 可选，外部源码目录相对路径（如 webdev-long-horizon 使用 sources/）

[evaluation]
default_agents = ["codex"]           # 可选，默认评估 agent
```

---

## 推荐命名

- 项目 ID：英文小写 + 短横线，如 `webdev-long-horizon`、`mobile-app`、`backend-api`。
- 会话名称：`session-<type>-YYYY-MM-NNN[-<agent>]`。
