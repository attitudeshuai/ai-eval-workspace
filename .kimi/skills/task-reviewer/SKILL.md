# Task Reviewer

Review 指定项目中的任务是否符合高难度长程任务标准。

## 触发条件

当用户要求 review 任务、检查任务质量、或任务准备交付时调用本技能。

## 工作流程

1. 确认目标项目 ID。
2. 读取任务目录下所有文件。
3. 对照 `docs/quality-gates.md` 逐项检查六大量闸门。
4. 运行 `python scripts/validate_task.py projects/<id>/tasks/<task-id>`。
5. 输出 review 报告，列出问题与修改建议。

## Review 输出格式

```markdown
# Task Review: <project-id>/<task-id>

## 总体结论
[通过 / 有条件通过 / 不通过]

## 详细检查

### 1. 可运行性
- [x] lockfile 存在
- [ ] npm install 失败：...

### 2. 任务完整性
...

## 阻塞问题
1. ...

## 建议改进
1. ...
```

## 判断标准

- 任一闸门失败即不通过。
- 无阻塞问题但有小缺陷可标记为“有条件通过”。
