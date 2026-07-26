---
name: gsb-prompt-generate
description: "GSB 提示词生成：源码推送 GitHub、创建对比分支、并生成提示词供多模型对比评测。Use when: GSB 项目初始化, 推送 GitHub, 生成对比提示词。"
---

# GSB 提示词生成（Setup + Generate）

> 配置从 `../config.toml` 读取，`secrets.toml` 中可覆盖。
> 依赖 agent：`skills/prompt-architect/SKILL.md`、`skills/humanizer-zh/SKILL.md`

GSB 多模型对比评测的第一步。核心目标：为参与对比的多个模型提供完全一致的起点代码 + 一条经去 AI 化优化的共享提示词。

## 功能概述

这个技能负责：

- 验证本地 origin 仓已就绪
- 将源码推送到 GitHub 仓库
- 在 GitHub 上创建各模型对比分支并推送
- 将各分支分别 clone 到本地独立目录
- 对 origin 仓代码进行类型分析，由用户确认任务类型
- 调用 `prompt-architect` agent 生成**单条**提示词
- 调用 `humanizer-zh` agent 对提示词进行去 AI 化优化
- 将最终提示词写入对应结果目录

这个技能不负责：

- 对分支仓库进行任何代码修改
- 执行模型测试或记录模型回答
- 多条提示词批量生成（GSB 每次只生成一条）

## 命令

| 命令 | 说明 |
|------|------|
| setup | 默认命令。确认任务类型→（Bug 修复类则在 origin 注入 bug）→推送 GitHub→创建并拉取对比分支→**自动进入 generate 流程** |
| generate | 传入已确认的类型，生成并优化单条提示词、写入结果文件 |
| info | 仅输出项目名和仓库地址，不执行任何操作 |

## 默认配置

> 配置从 `../config.toml` 的 `[github]`/`[[models]]`/`[[comparisons]]`/`[paths]` 段读取。模型列表从 `[[models]]` 读取（name/slug），对比组合从 `[[comparisons]]` 读取（pair 下标 + required）。session 名从 `[sessions].active` 读取。

## 执行流程

### setup（默认命令）

1. 用户输入项目名（如 `demo-hello`）。
2. 校验 origin 仓 `{work_root}/{session}/source code/<项目名>/<项目名>-origin/` 存在且有 `.git`。
3. 扫描 origin 仓项目结构，展示初步分析摘要，**需要用户从以下 7 种类型中确认一种**：

   | 类型 | 说明 |
   |------|------|
   | Bug 修复 | 定位并修复现有 bug |
   | 0-1 代码生成 | 从零开始实现新功能或新模块 |
   | Feature 迭代 | 在现有功能基础上追加小功能 |
   | 代码理解 | 解释逻辑、梳理调用链、分析风险 |
   | 工程化 | 环境、构建、配置、CI/CD 相关 |
   | 代码重构 | 性能、可读性、解耦，不改变行为 |
   | 代码测试 | 覆盖正常/异常/边界三类路径的测试 |

   **类型未经用户确认，禁止进行后续任何操作。**

6. 用户确认类型后，根据类型走不同分支：

   **若类型为『Bug 修复』：**
   - 调用 `prompt-architect` agent，根据代码设计一个想实际线上会出现的 bug（逻辑、业务、状态、权限等）。
   - 将 bug 注入 **origin 仓本地文件**，做最小验证（类型分析确认可复现）。
   - 在 origin 仓内提交 bug：
     ```bash
     git add -A
     git commit -m "inject bug for gcs evaluation"
     ```
   - **bug 注入完成后，禁止再对 origin 仓做任何代码修改。**

   **若类型为其他 6 种：**
   - origin 仓保持原样，直接进入下一步。

7. 在 origin 仓目录内，配置 GitHub 远程地址、首次推送到 `<项目名>` 仓库。

8. 推送完成后，在 GitHub 上从 main 创建各模型对比分支（分支名 = 模型 slug）：

   ```bash
   git push origin main:spring
   git push origin main:summer
   ```

   > 若类型为 Bug 修复，各分支因继承自 main 而自动包含相同的 bug。

9. 将各分支分别 clone 到本地独立目录（从 GitHub 拉取）：

   ```bash
   git clone -b spring git@github.com:attitudeshuai/<项目名>.git \
     "{work_root}/{session}/source code/<项目名>/<项目名>-spring"
   ```

10. 验证所有本地目录均存在（origin + 各分支）。
11. 输出汇总：GitHub 地址、本地目录列表、分支状态、**确认的任务类型**。
12. **setup 完成后，立即自动执行 generate 流程**，无需用户再次输入命令。

### generate

1. 用户传入 setup 阶段已确认的任务类型。
   - 若未传入类型，必须让用户手动确认，不能跳过。
