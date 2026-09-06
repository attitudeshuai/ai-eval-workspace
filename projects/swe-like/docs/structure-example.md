# swe-like 交付结构样例

> 以一道题为例，展示伪 Harbor 交付包结构。目录名 = 题目名称。

---

## 总览（一个 zip = 一道题）

```text
<题目名称>/
├── task.toml                 # 16 键底稿字段（题目背景信息）
├── instruction.md            # 需求 Prompt 原文
├── docs/
│   └── 底稿必填字段.md         # 人工回填备用（本地项目 / 无 lark-cli 时生成）
├── environment/
│   └── Dockerfile            # 基线 public.ecr.aws/x8v8d7g8/mars-base:latest，ARG BASE_SHA
├── tests/
│   └── nl_rubric.yaml        # 自然语言判分标准（≥5 条，f2p/p2p）
├── solution/                 # 本批允许留空
└── evidence/                 # 一次运行的取证
    ├── trajectory.jsonl      # TraeX 轨迹（或 trajectory.md / trajectory.json）
    ├── model.patch           # diff 基准 = base_commit
    └── screenshots/          # 运行结果截图（非空）
```

---

## 示例：restic 一题

```text
restic-01-prune-json-output/
├── task.toml
├── instruction.md
├── environment/
│   └── Dockerfile
├── tests/
│   └── nl_rubric.yaml
├── solution/
└── evidence/
    ├── trajectory.jsonl
    ├── model.patch
    └── screenshots/
        └── verify-passed.png
```

---

## task.toml 16 键

| 键 | 说明 |
|----|------|
| `title` | 题目名称（= zip 目录名） |
| `submitter` | 提交人（不回填） |
| `submit_date` | YYYY-MM-DD |
| `language` | Python / Go |
| `task_type` | 功能新增 / Bug 修复 / 测试增强 / 重构/性能 / 配置/工具链 / 其他 |
| `repo_url` | 原始仓库 URL |
| `base_commit` | 40 位完整 SHA，= Dockerfile BASE_SHA |
| `realism_and_difficulty` | 真实性与难度说明 |
| `modules` | 可能涉及模块 |
| `trae_session_id` | miniswe 留空 |
| `effective_turns` | 有效轮数（有效 TC） |
| `harness` | Trae / TraeX / miniswe |
| `seed_model` | Seed Evolving |
| `requirement_met` | 完成 / 部分完成 / 未完成 / 无法判断 |
| `run_result` | 逐条对应 rubric：id + 通过/未通过 + 原因 |
| `notes` | 备注（可空） |

---

## nl_rubric.yaml 样例

```yaml
rubrics:
  - id: 1
    type: f2p
    text: 功能默认关闭，关闭时保持现有行为。

  - id: 2
    type: f2p
    text: 开启后……（可观察行为）。

  - id: 3
    type: p2p
    text: 回归：既有测试不得回归。
```

> 至少 5 条，至少各 1 条 f2p 和 p2p。
