# Mock 数据

本目录用于存放任务所需的 Mock 数据（JSON 格式），供前端开发使用。

## 使用方式

在前端项目中通过 Mock 服务或直接 import 加载：

```typescript
// 示例：在 src/mock/index.ts 中加载
import users from '../../mock-data/users.json'
```

## 规范

请遵循 `templates/task/mock-data/README.md` 中的规范编写数据文件：

- 文件名使用 `snake_case.json`
- UTF-8 编码
- 完整覆盖任务所有模块
- 数据贴近真实业务场景

## 任务创建后

当你使用 `create_task.py` 创建新任务后，AI Agent 会在此目录下生成对应的 JSON 数据文件（如 `users.json`、`tables.json` 等）。如果发现缺少文件，请通知 AI Agent 补充。
