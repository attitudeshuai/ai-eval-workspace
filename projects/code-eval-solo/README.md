# code-eval-solo: 单模型代码评估

评估单个 AI 模型在代码生成、Bug 修复、Feature 迭代等场景下的代码能力。

## 评估模式

本项目的核心思路是：**一条提示词 = 一个独立子仓 = 一次独立评估**。

1. 以项目源码为基础，按任务类型批量生成多条提示词
2. 每条提示词对应一个独立子仓（代码副本），避免任务间互相污染
3. 用户在 Trae 等 IDE 中让模型逐条完成提示词
4. 收集模型回答后，逐条分析是否完成 prompt 要求

## 目录结构

```
code-eval-solo/
├── config.toml                 # 项目配置（task_types、路径约定、评估参数）
├── SKILL.md                    # AI Agent 执行规范
├── secrets.toml                # 本地敏感配置（gitignore，不提交）
├── README.md                   # 本文件
├── docs/
│   └── workflow.md             # 详细操作流程
└── templates/
    └── prompt-file.md          # 提示词文件模板
```

## 项目来源

所有项目源码放置在 `{work_root}/{SESSION_NAME}/source code/` 下，自建自管理。

## 支持的任务类型

| 类型 | 默认配额 | 说明 |
|------|:------:|------|
| Bug修复 | 5 | 定位并修复代码中的 bug |
| 0-1代码生成 | 5 | 从零实现新功能 |
| Feature迭代 | 5 | 在现有功能上追加 |
| 代码理解 | 1 | 解释逻辑、分析调用链 |
| 工程化 | 1 | 环境、构建、CI/CD |
| 代码重构 | 1 | 性能、可读性优化 |
| 代码测试 | 1 | 测试用例编写 |

## 快速开始

### 1. 配置本地环境

编辑 `secrets.toml`（首次使用从模板复制）：

```toml
work_root = "sessions/code-eval-solo"
active_session = "solo-demo"
```

### 2. 生成提示词

向 AI Agent 发送：
```
使用 code-eval-solo 技能，项目 project-150，生成：
bugfix*5  codegen*5  feature*5  understand*1  refactor*1  engineering*1  test*1
```

### 3. 分析结果

向 AI Agent 发送：
```
使用 code-eval-solo 技能，分析 project-150 的 bugfix-01，第 1 次对话
```

## 多人协作

- 每个人在本地 `secrets.toml` 中配置自己的路径和 session
- `config.toml` 中的默认值仅作为参考，会被 `secrets.toml` 覆盖
- 不要提交 `secrets.toml` 到 Git
