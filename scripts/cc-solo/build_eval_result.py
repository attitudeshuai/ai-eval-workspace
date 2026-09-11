#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 评价结果生成（替代原「正式提交表 CSV + 飞书投递」）
=========================================================
先 GET 平台表单定义接口校验字段规范（见 check_form_schema.py），再按下述规范把
{work_root}/{SESSION}/records/ 下每个任务的共享字段（task-info.md）与每轮数据（{任务}-R{NN}.md）
合成**一轮 = 一条评价结果**，输出：

    deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}.json      ← 提交接口的载荷来源（唯一产物）
    deliverables/cc-solo/{SESSION}/评价结果-{SESSION}-{date}-质检报告.md  ← 逐条 error / warn

    （**不再生成人工核对 CSV**，已按要求取消该导出。）

用法：
    python scripts/cc-solo/build_eval_result.py
    python scripts/cc-solo/build_eval_result.py --session session-0909
    python scripts/cc-solo/build_eval_result.py --task h5-demo-feature-01
    python scripts/cc-solo/build_eval_result.py --out /tmp/x.json

说明：
- 只读记录文件；不改动任何数据。
- 校验：① 表单规范（必填/选项/数值范围/长度/URL 正则）；② 项目规则（首轮非简单、
  SessionID 一致、TurnID 唯一、轮次 ≤10、轨迹文件存在、分数与描述方向一致等）；
  ③ 去 AI 化层（humanizer 强制符号 / AI 套话词 / 长英文串 / 跨轮次承接表述）。
- 轨迹文件是「附件」类型，本脚本只填**本机路径**；真正提交前由 submit_eval_result.py 上传拿到
  远端 path 再回填（见 json 里的 upload_api）。
