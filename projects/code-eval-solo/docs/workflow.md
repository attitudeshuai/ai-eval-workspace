# code-eval-solo 操作流程

## 前置条件

- 已配置 `secrets.toml`
- Python 环境已就绪

---

## 一、放置源码

将项目源码放到 `{work_root}/{SESSION_NAME}/source code/{项目名}/`，确保已 `git init`。

---

## 二、生成提示词

```
使用 code-eval-solo 技能，项目 demo-hello，generate：
bugfix*5  codegen*5  feature*5  understand*1  refactor*1  engineering*1  test*1
```

AI 将：
1. 扫描项目结构，调用 prompt-architect 生成提示词
2. 写入提示词文件到 `{work_root}/{SESSION_NAME}/ai-model-result/{项目名}/`
3. Bug 修复类型在主仓注入 bug

---

## 三、分析结果

```
使用 code-eval-solo 技能，分析 demo-hello 的 bugfix-01，第 1 次对话
```

AI 将：
1. 读取提示词文件和模型回答
2. 通过 git 获取代码变更
3. 调用 implementation-reviewer + 10 维度过程分析
4. 写入评价结果文件

---

## 四、导出

```
solo demo-hello export
```

输出 CSV 到 `deliverables/code-eval-solo/{SESSION_NAME}/{项目名}/`。

---

## 五、文件命名约定

| 场景 | 格式 | 示例 |
|------|------|------|
| 提示词文件 | `{项目名}-{ALIAS}-{index}.md` | `demo-hello-bugfix-01.md` |
| 评价结果 | `{项目名}-{ALIAS}-{index}-评价结果.md` | `demo-hello-bugfix-01-评价结果.md` |

## 六、目录布局

```
{work_root}/{SESSION_NAME}/
├── source code/
│   └── demo-hello/                  # 主仓
│       ├── .git/
│       └── index.html
└── ai-model-result/
    └── demo-hello/
        └── demo-hello-bugfix/
            ├── demo-hello-bugfix-01.md
            └── demo-hello-bugfix-01-评价结果.md
```
