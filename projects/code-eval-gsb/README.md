# code-eval-gsb: 多模型代码对比评估（GSB）

评估多个 AI 模型在相同代码任务下的相对表现，支持 1v1、2v1 等对比模式。

## 评估模式

本项目的核心思路是：**同一代码任务 → 多个模型分别执行 → 对比分析**。

1. 将项目源码推送到 GitHub 仓库
2. 为每个模型创建独立分支，模型各自在分支上工作
3. 生成一条统一提示词，所有模型共享相同输入
4. 用户在 Trae 中让各模型分别完成提示词
5. 逐轮评价每个模型的表现，最终汇总 GSB 对比结论

## 对比模式

| 模式 | 模型数 | 对比组合 | 适用场景 |
|------|:-----:|------|------|
| 1v1 | 2 | A vs B | 两模型直接 PK |
| 2v1 | 3 | A vs B, A vs C（B vs C 可选） | 基准模型 vs 两个对比模型 |
| 通用 | N | 完全由配置决定 | 灵活自定义 |

## 目录结构

```
code-eval-gsb/
├── config.toml                 # 项目配置（模型、对比规则、评估参数）
├── SKILL.md                    # AI Agent 执行规范
├── secrets.toml                # 本地敏感配置（gitignore，不提交）
├── README.md                   # 本文件
├── docs/
│   ├── runbook.md
│   └── structure-example.md
└── templates/
    ├── prompt-file.md
    └── summary-form.md
```

## 快速开始

### 1. 配置本地环境

编辑 `secrets.toml`：

```toml
work_root = "sessions/code-eval-gsb"
active_session = "session-gsb1v1"
github_pat = "your-github-pat"
```

### 2. 初始化项目

向 AI Agent 发送：
```
使用 code-eval-gsb 技能，setup 项目 1035
```

AI 将完成：源码推送 GitHub → 创建分支 → 生成提示词。

### 3. 轮次评价

每轮对话后在 AI Agent 中执行：
```
使用 code-eval-gsb 技能，review demo-hello bugfix steve 第1轮
```

### 4. 汇总分析

所有模型完成后：
```
使用 code-eval-gsb 技能，analyze demo-hello bugfix
```

## 多人协作

- 每个人在本地 `secrets.toml` 中配置自己的路径和 session
- `config.toml` 中的默认值会被 `secrets.toml` 覆盖
- GitHub 仓库创建后所有人可访问，但各自本地 clone 路径独立
- 不要提交 `secrets.toml` 到 Git
