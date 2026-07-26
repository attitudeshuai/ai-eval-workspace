# GSB 0723 使用手册

> 适用：Seed 模型 GSB 众测 0723 期
> **🤖 本期执行模式：DeepSeek（GitHub Copilot）**
> 核心文件：`scripts/gsb/config.yaml`、`scripts/gsb/gsb 0723.md`
> 配套 Skill：`projects/code-eval-gsb/skills/01-prompt-generate.md`、`02-round-review.md`、`03-summary-analysis.md`

---

## 一、本期核心要求速览

### 1.1 评测对象

- **参评模型**：Charmander / Squirtle / Bulbasaur
- **对比策略**：两两 GSB，共 3 组，**不提供 Same 选项**
  - Charmander vs Squirtle
  - Charmander vs Bulbasaur
  - Squirtle vs Bulbasaur

### 1.2 环境与工具

- 使用 **非字节员工账户** 登录 **Trae CN** 最新版
- 必须使用 **SOLO Agent 模式**
- **关闭 Auto**
- 每道题打开 **新的任务窗口**
- 按 `scripts/gsb/gsb 0723.md` 中的 PPE 配置（待定）配置 `settings.json` 并 reload 窗口

### 1.3 关键分布要求

| 维度                   | 本期要求                                                                                                          |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **任务类型**     | Feature 30% / Bug 25% / 0-1 代码生成 15% / 代码重构 15% / 代码理解 5% / 工程化 5% / 代码测试 5%（允许 ±2% 浮动） |
| **修改范围**     | 单文件 5% / 模块内多文件 20% / 跨模块多文件 35% / 跨系统多模块 40%                                                |
| **约束标签数量** | 0 个 5% / 1 个 10% / 2 个 35% / 3 个 35% / ≥4 个 15%                                                             |
| **Max 模式**     | 70% 开启 / 30% 不开启                                                                                             |
| **上下文窗口**   | 日常短窗口 30% / 长上下文 30% / 超长 1M 40%（建议，非强制）                                                       |

### 1.4 评分维度

本期共 **8 个维度**：

- **5 个基础维度**：交付完整性、指令遵循、任务规划、推理能力、边界感
- **3 个 Add-on 维度**：
  - 长上下文保持能力（仅长上下文/超长样本打分，短窗口填 `N/A`）
  - 思考效率（全部样本打分）
  - 工具调用效率（全部样本打分，需填写问题工具名）

---

## 二、整体作业流程

### Simple 版（一句话记牢）

```
下代码 → 出题 → 跑 3 个模型 → 写评价 → 出汇总表 → 交
```

### 详细版

```
准备本地主分支
    ↓
运行 code-eval-gsb 提示词生成 → 推送 GitHub → 生成提示词文件
    ↓
在 Trae SOLO Agent 中分别跑 3 个模型
    ↓
每轮结束后运行 code-eval-gsb 轮次分析
    ↓
全部完成后运行 code-eval-gsb 汇总 analyze
    ↓
人工核对 → 交叉验证 → 提交
```

### 触发 AI 执行的命令示例

#### Kimi 模式（`.kimi/skill/`）

| 步骤 | 你给 AI 发的指令 |
|------|-----------------|
| **Setup** | `执行 code-eval-gsb 提示词生成，项目名是 <Repo ID>，主分支已放到 <路径>` |
| **生成提示词** | `继续 generate，任务类型是 <类型>`（setup 完成后通常自动进入） |
| **Review** | `执行 code-eval-gsb 轮次分析，项目名 <Repo ID>，类型 <类型>，模型 Charmander，轮次 1` |
| **汇总** | `执行 code-eval-gsb 汇总 analyze，项目名 <Repo ID>，类型 <类型>` |
| **验证** | `运行 scripts/gsb/cross_file_verifier.py <Repo ID> <类型>` |

#### DeepSeek 模式（`projects/code-eval-gsb/skills/`）🤖 本期使用

> ⚠️ 以下均为**自然语言对话指令**，直接在 Copilot Chat 中输入即可触发对应 Skill。只有「验证」步骤需要在终端执行 Python 脚本。

