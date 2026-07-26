# Mock 数据模板说明

本目录定义 `mock-data/` 的结构规范，供 AI Agent 在生成任务资产时参考。

> `create_task.py` 不会自动复制本目录。当你运行 `create_task.py` 后，需要在此任务目录下手动创建 `mock-data/` 并填充 JSON 数据文件。

## 目录结构

```text
mock-data/
├── README.md                # 使用说明（含测试账号、数据关系图）
├── users.json               # 登录认证
├── dashboard.json           # 数据概览 / 首页看板
├── tables.json              # 表列表（核心资源）
├── table_fields.json        # 表字段定义
├── table_sample_data.json   # 表样例数据
├── table_change_log.json    # 表变更记录
├── dictionary.json          # 数据字典
├── lineage.json             # 数据血缘（nodes + edges）
├── quality_rules.json       # 质量规则列表
├── quality_reports.json     # 质量报告（评分、趋势、失败样本）
├── tags.json                # 标签管理（categories + tags）
└── search_index.json        # 搜索索引
```

## 命名规范

- 文件名使用 `snake_case.json`
- 文件内容使用 UTF-8 编码
- 每个 JSON 文件应包含完整的、可直接被前端 Mock 服务加载的数据
- 数据字段应尽量贴近真实业务场景

## 数据完整性要求

| 模块 | 对应文件 | 最低数据量 |
|------|----------|-----------|
| 登录认证 | `users.json` | ≥ 2 个用户，包含 admin 角色 |
| Dashboard | `dashboard.json` | 统计卡片数据 + 趋势数组 ≥ 5 条 + 分布数据 |
| 数据表 | `tables.json` | ≥ 15 张表 |
| 表字段 | `table_fields.json` | ≥ 3 张表的字段定义 |
| 表样例 | `table_sample_data.json` | ≥ 2 张表的样例数据 |
| 表变更 | `table_change_log.json` | ≥ 3 张表的变更记录 |
| 数据字典 | `dictionary.json` | ≥ 5 个字典类型，每个 ≥ 3 个字典项 |
| 数据血缘 | `lineage.json` | ≥ 10 个节点 + ≥ 10 条边 |
| 质量规则 | `quality_rules.json` | ≥ 10 条规则，覆盖 ≥ 3 个维度 |
| 质量报告 | `quality_reports.json` | 含评分、趋势、失败样本 |
| 标签 | `tags.json` | ≥ 3 个分类，每个 ≥ 3 个标签 |
| 搜索 | `search_index.json` | ≥ 20 条可搜索记录 |

## 使用方式

`mock-data/` 下的 JSON 文件在前端项目中通过 Mock 服务加载，例如：

```typescript
// src/mock/index.ts
import users from '../../mock-data/users.json'
import tables from '../../mock-data/tables.json'
// dashboard, dictionary, lineage 等同理
```

或通过专门的 Mock 中间件自动加载 `mock-data/` 目录下的所有 JSON 文件。

## 生成步骤

1. 运行 `create_task.py` 生成任务骨架
2. 根据任务需求编写各 JSON 文件
3. 将数据文件放入任务目录下的 `mock-data/`
4. 在 `task.md` 中补充 Mock 数据说明和测试账号

## 常见数据字段说明

### users.json
```json
[
  {
    "id": 1,
    "username": "admin",
    "password": "admin123",
    "nickname": "管理员",
    "role": "admin",
    "permissions": ["*"],
    "status": "active"
  }
]
```

### tables.json
```json
[
  {
    "id": "TBL-001",
    "name": "user_base_info",
    "display_name": "用户基础信息表",
    "description": "存储用户注册信息",
    "database": "MySQL",
    "tier": "ODS",
    "row_count": 12500000,
    "field_count": 16,
    "tags": ["用户行为", "基础数据"],
    "updated_at": "2026-07-12 14:30:00"
  }
]
```

### lineage.json
```json
{
  "nodes": [
    { "id": "n1", "name": "user_base_info", "type": "table", "tier": "ODS" }
  ],
  "edges": [
    { "source": "n1", "target": "n6", "relation": "source" }
  ]
}
```
