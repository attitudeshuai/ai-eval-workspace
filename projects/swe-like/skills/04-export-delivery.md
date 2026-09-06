---
name: swe-export-delivery
description: "SWE 交付导出：填 task.toml → toml2base.py 体检（--dry-run）→ 回填底稿；本地项目/无 lark-cli 时改生成 docs/底稿必填字段.md 供人工填写。Use when: SWE 导出, task.toml, toml2base, 底稿回填。"
---

# SWE 交付导出 · 回填底稿（网站表单）

> 现行：不再交付飞书，改为一题一个 zip（伪 Harbor）+ task.toml，用 toml2base.py 一键回填底稿。
> 规范见 `../docs/SWE-like Repo-v3.md`（第 2 / 7 节）与 `../docs/内部规范-v1.md`。

## 功能概述

1. （前置）去 AI 化：对 instruction.md 与 task.toml 的自然语言字段（真实性与难度说明、产物结果、notes）及底稿交付字段，按 `skills/humanizer-zh/SKILL.md` 全文过一遍，命中即改，不允许保留。
2. 组装交付包：`<题目名称>/`（task.toml + instruction.md + environment/Dockerfile + tests/nl_rubric.yaml + solution/ + evidence/）。
3. 填好 `task.toml` 的 16 个键。
4. 用 `toml2base.py --dry-run` 体检（不写库）。
5. 体检通过后 `toml2base.py` 回填底稿（整包 zip 上传「交付包」列）。

## 执行流程

```bash
# 1) 体检，不写库
python3 toml2base.py --dry-run <题目目录>

# 2) 体检通过后写入底稿（同一题重跑为更新原记录，不会重复建行）
python3 toml2base.py <题目目录>
```

> 环境要求：Python 3；`pip install pyyaml tomli`（3.11+ 无需 tomli）；`lark-cli auth login`；具备底稿编辑权限。缺任一项脚本会明确指出。
>
> **提交前强制**：先按 `skills/humanizer-zh/SKILL.md` 对 instruction.md、task.toml 自然语言字段和底稿交付字段做一次全量去 AI 化（禁用「」、——、反引号、加粗、列表符号、AI 高频词等），命中即改；有残留即使体检通过也不得提交。

## 人工回填（备用路径）

当满足以下任一情形时，`toml2base.py` 无法直接回填，改为在交付包生成 **`docs/底稿必填字段.md`**，由提交人逐字段复制到底稿：

- 本地项目 / 题库无远程 `repo_url`、`Fork Repo Commit URL` 取不到
- 环境里没有 `lark-cli` 或未完成 `auth login`（无底稿编辑权限）
- 底稿「需求预检记录」需先录入并通过，脚本写不进去

生成内容：把底稿**必填字段**（标 `*`）按「基础与仓库信息 / 出题内容与产物 / 运行记录」三组列出，值取自 `task.toml`、`instruction.md`、`tests/nl_rubric.yaml`，并标注截图、轨迹、预检记录这几项由提交人自行处理。注意：**每个字段的值直接内联在对应单元格里**（多行内容用 `<br>` 展开），不要用「见第 X 节」之类引用让提交人滚动查找各处正文。

注意：`repo_url`、`Fork Repo Commit URL` 依赖远程仓库，本地项目需提交人补填；`base_commit` 仍须与 `environment/Dockerfile` 的 `ARG BASE_SHA` 一致；`run_result` 须逐条对应 rubric（`<id> <通过|未通过> <原因>`），与人工作「是否完成需求」保持一致。

## task.toml 16 键（详见 Repo-v3 第 2 节）

| 键 | 说明 |
|----|------|
| `title` | 题目名称（= zip 目录名） |
| `submitter` | 提交人（不回填，底稿圈自己） |
| `submit_date` | YYYY-MM-DD |
| `language` | 仅 Python / Go |
| `task_type` | 功能新增 / Bug 修复 / 测试增强 / 重构/性能 / 配置/工具链 / 其他 |
| `repo_url` | 原始仓库 URL |
| `base_commit` | 40 位完整 SHA，= Dockerfile 的 ARG BASE_SHA |
| `realism_and_difficulty` | 真实性与难度说明 |
| `modules` | 可能涉及模块 |
| `trae_session_id` | miniswe 可留空 |
| `effective_turns` | 有效轮数（有效 TC，见 02-step-count） |
| `harness` | Trae / TraeX / miniswe |
| `seed_model` | Seed Evolving |
| `requirement_met` | 完成 / 部分完成 / 未完成 / 无法判断 |
| `run_result` | 逐条对应 rubric：id + 通过/未通过 + 原因 |
| `notes` | 备注（可空） |

## 退回红线（提交前自查）

- 必需文件缺失或空：task.toml、instruction.md、environment/Dockerfile、tests/nl_rubric.yaml、evidence/model.patch
- evidence/trajectory.jsonl、trajectory.json、trajectory.md 全都不存在或全为空
- harness 填 Trae 或 TraeX 却没填 trae_session_id
- evidence/screenshots/ 为空
- task.toml 的 title 与交付包目录名不一致
- 单选列取值不在底稿选项内
- base_commit 与 Dockerfile 的 ARG BASE_SHA 不一致
- task.toml 含规范外键或键名大小写不符
- rubric 少于 5 条、type 不为 f2p/p2p、id 重复，或无 f2p 条目
- 产物结果未逐条对应 rubric，或与「是否完成需求」矛盾
- instruction.md 或 rubric 残留 `<……>` 占位
- instruction.md / 底稿字段残留 AI 痕迹（「」、——、反引号、加粗、列表符号等，按 `skills/humanizer-zh/SKILL.md` 判定）

## 附件

- `count_steps.py`：自查 `effective_turns`（对 `.trae/cli/sessions/` 原始轨迹跑）。
- `harbor-交付模板包.zip`：模板，解压后把「请改成题目名称」目录重命名为本题题目名称。