**code-eval-gsb 提示词生成（项目初始化 + 出题）**

| 子命令 | 你给 AI 发的指令 | 说明 |
|--------|-----------------|------|
| **setup**（默认） | `执行 code-eval-gsb 提示词生成，项目名是 <Repo ID>，主分支已放到 <路径>` | 读取配置 → 验证本地主分支 → 确认类型 → 推送 GitHub → 创建分支 → **自动衔接 generate** |
| **generate**（自动衔接） | `继续 generate，任务类型是 <类型>` | 调用 prompt-architect + humanizer-zh 生成提示词，写入对话内容文件。setup 完成后自动进入，一般无需手动触发 |
| **info** | `执行 code-eval-gsb 提示词生成 info，项目名 <Repo ID>` | 仅输出项目名和 GitHub 仓库地址，不执行任何写操作 |

**code-eval-gsb 轮次分析（轮次评审）**

| 子命令 | 你给 AI 发的指令 | 说明 |
|--------|-----------------|------|
| **review**（唯一命令） | `执行 code-eval-gsb 轮次分析，项目名 <Repo ID>，类型 <类型>，模型 Charmander，轮次 1` | 读取本轮对话 → 调用 reviewer 评估 → 满意则结束 / 不满意则生成追问提示词 → 追加评价 → 验证 Session ID |

**code-eval-gsb 汇总（汇总表单）**

| 子命令 | 你给 AI 发的指令 | 说明 |
|--------|-----------------|------|
| **analyze**（默认） | `执行 code-eval-gsb 汇总 analyze，项目名 <Repo ID>，类型 <类型>` | 完整执行：读对话 → 查代码变更 → reviewer 评分 + GSB 对比 → humanizer-zh 去 AI 化 → 生成汇总表单 → 交叉验证 |
| **init** | `执行 code-eval-gsb 汇总 init，项目名 <Repo ID>，类型 <类型>` | 仅预生成表单骨架（固定字段），不调用任何 agent，适合对话未完成时提前准备 |

> ⚠️ **触发规则**：`code-eval-gsb 汇总` 仅在你的消息中明确包含「汇总」二字时才会被触发；其他两个 skill 匹配描述关键词即可。

**终端验证脚本**

| 步骤 | 终端命令 |
|------|---------|
| **交叉验证** | `python scripts/gsb/cross_file_verifier.py <Repo ID> <类型>` |

---

## 三、输出字段与生成方式

下表对应最终提交表单的字段（每模型一份），说明当前模板是否支持以及如何生成该字段值。

| 字段 | 当前模板是否支持 | 生成方式 |
|------|------------------|----------|
| **context 占用** | ✅ | 从 `-对话内容.md` 中「最后一轮 context 占用」字段读取。人工在 Trae 对话底部查看 `X% of YK` 并填写；若触发自动压缩，记录为 `在第 N 轮触发了自动压缩，最终 X% of YK`。 |
| **长上下文保持能力** | ✅ | 1-5 分。implementation-reviewer 参考评分；日常短窗口样本强制填 `N/A`。 |
| **出现的问题（长上下文）** | ✅ | 多选。implementation-reviewer 识别后勾选；选项来自 `config.yaml` 的 `long_context_issue_options`（前文约束遗忘 / 已改代码回退/重复劳动 / 路径幻觉 / lost-in-the-middle / 前后自相矛盾 / 其他 / 未出现显著问题）。 |
| **打分理由（长上下文）** | ✅ | 必须包含：轮次+动作、对交付/效率的具体影响、能力明显退化时的 context 占用百分比；选「其他」需具体描述。由 reviewer 分析 + humanizer-zh 去 AI 化后写入。 |
| **思考效率** | ✅ | 1-5 分。implementation-reviewer 参考评分；全部样本打分。 |
| **出现的问题（思考）** | ✅ | 多选。implementation-reviewer 识别后勾选；选项来自 `config.yaml` 的 `thinking_efficiency_issue_options`（简单题过度思考 / 思考发散跑题 / 反复自我否定绕圈 / 思考不足直接猜 / 思考陷入死循环 / 其他 / 未出现显著问题）。 |
| **打分理由（思考）** | ✅ | 必须包含：轮次+动作、对交付/效率的具体影响；选「其他」需具体描述。由 reviewer 分析 + humanizer-zh 去 AI 化后写入。 |
| **ToolCall 效率** | ✅ | 1-5 分。implementation-reviewer 参考评分；全部样本打分。 |
| **出现的问题（ToolCall）** | ✅ | 多选。implementation-reviewer 识别后勾选；选项来自 `config.yaml` 的 `toolcall_efficiency_issue_options`（重复读取同一文件 / 文件间反复横跳 / 无效探索或无关调用 / 失败调用未能自行纠正 / 该用工具时不用 靠瞎猜 / 其他 / 未出现显著问题）。 |
| **打分理由（ToolCall）** | ✅ | 必须包含：轮次+工具名称+动作+对交付/效率的具体影响；选「其他」需具体描述。由 reviewer 分析 + humanizer-zh 去 AI 化后写入。 |

