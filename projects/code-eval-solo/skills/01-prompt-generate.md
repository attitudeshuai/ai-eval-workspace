---
name: solo-prompt-generate
description: "Solo 提示词生成：批量生成提示词文件、在主仓注入 bug、调用 skill-git-init 推送至 GitHub。Use when: Solo 项目初始化, 批量提示词生成, Bug 注入, Git 推送。"
---

## ⚙️ 当前期配置

> 配置从 `../config.toml` 读取。`secrets.toml` 可覆盖 `active_session`、`repo_base_path`、`work_root`。
> 依赖 agent：`skills/prompt-architect/SKILL.md`、`skills/humanizer-zh/SKILL.md`
> 路径变量：`{work_root}`=`[paths].work_root`、`{SESSION_NAME}`=`[sessions].active`、`{PROJECT_PREFIX}`=`[source_rules].local_prefixes[0]`、`{REPO_BASE_PATH}`=`[paths].repo_base_path`

# Solo 项目提示词批量生成

## 功能概述

专用于 Solo 项目（项目名以 `{PROJECT_PREFIX}-` 开头）的批量提示词生成入口。

负责：校验主仓 → 扫描已有文件确定 index → 调用 prompt-architect → 写入文件 → Bug 注入 → git 推送。

## 命令

| 命令 | 说明 |
|------|------|
| generate | 默认。生成提示词文件 + Bug 注入 + 推送主仓 |
| info | 仅输出项目名与路径，不写文件 |
| append | 追加一轮提示词到已有文件末尾 |

## 默认配置

> 项目命名 `{PROJECT_PREFIX}-<id>`（不补零）、主仓 `{REPO_BASE_PATH}/{PROJECT_PREFIX}-<id>/`、结果 `{work_root}/{SESSION_NAME}/ai-model-result/`、index **全局累计跨类型不重置**。

## 输入规则

- 项目 ID：`123` 或 `{PROJECT_PREFIX}-123` 均可
- 类型配额：`bugfix*5`、`codegen*5`、`feature*5`、`understand*1`、`refactor*1`、`engineering*1`、`test*1`（别名映射见 config.toml）

## 路径规则

- 主仓：`{REPO_BASE_PATH}/{PROJECT_PREFIX}-<id>/`（必须已 git init）
- 结果目录：`{work_root}/{SESSION_NAME}/ai-model-result/{PROJECT_PREFIX}-<id>/{PROJECT_PREFIX}-<id>-{ALIAS}/`
- 提示词文件：`{PROJECT_PREFIX}-<id>-{ALIAS}-<index>.md`（{ALIAS} 为 config.toml 中定义的英文别名）

## 执行流程

### generate

1. 标准化项目名（不做补零）。
2. **校验主仓**存在且有 `.git`。
3. **扫描已有提示词文件，确定下一个 index**（全局累计，跨类型不重置）。index 自动补零（≤9 补 2 位，≥10 补 3 位）。
4. **调用 `prompt-architect` skill**，传入项目名、类型配额和代码目录上下文。
   - 0-1代码生成/Feature迭代：正确实现须 ≥2 个文件改动
   - Bug修复：bug 现象须涉及 ≥2 个不同文件的缺陷
   - **提示词必须纯自然语言**，禁止 API 路径、字段名、文件名、SQL、枚举值
5. **⚠️ [主 Agent 必须执行]** 用 PowerShell 写入文件：
   ```powershell
   [System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::UTF8)
   ```
   禁止用 Set-Content。提示词与「用户第一次提示词：」同行不换行。prompt-architect 不写文件。
6. 文件正文包含同名标识串。
7. **Bug 修复在 generate 内一次性注入**（直接改主仓代码）：
   - 每条 bug 不同维度，≥2 个文件改动
   - 逻辑缺陷，非语法错误
   - 注入后禁止手动 git 提交
8. **调用 `skill-git-init` 推送主仓**（commit message: `source code init.`）。
9. 推送后禁止再改主仓。
10. 输出汇总。

### info / append

- info：输出项目名和路径，校验主仓状态。
- append：读取已有文件，确定下一个 index，追加提示词模板。

## 提示词文件模板

```markdown
{PROJECT_PREFIX}-150-codegen-01

用户第一次提示词：<prompt 内容>

模型第一次回答 trae session id：

修改范围: <无需修改/单文件/模块内多文件/跨模块多文件/跨系统多模块>

模型第一次回答内容：


用户第二次提示词：
...
（预留至第 5 轮）
```

> 文件内容禁止反引号。目标文件已存在则跳过。

## 注意事项

1. 项目不 clone，源码须事先在 `{REPO_BASE_PATH}`。
2. 文件名与标识串一致，格式为 `{PROJECT_PREFIX}-<id>-{ALIAS}-<index>`。
3. generate 结束前必须 git push。
4. 所有提示词在主仓 main 分支依次执行，commit message 固定为 trae session id。
