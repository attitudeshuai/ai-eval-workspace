---
name: task-reviewer
description: 'Review eval tasks against quality gates to ensure high-difficulty long-horizon standards. Use when reviewing task quality, checking tasks before delivery, 审查任务, 检查任务质量, 任务交付审查, quality gate check.'
---

# Task Reviewer

对照 `docs/quality-gates.md` 审查指定项目中的任务是否符合高难度长程任务标准。

## When to Use

- 用户要求 review 任务
- 任务准备交付前需要质量审查
- 需要检查任务是否满足六大量闸门

## 前置确认

调用前需确认：
- **目标项目 ID**
- **任务 ID**

## Procedure

### 1. 读取项目约定

读取项目级文档确认校验方式：
- `projects/<project-id>/AGENTS.md`
- `projects/<project-id>/OPERATIONAL_WORKFLOW.md`
- `projects/<project-id>/config.toml`

### 2. 读取任务全部文件

读取任务目录下所有文件，包括：
- `task.md`
- `metadata.json`
- `rubric.json`
- `target_states.md`
- `README.md`
- `assets/`
- `mock-data/`

### 3. 逐项检查六大量闸门

对照 [quality-gates.md](../../docs/quality-gates.md) 逐项检查：

1. **可运行性**：lockfile 存在、npm install 成功、npm run dev 可启动
2. **任务完整性**：所有必需文件存在且内容完整
3. **评估可操作性**：rubric 叶节点有明确证据类型
4. **视觉参考完备性**：至少 4 类关键状态截图
5. **独立性**：不依赖外部不可控服务
6. **安全性**：不泄露答案、不含敏感信息

### 4. 运行校验脚本

```bash
# 通用校验
python scripts/webdev-long-horizon/validate_task.py \
  projects/<project-id>/tasks/<task-id>

# webdev 外部 source 模式
python scripts/webdev-long-horizon/validate_task.py \
  --allow-no-starter \
  <task-id>
```

### 5. 输出 Review 报告

## 输出格式

```markdown
# Task Review: <project-id>/<task-id>

## 总体结论
[✅ 通过 / ⚠️ 有条件通过 / ❌ 不通过]

## 详细检查

### 1. 可运行性
- [x] lockfile 存在
- [x] npm install 成功
- [ ] npm run dev 失败：端口冲突

### 2. 任务完整性
- [x] task.md 存在且内容完整
- [x] rubric.json 格式正确（15 个叶节点）
- [x] target_states.md 覆盖 4 类状态

### 3. 评估可操作性
- [x] 所有叶节点有明确证据类型
- [ ] r005 证据类型不明确（标记为 manual_review 但缺少判断标准）

### 4. 视觉参考完备性
- [x] desktop.png 存在
- [x] mobile.png 存在
- [ ] 缺少 empty_state.png

### 5. 独立性
- [x] 无外部登录依赖
- [x] 无付费 API 调用

### 6. 安全性
- [x] task.md 无答案泄露
- [x] 源码无硬编码密钥

## 阻塞问题
1. 缺少 empty_state.png 参考截图
2. r005 证据类型不明确

## 建议改进
1. 补充空状态参考截图
2. 为 r005 添加明确的判断标准
```

## 判断标准

- **通过**：所有闸门检查通过，无阻塞问题
- **有条件通过**：无阻塞问题但有小缺陷（如缺少非必要的参考截图）
- **不通过**：任一闸门失败（如无法启动、缺少必需文件、答案泄露）

## 与其他 Skill 的关系

- 通常在 `task-creator` / `webdev-greenfield-task-creator` / `webdev-incremental-task-creator` 之后运行
- 审查通过后任务可以进入 SOTA 运行阶段（`sota-runner` / `webdev-sota-runner`）