"""
import argparse
import datetime
import json
import os
import re
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.toml")
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.toml")
FIELDS_PATH = os.path.join(PROJECT_DIR, "docs", "submission", "fields.json")

DIMENSIONS = [  # 记录文件里的中文小标题 → 表单字段
    ("交付完整性", "score_delivery", "desc_delivery"),
    ("指令遵循", "score_instruction", "desc_instruction"),
    ("任务规划", "score_planning", "desc_planning"),
    ("推理能力", "score_reasoning", "desc_reasoning"),
    ("执行能力", "score_execution", "desc_execution"),
]

# 分数与描述方向一致性（提示项，不自动改）
STRONG_NEG = ("未完成", "没完成", "没改", "未实现", "未提供", "未处理", "失败", "无法运行",
              "不可用", "虚假", "答非所问", "一行代码", "严重幻觉", "死循环", "编译不过",
              "跑不通", "无法编译", "没跑通", "压根没")
NEG_ANY = STRONG_NEG + ("报错", "错误", "幻觉", "编造", "臆造", "瞎猜", "无视", "无头苍蝇",
                        "冗余", "缺失", "遗漏", "漏掉", "滥用", "低效", "反复", "重复",
                        "卡住", "绕圈", "无效", "不符合", "多余", "越界", "擅自")
# AI 写作痕迹（提示项：交付文本须已过去 AI 化）
AI_TRACE = ("——", "综上所述", "总而言之", "首先，", "其次，", "总的来说", "需要注意的是",
            "不仅仅是", "更是", "赋能", "助力", "深度剖析")

# humanizer-zh 的强制清除符号（交付文本一经出现必须清除）；命中即 error，阻塞提交
HUMANIZER_SYMBOLS = ("——", "`", "「", "」", "→", "⇒", "=>", "->", "\"", "'")

# 项目补充红线：形近破折号的写法（连续两个汉字「一」），机器审核容易与「——」混淆
# 命中即 error（五个「-描述」），hint 字段记 warn（可能含人工原文，不改写）
PROJECT_SYMBOLS = ("一一",)
PROJECT_SYMBOLS_FIX = "改写成「逐条对上」「逐项对应」「各条对应」这类说法"

# AI 套话/空词（评价结果里一律不用）；命中即 error，阻塞提交
# 「模型」指被评测的 AI 时改用「它」；指 Django 数据模型时写「数据定义」或引用 models.py 里的类名
BANNED_CLICHE = ("落地", "模型", "赋能", "助力", "闭环", "抓手", "沉淀", "复用", "对齐", "打通",
                 "链路", "颗粒度", "场景化", "心智", "拉通", "复盘", "生态", "矩阵", "调性",
                 "层面", "体现")

# 跨轮次承接表述：每条描述必须能**独立阅读**，不得依赖其他轮次
# （平台实测按此返修：'描述中出现了「上一轮」这一依赖其他轮次才能理解的承接表述，导致该段描述无法被独立阅读'）
CROSS_ROUND = ("上一轮", "前一轮", "上轮", "上一次轮", "之前的轮次", "前面几轮", "本轮之前")

# 长英文串（命令 / 参数 / 标识符 / 路径）：平台的 B-5「公共长片段」查重按连续字符比对，
# 长英文串在别的提交里也常见 → 容易被判「套模板」打回。评价里尽量写成中文。
LONG_TOKEN_MIN = 12      # ≥12 个连续英文字符：warn（提示改写）
LONG_TOKEN_ERROR = 16    # ≥16 个连续英文字符：error（基本必被打回）
LONG_TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\-]{%d,}" % LONG_TOKEN_MIN)

# 字段 key → 中文名（仅用于质检信息展示）
FIELD_CN = dict({"other_issues": "其他问题", "user_prompt": "User Prompt", "languages": "语言/框架"},
                **{dkey: cn for cn, _, dkey in DIMENSIONS})

# 进入提交 body 的 AI 起草正文字段：humanizer 强制符号命中即 error，阻塞提交
AI_TEXT_FIELDS = tuple(dkey for _, _, dkey in DIMENSIONS)
# 不进提交 body、或可能是人工原文的字段：只提示、不阻塞
#   other_issues —— 选填字段，一律不进提交 body
#   user_prompt  —— 可能是人工原文（规范要求「人工原文不改写」）
AI_TEXT_HINT_FIELDS = ("other_issues", "user_prompt", "languages")


# ------------------------------------------------------------------ 基础读取
def read_utf8(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def parse_blocks(text):
    """按行首 '## ' 切块：{标题: 内容}（值保留多行）。"""
    blocks, cur = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            blocks[cur] = []
        elif cur is not None:
            blocks[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in blocks.items()}


def load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_settings():
    cfg, sec = load_toml(CONFIG_PATH), load_toml(SECRETS_PATH)
    work_root = cfg.get("paths", {}).get("work_root", "sessions/cc-solo")
    records_dir = cfg.get("paths", {}).get("records_dir", "records")
    deliverables = cfg.get("paths", {}).get("deliverables_root", "deliverables/cc-solo")
    session_secrets = sec.get("active_session")
    session_config = cfg.get("sessions", {}).get("active")
    container = cfg.get("container", {})
    submission = dict(cfg.get("submission", {}))
    submission.update({k: v for k, v in sec.get("submission", {}).items() if v})
    return {
        "work_root": work_root,
        "records_dir": records_dir,
        "deliverables_root": deliverables,
        "session": session_secrets or session_config or "session-0909",
        "session_secrets": session_secrets,
        "session_config": session_config,
        "max_rounds": int(cfg.get("limits", {}).get("max_rounds", 10)),
        "container": container,
        "submission": submission,
    }


def load_spec():
    if not os.path.exists(FIELDS_PATH):
        print(f"[错误] 缺少字段规范 {FIELDS_PATH}\n       先跑：python scripts/cc-solo/extract_submit_fields.py")
        sys.exit(2)
    with open(FIELDS_PATH, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ 取值
def shared_values(info, cfg, spec):
    """task-info.md → 共享字段。"""
    snap = info.get("初始环境快照", "")
    snap = re.sub(r"[（(].*?[）)]", " ", snap)          # 去掉尾部的中文说明
    snap = snap.strip().split()[0] if snap.strip() else ""
    return {
        "harness": info.get("Harness", "").strip(),
        "harness_version": info.get("Harness版本", "").strip(),
        "os_platform": info.get("操作系统", "").strip(),
        "repro_level": info.get("环境可复现等级", "").strip(),
        "env_snapshot": snap,
        "session_id": info.get("SessionID", "").strip(),
    }


def round_values(blocks, spec):
    """{任务}-R{NN}.md → 本轮字段。"""
    vals = {
        "question_type": blocks.get("任务类型", "").strip(),
        "difficulty": blocks.get("任务难度", "").strip(),
        "languages": blocks.get("语言/框架", "").strip(),
        "user_prompt": blocks.get("User Prompt", "").strip(),
        "turn_id": blocks.get("TurnID/PromptID", "").strip(),
        "other_issues": blocks.get("其他问题", "").strip(),
    }
    for cn, skey, dkey in DIMENSIONS:
        vals[skey] = blocks.get(cn, "").strip()
        vals[dkey] = blocks.get(f"{cn}-描述", "").strip()
    return vals


def to_int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ 校验
def validate(fields, spec, ctx, issues):
    """表单规范校验（spec 驱动）+ 项目规则。"""
    by_key = {f["field_key"]: f for f in spec["fields"]}
    for key, fld in by_key.items():
        raw = fields.get(key)
        if fld["field_type"] == "number":
            iv = to_int(raw)
            if iv is None:
                if fld["is_required"] or str(raw).strip():
                    issues.append(("error", key, f"{fld['label']} 缺失或不是整数：{raw!r}"))
                continue
            v = fld.get("validation", {})
            if str(v.get("integer", True)).lower() != "false" and iv != float(raw if raw != "" else 0):
                pass
            lo, hi = v.get("min"), v.get("max")
            if lo is not None and iv < lo:
                issues.append(("error", key, f"{fld['label']}={iv} 小于下限 {lo}"))
            if hi is not None and iv > hi:
                issues.append(("error", key, f"{fld['label']}={iv} 大于上限 {hi}"))
            continue

        text = "" if raw is None else str(raw)
        if not text.strip():
            if fld["is_required"]:
                issues.append(("error", key, f"{fld['label']} 为必填但为空"))
            continue
        opts = fld.get("options") or []
        if opts and text not in opts:
            issues.append(("error", key, f"{fld['label']}={text!r} 不在允许选项内：{opts}"))
        ml = fld.get("max_length") or 0
        if ml and len(text) > ml:
            issues.append(("error", key, f"{fld['label']} 长度 {len(text)} 超过上限 {ml}"))
        pat = (fld.get("validation") or {}).get("pattern")
        if pat and not re.match(pat, text):
            issues.append(("error", key,
                           f"{fld['label']} 不符合格式要求（{fld['validation'].get('pattern_message', '')}）：{text[:80]}"))

    # 项目规则
    if ctx["round"] == 1 and fields.get("difficulty") == "简单":
        issues.append(("error", "difficulty", "首轮严禁「简单」"))
    if to_int(fields.get("x_iteration")) != ctx["round"]:
        issues.append(("error", "x_iteration", f"当前对话轮次排序={fields.get('x_iteration')} 与轮次 R{ctx['round']:02d} 不一致"))
    if not ctx["trace_exists"]:
        issues.append(("error", "trace_file", f"轨迹文件不存在：{ctx['trace_local']}"))

    # 分数与描述方向 + 描述质量 + AI 痕迹
    for cn, skey, dkey in DIMENSIONS:
        sc, desc = to_int(fields.get(skey)), fields.get(dkey, "")
        if sc is None:
            continue
        if sc >= 4 and any(t in desc for t in STRONG_NEG):
            issues.append(("warn", dkey, f"{cn}={sc} 但描述含强失败词，须人工复核一致性"))
        if sc <= 2 and not any(t in desc for t in NEG_ANY):
            issues.append(("warn", dkey, f"{cn}={sc} 但描述未见负面证据，须人工复核一致性"))
        if desc and len(desc) < 8:
            issues.append(("warn", dkey, f"{cn}-描述过短（{len(desc)} 字），疑似笼统"))
        hit = [t for t in AI_TRACE if t in desc]
        if hit and dkey not in AI_TEXT_FIELDS:
            issues.append(("warn", dkey, f"{cn}-描述疑似 AI 写作痕迹：{'、'.join(hit)}（须先去 AI 化）"))

    # AI 痕迹（红线：提交 body 的所有字段须已过 humanizer-zh 完整流程；本处只做机械兜底）
    # 符号类 = humanizer 强制项，命中即 error 阻塞提交；高频词类 = warn，需人工复核
    for key in AI_TEXT_FIELDS:
        text = str(fields.get(key) or "")
        if not text.strip():
            continue
        label = FIELD_CN.get(key, key)
        sym = [s for s in HUMANIZER_SYMBOLS if s in text]
        if sym:
            issues.append(("error", key,
                           f"{label} 含 humanizer-zh 强制清除符号 {'、'.join(sym)}，"
                           f"须按 skills/humanizer-zh 完整流程去 AI 化后重录"))
        psym = [s for s in PROJECT_SYMBOLS if s in text]
        if psym:
            issues.append(("error", key,
                           f"{label} 含项目补充红线写法（形近破折号，易与 —— 混淆）：{'、'.join(psym)}；"
                           f"{PROJECT_SYMBOLS_FIX}"))
        word = [t for t in AI_TRACE if t in text]
        if word:
            issues.append(("warn", key, f"{label} 疑似 AI 高频词：{'、'.join(word)}（须人工复核）"))
        cl = [w for w in BANNED_CLICHE if w in text]
        if cl:
            issues.append(("error", key,
                           f"{label} 含 AI 套话词 {'、'.join(cl)}（评价结果里一律不用：指被评测的 AI 用「它」，"
                           f"指 Django 数据模型写「数据定义」或引用 models.py 里的类名）"))
        cr = [w for w in CROSS_ROUND if w in text]
        if cr:
            issues.append(("error", key,
                           f"{label} 含跨轮次承接表述 {'、'.join(cr)}（描述必须能独立阅读：不要写「上一轮」"
                           f"这类依赖其他轮次才懂的表述，直接陈述本轮的事实与证据）"))
        longs = sorted({m.group(0) for m in LONG_TOKEN_RE.finditer(text)}, key=len, reverse=True)
        if longs:
            worst = [t for t in longs if len(t) >= LONG_TOKEN_ERROR]
            msg = ("长英文串 " + "、".join(f"{t}({len(t)})" for t in longs[:6])
                   + ("…" if len(longs) > 6 else "")
                   + "（平台 B-5 公共长片段查重按连续字符比对，容易被判套模板打回；请尽量改写成中文）")
            issues.append(("error" if worst else "warn", key, f"{label} 含{msg}"))

    for key in AI_TEXT_HINT_FIELDS:
        text = str(fields.get(key) or "")
        if not text.strip():
            continue
        label = FIELD_CN.get(key, key)
        sym = [s for s in HUMANIZER_SYMBOLS if s in text]
        if sym:
            issues.append(("warn", key,
                           f"{label} 含疑似 AI 符号 {'、'.join(sym)}：若为人工原文则保持原样并在质检报告备注，"
                           f"若为 AI 起草（如追问/修复提示词）则须先经 humanizer-zh 处理"))
        psym = [s for s in PROJECT_SYMBOLS if s in text]
        if psym:
            issues.append(("warn", key,
                           f"{label} 含项目补充红线写法 {'、'.join(psym)}（形近破折号，易与 —— 混淆）："
                           f"若为人工原文则保持原样并在质检报告备注，AI 起草的须{PROJECT_SYMBOLS_FIX}"))
        cl = [w for w in BANNED_CLICHE if w in text]
        if cl:
            issues.append(("warn", key,
                           f"{label} 含 AI 套话词 {'、'.join(cl)}：人工原文保持原样（不改写），"
                           f"AI 起草的须替换（如「全链路」改「全流程」）"))


# ------------------------------------------------------------------ 主流程
def collect_tasks(records_root):
    """含 task-info.md 的目录 = 任务；否则下钻。"""
    out = []
    for entry in sorted(os.listdir(records_root)):
        if entry.startswith("."):
            continue
        p = os.path.join(records_root, entry)
        if not os.path.isdir(p):
            continue
        if os.path.exists(os.path.join(p, "task-info.md")):
            out.append((entry, p))
        else:
            out.extend(collect_tasks(p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", help="SESSION_NAME（默认取 secrets/config 的 active）")
    ap.add_argument("--task", help="只导出指定任务 ID")
    ap.add_argument("--out", help="JSON 输出路径")
    args = ap.parse_args()

    # ---- 第一步：先请求平台的表单定义接口，确认本地字段规范没过期 ----
    # GET https://solo2.jzxhnh.com/api/v1/submissions/form-schema
    schema_check = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from check_form_schema import check_schema
        schema_check = check_schema()
    except Exception as e:  # noqa: BLE001
        print(f"[提示] 表单规范预检跳过：{e}")
    if schema_check:
        if schema_check["ok"] is True:
            print(f"[表单规范] fingerprint={schema_check['local_fp']}，与平台一致 ✅")
        elif schema_check["ok"] is False:
            print(f"[警告] 平台表单已变：本地 {schema_check['local_fp']} / 平台 {schema_check['remote_fp']}")
            for d in schema_check["diffs"]:
                print(f"        - {d}")
            print("        处理：重跑 python scripts/cc-solo/extract_submit_fields.py 后重新生成本文件")
        else:
            print(f"[提示] 表单规范预检未完成：{schema_check['reason']}")

    spec = load_spec()
    cfg = load_settings()
    # 会话选择：命令行 > secrets > config；若前者目录不存在则回退到存在的那个，并提示
    candidates = [s for s in (args.session, cfg["session_secrets"], cfg["session_config"]) if s]
    session, tried = None, []
    for cand in candidates:
        root = os.path.join(WORKSPACE, cfg["work_root"], cand, cfg["records_dir"])
        tried.append((cand, os.path.isdir(root)))
        if os.path.isdir(root):
            session = cand
            break
    if session is None:
        print("[错误] 找不到任何可用的 records 目录，已尝试：")
        for cand, ok in tried:
            print(f"  - {cand}: {'存在' if ok else '不存在'}")
        sys.exit(2)
    if len(tried) > 1 and tried[0][0] != session:
        print(f"[提示] 已回退使用会话 {session}（secrets.toml 的 active_session="
              f"{cfg['session_secrets']!r}、config.toml 的 active={cfg['session_config']!r}）；"
              f"建议把两处对齐，避免后续步骤走错目录。")
    records_root = os.path.join(WORKSPACE, cfg["work_root"], session, cfg["records_dir"])
    if not os.path.isdir(records_root):
        print(f"[错误] records 目录不存在：{records_root}")
        sys.exit(2)

    tasks = collect_tasks(records_root)
    if args.task:
        tasks = [(t, p) for t, p in tasks if t == args.task]
        if not tasks:
            print(f"[错误] 未找到任务 {args.task}（在 {records_root} 下）")
            sys.exit(2)

    records, notes = [], []
    if schema_check and schema_check["ok"] is False:
        notes.append("平台表单规范已变（fingerprint 不一致），本文件可能已过期："
                     "请重跑 extract_submit_fields.py 后重新生成")
    for task_id, tdir in tasks:
        info = parse_blocks(read_utf8(os.path.join(tdir, "task-info.md")))
        shared = shared_values(info, cfg, spec)
        rfiles = sorted(f for f in os.listdir(tdir)
                        if re.match(rf"^{re.escape(task_id)}-R\d+\.md$", f))
        if not rfiles:
            notes.append(f"{task_id}: 只有 task-info.md，没有任何 {task_id}-R*.md，未产出数据")
        seen_turns, per_task_rounds = [], []
        for rf in rfiles:
            rn = int(re.search(r"R(\d+)\.md$", rf).group(1))
            blocks = parse_blocks(read_utf8(os.path.join(tdir, rf)))
            fields = dict(shared)
            fields.update(round_values(blocks, spec))
            fields["x_iteration"] = rn

            # 选填字段：产物 JSON 里也置空（与提交 body 保持一致；原文仍留在 records/ 的 R{NN}.md）
            for fld in spec["fields"]:
                if not fld["is_required"]:
                    fields[fld["field_key"]] = ""

            # 数值型字段按表单规范转成整数（分数/轮次排序），避免提交时被判成字符串
            for fld in spec["fields"]:
                if fld["field_type"] == "number":
                    iv = to_int(fields.get(fld["field_key"]))
                    if iv is not None:
                        fields[fld["field_key"]] = iv

            # 轨迹附件：优先整份轨迹（平台 trace_file 的 help_text 指向 ~/.codex/sessions/ 或
            # ~/.claude/projects/ 的原始会话文件，配 SessionID + TurnID 定位到某一轮）；
            # 整份缺失时才回退本轮切片（切片只用于打分阶段定位单轮）
            full_name = f"{task_id}-trajectory.jsonl"
            slice_name = f"{task_id}-R{rn:02d}-trajectory.jsonl"
            cand = os.path.join(tdir, full_name)
            if not os.path.exists(cand):
                cand = os.path.join(tdir, slice_name)
            trace_local = os.path.relpath(cand, WORKSPACE).replace("\\", "/")
            fields["trace_file"] = trace_local
            trace_exists = os.path.exists(cand)

            issues = []
            validate(fields, spec, {
                "round": rn, "trace_local": trace_local, "trace_exists": trace_exists,
            }, issues)
            seen_turns.append(fields.get("turn_id"))
            per_task_rounds.append((rn, fields))

            records.append({
                "record_key": f"{task_id}#R{rn:02d}",
                "task_id": task_id,
                "round": rn,
                "fields": fields,
                "trace_file_local": trace_local,
                "trace_file_uploaded": None,
                "ready": not any(lv == "error" for lv, _, _ in issues),
                "issues": [{"level": lv, "field": fk, "message": msg} for lv, fk, msg in issues],
            })

        if len(per_task_rounds) > cfg["max_rounds"]:
            notes.append(f"{task_id}: 共 {len(per_task_rounds)} 轮 > 上限 {cfg['max_rounds']}")
        sids = {f.get("session_id") for _, f in per_task_rounds}
        if len(sids) > 1:
            notes.append(f"{task_id}: SessionID 各轮不一致 {sids}")
        dup = [t for t in set(seen_turns) if t and seen_turns.count(t) > 1]
        if dup:
            notes.append(f"{task_id}: TurnID 重复 {dup}")

    records.sort(key=lambda r: (r["task_id"], r["round"]))
    date = datetime.date.today().strftime("%Y-%m-%d")
    base = os.path.join(WORKSPACE, cfg["deliverables_root"], session,
                        f"评价结果-{session}-{date}")
    out_json = args.out or base + ".json"
    os.makedirs(os.path.dirname(out_json), exist_ok=True)

    n_err = sum(1 for r in records if not r["ready"])
    payload = {
        "schema": "cc-solo-eval-result/v1",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "generator": "scripts/cc-solo/build_eval_result.py",
        "field_spec": os.path.relpath(FIELDS_PATH, WORKSPACE).replace("\\", "/"),
        "field_spec_fingerprint": spec.get("fingerprint"),
        "session": session,
        "field_order": spec["field_order"],
        "labels": {f["field_key"]: f["label"] for f in spec["fields"]},
        "required_fields": spec["required_fields"],
        # 选填字段在提交 body 里一律置空字符串（字段保留、内容不提交）
        "blank_optional_fields": [f["field_key"] for f in spec["fields"] if not f["is_required"]],
        "upload_api": spec.get("upload_api", {}),
        "submit_api": {
            "url": cfg["submission"].get("submit_url") or spec.get("submit_api", {}).get("url"),
            "note": "提交接口已就位；用 scripts/cc-solo/submit_eval_result.py（默认 dry-run，加 --commit 才发请求）"
                    "上传轨迹并提交本文件。body 保持 24 字段结构，选填字段一律置空字符串。",
        },
        "records": records,
        "summary": {
            "records": len(records),
            "ready": len(records) - n_err,
            "blocked": n_err,
            "tasks": len({r["task_id"] for r in records}),
            "warnings": sum(1 for r in records for i in r["issues"] if i["level"] == "warn"),
            "errors": sum(1 for r in records for i in r["issues"] if i["level"] == "error"),
            "by_task": {t: sum(1 for r in records if r["task_id"] == t) for t in sorted({r["task_id"] for r in records})},
        },
        "notes": notes,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 质检报告（Markdown）
    out_md = os.path.splitext(out_json)[0] + "-质检报告.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(f"# cc-solo 评价结果质检报告（{session}，{date}）\n\n")
        f.write(f"- 生成时间：{payload['generated_at']}\n")
        f.write(f"- 字段规范：`{payload['field_spec']}`（fingerprint `{payload['field_spec_fingerprint']}`）\n")
        f.write(f"- 数据条数：{payload['summary']['records']}（可直接提交 {payload['summary']['ready']}，"
                f"有 error 阻塞 {payload['summary']['blocked']}）\n")
        f.write(f"- 校验项：error {payload['summary']['errors']} / warn {payload['summary']['warnings']}\n\n")
        f.write("## 去 AI 化与提交范围（红线）\n\n")
        f.write("> 提交 body 里的**所有字段**在提交前须已过 `skills/humanizer-zh` 完整流程（28 条规则全查）；"
                "本脚本只做机械兜底：符号类记 error（阻塞提交），高频词类记 warn。\n\n")
        f.write("- **进入提交 body、须去 AI 化的 AI 起草字段**：五维描述（desc_delivery / desc_instruction / "
                "desc_planning / desc_reasoning / desc_execution）\n")
        f.write("- **只提示不阻塞**：other_issues（其他问题，选填、提交时置空字符串）、"
                "user_prompt（人工原文保持原样）、languages\n")
        f.write("- **选填字段一律置空字符串**：本规范里只有 other_issues（其他问题，`is_required=false`）——"
                "字段保留在 body 里，值提交为空串（产物 JSON 里同样置空）；内部字段备注（内部）、"
                "截图附件（内部）、以及本报告这份去 AI 化字段清单也不提交\n")
        f.write(f"- **长英文串（红线）**：评价里尽量写成中文，避免出现 ≥{LONG_TOKEN_MIN} 个连续英文字符的"
                f"命令/参数/标识符/路径（≥{LONG_TOKEN_ERROR} 记 error）。平台 B-5「公共长片段」查重按连续字符"
                f"比对，长英文串在别的提交里也常见，容易被判「套模板」打回。\n")
        f.write("- **跨轮次承接表述（红线，实测被返修）**：每条描述必须能**独立阅读**，不要写"
                "「上一轮」「前一轮」这类依赖其他轮次才懂的表述；直接陈述本轮的事实与证据"
                "（如「本轮未动用任务板，因此没有可追踪的状态链」）。\n\n")
        f.write("## 逐条结果\n\n")
        for r in records:
            flag = "✅ 可提交" if r["ready"] else "⛔ 有阻塞项"
            f.write(f"### {r['record_key']} — {flag}\n\n")
            f.write(f"- 任务类型：{r['fields'].get('question_type')}｜难度：{r['fields'].get('difficulty')}"
                    f"｜轮次排序：{r['fields'].get('x_iteration')}\n")
            f.write(f"- 轨迹文件：`{r['trace_file_local']}`\n")
            for i in r["issues"]:
                f.write(f"- [{'error' if i['level'] == 'error' else 'warn'}] {i['field']}：{i['message']}\n")
            if not r["issues"]:
                f.write("- 无问题\n")
            f.write("\n")
        if notes:
            f.write("## 任务级提示\n\n")
            for n in notes:
                f.write(f"- {n}\n")

    print("=" * 64)
    print(f"评价结果：{out_json}")
    print(f"质检报告：{out_md}")
    print(f"会话：{session}｜任务：{payload['summary']['tasks']}｜数据条数（一轮一条）：{payload['summary']['records']}")
    print(f"可提交：{payload['summary']['ready']}｜有阻塞项：{payload['summary']['blocked']}"
          f"｜error {payload['summary']['errors']} / warn {payload['summary']['warnings']}")
    for r in records:
        bad = [i for i in r["issues"] if i["level"] == "error"]
        if bad:
            print(f"  ⛔ {r['record_key']}：" + "；".join(i["message"] for i in bad))
    for n in notes:
        print(f"  · {n}")
    print("-" * 64)
    print("提示：轨迹文件（附件）需先上传拿远端 path；拿到提交 URL 后执行")
    print("      python scripts/cc-solo/submit_eval_result.py --result <上面的 json> --dry-run")
    print("=" * 64)


if __name__ == "__main__":
    main()