---

## 四、详细操作步骤

### 步骤 1：准备本地主分支

1. 从题目清单（如 `solo出题清单_GSB0723_sxw.xlsx`）中确定要测的 **Repo ID**。
2. 将对应主分支源码手动下载到：
   ```
   02.work session/session-gsb0723/source code/<Repo ID>/<Repo ID>/
   ```
3. 确认目录存在且内部有 `.git`。

### 步骤 2：运行 code-eval-gsb 提示词生成

触发方式：在对话中说明要执行 GSB setup，并提供 Repo ID。

该 skill 会：

- 读取 `scripts/gsb/config.yaml`
- 确认任务类型（必须人工从 `task_types` 中选择一种）
- 如果是 **Bug 修复**，会在 origin 仓注入 bug 并提交
- 将 origin 仓推送到 GitHub 公共仓库 `<Repo ID>`
- 为每个模型创建分支（Charmander / Squirtle / Bulbasaur）并 clone 到本地
- 调用 PromptArchitect + humanizer-zh 生成提示词
- 调用 `prompt_file_generator.py` 生成结果文件

生成后，每个类型目录下会有：

```
<Repo ID>-<类型>-charmander-对话内容.md
<Repo ID>-<类型>-squirtle-对话内容.md
<Repo ID>-<类型>-bulbasaur-对话内容.md
<Repo ID>-<类型>-charmander-评价结果.md
<Repo ID>-<类型>-squirtle-评价结果.md
<Repo ID>-<类型>-bulbasaur-评价结果.md
```

### 步骤 3：在 Trae 中执行模型测试

1. 为每个模型打开 **全新的 SOLO Agent 任务窗口**。
2. 复制对应 `-对话内容.md` 中的首轮提示词（含约束标签）到 Trae。
3. 按本期要求设置 **是否开启 Max**：
   - 70% 题目开启 Max（1M 上下文）
   - 30% 不开启
   - 同一道题的 3 个模型必须保持一致
4. 观察模型交互，记录：
   - 每轮回答的 **Trae Session ID**（复制到 `-对话内容.md`）
   - 每轮模型回答内容（可截图+摘要）
   - **最后一轮 context 占用**（Trae 底部 `X% of YK`）
   - 如触发自动压缩，需额外说明

> **轮次限制**：常规任务 ≤3 轮；长上下文/超长上下文任务可适当突破，鼓励多轮观察长上下文能力。

### 步骤 4：每轮结束后运行 code-eval-gsb 轮次分析

输入格式：

```
项目名：<Repo ID>
类型：<任务类型>
模型：<Charmander / Squirtle / Bulbasaur 或 slug>
轮次：<1 / 2 / 3>
```

该 skill 会：

- 读取本轮模型回答
- 调用 implementation-reviewer 评估
- 判断是否满意/不满意
- 不满意时生成下一轮追问提示词（写入 `-对话内容.md`）
- 将评价追加到 `-评价结果.md`
- 验证 Session ID 一致性

