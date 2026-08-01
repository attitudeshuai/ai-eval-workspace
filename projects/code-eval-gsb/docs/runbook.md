# GSB 多模型代码对比评估 Runbook

本 Runbook 提供与 AI Agent 对话时的自然语言指令模板，用于一步一步完成 GSB 多模型对比评估的全流程。

配置统一读取 `projects/code-eval-gsb/config.toml`，敏感信息在 `secrets.toml`（`.gitignore` 已排除）。

> 对应技术细节见 `skills/01-prompt-generate.md`、`skills/02-round-review.md`、`skills/03-summary-analysis.md`。

---

## 通用启动语

```text
gsb {项目ID} {操作}
```

如：`gsb demo-hello setup`、`gsb demo-hello review bugfix steve 第1轮`

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

将项目源码放到 `{work_root}/{SESSION_NAME}/source code/{项目名}/{项目名}-origin/`，确保已 `git init`。

**0-1 代码生成项目**：origin 仓只需放一个标准命名的 `README.md`（完整需求规格书：技术栈 + 功能模块 + 约束），仓内不放任何代码。项目名 = 需求 md 文件名（如 `projects/code-eval-gsb/docs/gsb0731_00001.md` → 项目名 `gsb0731_00001`），把该 md 原样复制为 `{项目名}-origin/README.md` 即可。

---

## 第 1 步：Setup（项目初始化 + 生成提示词）

### 指令模板

```text
gsb demo-hello setup

# 0-1 代码生成（项目名 = docs 下需求 md 文件名）
gsb gsb0731_00001 setup
```

### AI 会执行

1. 扫描项目结构，展示摘要，请用户确认任务类型（7选1；0-1 项目生成指令自带「0-1代码生成」类型，无需确认）
2. Bug 修复类型：注入 bug → commit；0-1 代码生成：origin 仓只含 README.md 需求规格书，保持原样
3. 推送 GitHub 仓库
4. 创建各模型对比分支并 clone 到本地
5. 调用 `prompt-architect` → `humanizer-zh` 生成去 AI 化提示词（0-1 代码生成首轮固定为"通读 README、按文档开发整套系统"口径，后续轮次按模型交付与 README 的差距在轮次分析阶段生成）
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

1. 进入 `demo-hello-steve/`，复制首轮提示词到 Trae
2. 模型完成后，将回答贴回 `-对话内容.md` 的「模型第一次回答内容」+ 填写 session id
3. 在其他模型分支（`demo-hello-natasha/`、`demo-hello-thor/`、`demo-hello-tony/`）中重复同样操作
4. 如需追问，使用 review 生成的追问提示词继续

### 0731 期 Trae 环境要求

- **Trae CN 客户端**（非字节员工账户登录，更新至最新版本），**SOLO Agent** 模式，关闭 Auto，选择内部策略模型
- **每一道题打开新的任务窗口**测试
- `settings.json` 写入 PPE 配置：`"ai_assistant.request.env": "ppe"` + `"ai_assistant.request.ppe": "ppe_trae_seed_code_dogfood"`，然后 Reload Window
- **所有任务开启 Max（1M 上下文）**：对话底部应显示 `X% of 1000K`；若显示 `of 186K` / `of 224K` 等小窗口，说明 Max 未生效，检查配置后重测本题
- 详细配置步骤见 [Seed模型 GSB 众测方案（0731）.md](Seed模型%20GSB%20众测方案（0731）.md) 第二节

---

## 第 3 步：轮次评价

### 指令模板

```text
gsb demo-hello review bugfix steve 第1轮
```

### AI 会执行

1. 读取该模型的对话内容
2. 调用 `implementation-reviewer` 评估
3. 判断满意/不满意
4. 不满意且未达第 6 轮 → 生成追问提示词，写入对话内容文件
5. 追加评价到 `-评价结果.md`

### 多轮追问（0731 期：3 ≤ 轮次 ≤ 6）

每轮对话结束后可重复执行 review。**本期要求每题至少 3 轮、最多 6 轮**：出题时已把题目设计成需 3 轮以上完成（第 2、3 轮含跨轮次依赖），即使回答满意，未满 3 轮也应继续预设的下一轮任务。各模型独立 review。

```text
# 第2轮（按预设多轮任务继续，或第1轮不满意时追问）
gsb demo-hello review bugfix steve 第2轮

# natasha / thor / tony 同理
gsb demo-hello review bugfix natasha 第1轮
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
3. 调用 `implementation-reviewer` 逐模型 8 维度打分（5 基础 + 3 Add-on）+ GSB 对比
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

---

## 第 5 步：交付导出（追加到飞书多维表格）

汇总表单人工核对定稿后执行：

### 指令模板

```text
gsb demo-hello export bugfix 提交人:张三 TraeCN用户ID:zhangsan001
```

### AI 会执行

1. 读取 `demo-hello-bugfix-评价汇总.md`，检查无 `【待用户填写】`/`【参考值，请确认】` 残留
2. 按交付表字段生成记录 JSON（模型区块顺序：Natasha → Thor → Steve → Tony）
3. 调用 `scripts/code-eval-gsb/append_delivery_feishu.py` 先 `--dry-run` 校验，再正式追加到飞书多维表格（地址见 `config.toml [feishu]`）
4. 输出追加的 record_id + 留空字段清单

### 产物

飞书多维表格「数据表」新增一条记录（含 4 模型评分、3 组 GSB、4 条模型评价）。脚本按 Github Repo 查重，重复追加需人工确认后加 `--force`。单选/多选字段只能写入已有选项，脚本会校验并列出合法选项。

> 技术细节见 `skills/04-export-delivery.md`。飞书凭证在 `secrets.toml [feishu]`；首次使用需在飞书开发者后台为应用开通 `bitable:app` 权限，并把应用添加为多维表格协作者。
