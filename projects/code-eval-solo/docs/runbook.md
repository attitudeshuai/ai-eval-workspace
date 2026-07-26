# Solo 单模型代码评估 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于一步一步完成 Solo 项目的全流程。

配置统一读取 `projects/code-eval-solo/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 对应技术细节见 `skills/01-prompt-generate.md` 等 skill 文件。

---

## 通用启动语

```text
solo {项目名} {操作}
```

如：`solo app-12 generate`、`solo app-12 analyze bugfix-01 第1次`

---

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

## 前置准备

### 1. 配置本地环境

```bash
# 复制模板
cp projects/code-eval-solo/secrets-simple.toml projects/code-eval-solo/secrets.toml
```

编辑 `secrets.toml`：

```toml
work_root = "sessions/code-eval-solo"
repo_base_path = "source code"
active_session = "solo-demo"
```

### 2. 放置项目源码

将项目源码放到 `{repo_base_path}/{PROJECT_PREFIX}-<id>/`，确保已 `git init`。

```bash
# 示例
cd sessions/code-eval-solo/solo-demo/source\ code/app-12
git init
git add -A
```

---

## 第 1 步：生成提示词

### 指令模板

```text
solo app-12 generate
bugfix*5
codegen*5
feature*5
understand*1
refactor*1
engineering*1
test*1
```

### AI 会执行

1. 校验主仓存在且已 git init
2. 扫描已有提示词文件，确定全局 index
3. 调用 `prompt-architect` 批量生成提示词
4. 用 PowerShell 写入提示词文件到 `{work_root}/{SESSION_NAME}/ai-model-result/app-12/`
5. Bug 修复类型在主仓一次性注入 bug
6. 调用 `skill-git-init` 推送主仓到 GitHub（commit: `source code init.`）

### 产物

```text
{work_root}/{SESSION_NAME}/ai-model-result/app-12/
├── app-12-bugfix/
│   ├── app-12-bugfix-01.md
│   └── ...
├── app-12-codegen/
│   ├── app-12-codegen-06.md
│   └── ...
└── ...
```

---

## 第 2 步：在 Trae 中执行

用户在 Trae 中打开主仓，逐条按提示词执行：

1. 复制「用户第一次提示词」内容到 Trae
2. 模型完成后，在 Trae 中提交代码（commit message = trae session id）
3. 将模型回答内容粘贴到提示词文件的「模型第一次回答内容」字段
4. 填写「模型第一次回答 trae session id」和「修改范围」
5. 如需追问，重复 1-4 填入「用户第二次提示词」等字段

---

## 第 3 步：分析结果

### 指令模板

```text
solo app-12 analyze bugfix-01 第1次
```

### AI 会执行

1. 读取提示词文件和 git commit 变更
2. 路线 A：调用 `implementation-reviewer` 评价代码产物
3. 路线 B：自行 10 维度分析对话过程
4. 写入评价结果到 `app-12-bugfix-01-评价结果.md`

### 产物

```text
{work_root}/{SESSION_NAME}/ai-model-result/app-12/app-12-bugfix/
├── app-12-bugfix-01.md
└── app-12-bugfix-01-评价结果.md
```

---

## 第 4 步：导出

### 导出评价结果

```text
solo app-12 export
```

AI 将评价结果汇总为 CSV，输出到 `deliverables/code-eval-solo/{SESSION_NAME}/app-12/csv-app-12-export.csv`，并执行 Session ID / Commit ID 验证。

### 导出提示词

```text
solo app-12 export-prompt
```

输出到 `deliverables/code-eval-solo/{SESSION_NAME}/app-12/csv-app-12-prompt-export.csv`，并与主 export 做一致性校验。