2. 读取 origin 仓代码，结合确认的类型**调用 `prompt-architect` agent**，传入项目名、类型（配额固定 `*1`）和 origin 仓代码目录上下文：
   - Bug 修复类型：代码中已有 bug，prompt 描述 bug 现象和触发条件，**不要把 bug 代码位置或修复方案交出**。
   - 其他类型：按类型策略正常出题。
3. 将 prompt-architect 输出的提示词**交给 `humanizer-zh` agent** 进行去 AI 化优化，确保语气自然、口语化，像真实工作里的需求或抛出的问题。
4. 为提示词添加**全部 5 种约束标签**（缺一不可），附到提示词正文末尾：

   | 约束类型 | 示例内容 |
   |----------|----------|
   | 技术栈或依赖约束 | 项目已有 xlsx.js，不要引入其他依赖 |
   | 架构或模式约束 | 现有项目是原生 JS，不要引入框架或构建工具 |
   | 代码风格或规范约束 | 保持现有的函数命名风格，不要改名 |
   | 非代码回复约束 | 只输出需要修改的文件，不要全量输出 |
   | 业务逻辑约束 | 已中奖记录不允许被修改 |

   Bug 修复类型在「非代码回复约束」中必须明确要求不要暴露修复方向。

5. 将优化后的提示词（含约束标签）写入结果文件——每个模型对应 1 份对话内容 + 1 份评价结果。
6. ⚠️ **写入完成即为 generate 流程的终点。禁止对任何分支仓库进行任何操作。**

### info

1. 用户输入一个或多个项目 ID。
2. 补全项目名。
3. 输出 GitHub 地址、本地目录结构预览。
4. 不执行任何 clone、push、写文件操作。

## 路径规则

```
# origin 仓（本地源码）
{work_root}/{session}/source code/<项目名>/<项目名>-origin/

# 各模型分支仓（从 GitHub clone，分支名 = 模型 slug）
{work_root}/{session}/source code/<项目名>/<项目名>-{模型slug}/

# 模型结果根目录
{work_root}/{session}/ai-model-result/<项目名>/

# 类型结果目录
{work_root}/{session}/ai-model-result/<项目名>/<项目名>-{ALIAS}/

# 对话内容文件（每模型一份，内容一致）
{work_root}/{session}/ai-model-result/<项目名>/<项目名>-{ALIAS}/<项目名>-{ALIAS}-<模型名>-对话内容.md

# 评价结果文件（每模型一份，空白模板）
{work_root}/{session}/ai-model-result/<项目名>/<项目名>-{ALIAS}/<项目名>-{ALIAS}-<模型名>-评价结果.md

# 评价汇总文件
{work_root}/{session}/ai-model-result/<项目名>/<项目名>-{ALIAS}/<项目名>-{ALIAS}-评价汇总.md
```

> ⚠️ **origin 仓与各分支仓同级并列，均在 `<项目名>/` 下，禁止相互嵌套。**

## 对话内容文件模板（各模型内容完全一致）

```markdown
<项目名>-{ALIAS}-01

用户第一次提示词：<humanizer-zh 优化后的提示词内容>

约束标签：
- 技术栈或依赖约束：<具体约束内容>
- 架构或模式约束：<具体约束内容>
- 代码风格或规范约束：<具体约束内容>
- 非代码回复约束：<具体约束内容>
- 业务逻辑约束：<具体约束内容>

注：约束标签必须包含上述全部 5 种类型，固定格式为「约束类型：内容」。

是否开启 Max：<是 / 否>（各模型同一题保持一致）

模型第一次回答 trae session id：

模型第一次回答内容：



用户第二次提示词：

模型第二次回答内容：



用户第三次提示词：

模型第三次回答内容：



最后一轮 context 占用：<X% of YK>（如触发自动压缩，记"在第 N 轮触发了自动压缩"）
```

## 评价结果文件模板（每个模型独立一份）

```markdown
<项目名>-{ALIAS}-{slug}-评价结果

模型：<模型原始名称>（分支：{slug}）

## 第一轮评价

## 输入规则

支持的项目 ID 输入形式：

- 直接提供项目名（如 label-01035、demo-hello）

如果用户明确指定项目名，以用户提供的为准。

## 认证说明

| 远程 | 方式 | 说明 |
|------|------|------|
| GitHub | SSH（优先）/ HTTPS + PAT | PAT 在 secrets.toml 中 |

## 注意事项

1. **GSB 每次固定只生成 1 条提示词**。
2. 任务类型必须在 GitHub 推送之前确认。
3. Bug 修复：bug 只在 origin 注入一次，commit 后推送 GitHub main。
4. 各分支仓是模型执行时的工作区，**generate 完成后不再触碰**。
5. humanizer-zh 优化是必须步骤。
6. GitHub 仓库可见性必须为 public。
7. 约束标签 5 种全部必填。