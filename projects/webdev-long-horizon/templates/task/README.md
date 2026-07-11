# {{title}}

## 任务简介

[一句话描述任务目标]

## 目录结构

```text
.
├── task.md              # 完整任务需求
├── metadata.json        # 任务元数据
├── README.md            # 本文件
├── assets/              # 参考截图与素材
├── mock-data/           # mock 数据
├── tests/               # Playwright / 单元测试
├── rubric.json          # 验收标准
├── target_states.md     # 关键状态说明
├── sota-run.md          # SOTA 运行记录
└── screenshots/         # 最终截图
```

源码管理方式（二选一）：

- **外部 source**（推荐）：`../sources/{{task_id}}/`
- **内置 starter**（传统）：`./starter/`

## 启动方式

若使用外部 source：

```bash
cd ../sources/{{task_id}}
npm install
npm run dev
```

若使用内置 starter：

```bash
cd starter
npm install
npm run dev
```

## 测试方式

```bash
# 单元测试
cd <source-dir>
npm run test

# 或运行 Playwright
cd ..
npx playwright test tests/playwright.spec.ts
```

## 已知限制

- [限制 1]
- [限制 2]