**注意**：追问提示词必须使用陈述/指令句式，针对产物 bug 或缺陷，不得针对验证流程。

### 步骤 5：全部完成后运行 code-eval-gsb 汇总

触发方式：对话中包含「汇总」二字，并提供 Repo ID、任务类型。

该 skill 会：

- 读取 3 个模型的 `-对话内容.md`
- 检查各分支代码变更（`git log main..HEAD`、`git diff main`）
- 调用 implementation-reviewer 给出 8 维度参考评分 + Bad Pattern + GSB 对比
- 调用 humanizer-zh 去 AI 化
- 生成 `<Repo ID>-<类型>-评价汇总.md`
- 执行 `cross_file_verifier.py` 验证 Session ID / Commit ID 一致性

### 步骤 6：人工核对与提交

打开 `-评价汇总.md`，重点核对：

1. **Session ID** 是否与 `-对话内容.md` 原文一致
2. **Prompt** 是否原文复制
3. **8 维度评分** 是否合理（Add-on 维度短窗口是否填 `N/A`）
4. **GSB 对比** 是否每题填了 3 条，且没有 Same/持平/各有优劣
5. **GSB 结论是否与平均分严格对齐**（胜者平均分必须更高）
6. **是否开启 Max** 和 **context 占用** 是否已补充
7. **代码理解类任务** 是否填写了 PR 链接

删除所有 `【参考值，请确认】` 标注后提交。

---

## 五、关键文件与路径

| 文件/目录                                                                       | 说明               |
| ------------------------------------------------------------------------------- | ------------------ |
| `scripts/gsb/config.yaml`                                                     | 本轮唯一配置入口   |
| `scripts/gsb/gsb 0723.md`                                                     | 本期完整需求文档   |
| `02.work session/session-gsb0723/source code/<Repo ID>/<Repo ID>/`            | 本地 origin 主分支 |
| `02.work session/session-gsb0723/source code/<Repo ID>/<Repo ID>-<slug>/`     | 各模型分支 clone   |
| `02.work session/session-gsb0723/ai-model-result/<Repo ID>/<Repo ID>-<类型>/` | 结果文件根目录     |
| `<Repo ID>-<类型>-<slug>-对话内容.md`                                         | 每模型对话记录     |
| `<Repo ID>-<类型>-<slug>-评价结果.md`                                         | 每模型轮次评价草稿 |
| `<Repo ID>-<类型>-评价汇总.md`                                                | 最终提交表单       |

---

## 六、常见注意事项

1. **严禁出题清单**：避免使用 贪吃蛇、俄罗斯方块、打砖块、五子棋、2048、电商购物车、RBAC 后台、博客 CMS、天气/番茄钟/习惯打卡等已被出烂的题目。
2. **Repo 防同质化**：同一 Repo 在一期众测中不超过总题量的 2%。
3. **约束标签**：每个 prompt 必须包含全部 5 种约束类型（技术栈/架构/代码风格/非代码回复/业务逻辑）。
4. **Max 模式**：同一题 3 个模型必须一致；记录到「是否开启 Max」。
5. **Context 占用**：每模型每题记录最后一轮 context 占用，含自动压缩说明。
6. **GSB 评价**：每题必填 3 条独立评价字段，分别描述每个模型相对另外两个模型的差距/优势。
7. **代码理解类**：必须有 PR（模型需将理解过程输出为新的 `.md` 文件并提交）。

---

## 七、快速检查清单

提交前逐条确认：

- [ ] 3 个模型 `-对话内容.md` 中 Session ID 已原文复制
- [ ] 最后一轮 context 占用已记录
- [ ] 是否开启 Max 已填写且三模型一致
- [ ] `-评价汇总.md` 中 8 维度评分完整，Add-on 短窗口填 `N/A`
- [ ] GSB 3 组对比均无 Same/持平/各有优劣
- [ ] GSB 胜者平均分严格高于败者
- [ ] Bad Pattern 识别具体、非空泛
- [ ] `cross_file_verifier.py` 验证通过
- [ ] 已删除所有 `【参考值，请确认】` 标注
