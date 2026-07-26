# GSB 多模型代码对比评估 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于一步一步完成 GSB 多模型对比评估的全流程。

配置统一读取 `projects/code-eval-gsb/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 对应技术细节见 `skills/01-prompt-generate.md`、`skills/02-round-review.md`、`skills/03-summary-analysis.md`。

---

## 通用启动语

```text
gsb {项目ID} {操作}
```

如：`gsb demo-hello setup`、`gsb demo-hello review bugfix spring 第1轮`

---

## 前置准备

> 📁 完整目录结构样例见 [structure-example.md](structure-example.md)

### 配置本地环境

```toml
work_root = "sessions/code-eval-gsb"
active_session = "session-gsb1v1"
github_pat = "your-github-pat"
```

### 放置项目源码

将项目源码放到 `{work_root}/{SESSION_NAME}/source code/{项目名}-origin/`，确保已 `git init`。

---

## 第 1 步：Setup（项目初始化 + 生成提示词）

### 指令模板

```text
gsb demo-hello setup
```

### AI 会执行

1. 扫描项目结构，展示摘要，请用户确认任务类型（7选1）
2. Bug 修复类型：注入 bug → commit
3. 推送 GitHub 仓库
4. 创建各模型对比分支并 clone 到本地
5. 调用 `prompt-architect` → `humanizer-zh` 生成去 AI 化提示词
6. 写入对话内容文件和评价结果文件（每模型各一份）

### 产物

```text
{work_root}/{session}/source code/demo-hello/
├── demo-hello-origin/
├── demo-hello-TestM_1/
└── demo-hello-TestM_2/

{work_root}/{session}/ai-model-result/demo-hello/demo-hello-{ALIAS}/
├── demo-hello-{ALIAS}-TestM_1-对话内容.md
├── demo-hello-{ALIAS}-TestM_1-评价结果.md
├── demo-hello-{ALIAS}-TestM_2-对话内容.md
└── demo-hello-{ALIAS}-TestM_2-评价结果.md
```

---

## 第 2 步：在 Trae 中执行

用户在各模型分支仓库中分别执行相同的提示词：

1. 进入 `demo-hello-spring/`，复制首轮提示词到 Trae
2. 模型完成后，将回答贴回 `-对话内容.md` 的「模型第一次回答内容」+ 填写 session id
3. 在其他模型分支（`demo-hello-summer/` 等）中重复同样操作
4. 如需追问，使用 review 生成的追问提示词继续

---

## 第 3 步：轮次评价

### 指令模板

```text
gsb demo-hello review bugfix spring 第1轮
```

### AI 会执行

1. 读取该模型的对话内容
2. 调用 `implementation-reviewer` 评估
3. 判断满意/不满意
4. 不满意且未达第3轮 → 生成追问提示词，写入对话内容文件
5. 追加评价到 `-评价结果.md`

### 多轮追问

每轮对话结束后可重复执行 review。最多 3 轮。各模型独立 review。

```text
# 第2轮（若第1轮不满意）
gsb demo-hello review bugfix TestM_1 第2轮

# TestM_2 同理
gsb demo-hello review bugfix TestM_2 第1轮
```

---

## 第 4 步：汇总分析

### 指令模板

```text
gsb demo-hello analyze bugfix
```

### AI 会执行

1. 加载所有模型的 `-对话内容.md`
2. 对各分支执行 `git diff main`
3. 调用 `implementation-reviewer` 逐模型 6 维度打分 + GSB 对比
4. 调用 `humanizer-zh` 去 AI 化
5. 生成 `demo-hello-bugfix-评价汇总.md`

### 产物

```text
{work_root}/{session}/ai-model-result/demo-hello/demo-hello-bugfix/
└── demo-hello-bugfix-评价汇总.md
```

评分字段中 `【待用户填写】` 和 `【参考值，请确认】` 需人工核对后提交。

---

## 预生成表单骨架（对话完成前）

```text
gsb demo-hello analyze init bugfix
```

不调用 agent，仅根据已有信息预填固定字段，其余留空。
