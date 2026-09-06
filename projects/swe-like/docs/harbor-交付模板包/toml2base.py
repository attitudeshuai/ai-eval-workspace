#!/usr/bin/env python3
"""把一个 Harbor 交付包写成「底稿-Harbor 交付（试行）」多维表格的一行。

用法：
    python3 toml2base.py <交付包目录或 zip>            # 体检通过后写入
    python3 toml2base.py <交付包目录或 zip> --dry-run   # 只体检并打印将写入的内容

底稿一共 23 列。其中 18 列由本脚本从交付包里自动提取：15 列来自 task.toml，
「需求 Prompt（原文）」来自 instruction.md，「Verify Rubric」来自 tests/nl_rubric.yaml，
「交付包（zip）」上传整个 zip。剩下 5 列脚本一律不写：「提交人」是人员列，由提交人
自己在底稿里圈；Reviewer、静态内容是否通过质检、题目是否可运行、质检备注由质检填写。

写入前先做一次全量体检并逐列打印结果，任何一列不通过就整体中止，不会写半行进去。
单选列的合法值实时从底稿拉取，脚本里不写死，底稿改了选项脚本自动跟着变。

依赖：lark-cli（已 auth login）、PyYAML。TOML 解析用 tomllib(3.11+)，回退 tomli / toml。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile

BASE_TOKEN = "Fm6sbEnuFaAzO1sDarUcXJbonIe"
TABLE_ID = "tblmEz1ad46zqfH2"

TITLE_COLUMN = "题目名称"
PROMPT_COLUMN = "需求 Prompt（原文）"
RUBRIC_COLUMN = "Verify Rubric"
ZIP_COLUMN = "交付包（zip）"

# 质检填写，脚本一律不写
REVIEWER_COLUMNS = ["Reviewer", "静态内容是否通过质检", "题目是否可运行", "质检备注"]

# 本批次只收这两种语言
BATCH_LANGUAGES = ["Python", "Go"]

REQUIRED_FILES = [
    "task.toml",
    "instruction.md",
    "environment/Dockerfile",
    "tests/nl_rubric.yaml",
    "evidence/model.patch",
]

# 轨迹导出形态任选其一，不与 harness 取值绑定：TraeX 从 .trae/cli/sessions/ 导出
# jsonl，Trae IDE 导出会话记录 Markdown，mini-swe-agent 交它自己写出的轨迹。
TRAJECTORY_FILES = [
    "evidence/trajectory.jsonl",
    "evidence/trajectory.json",
    "evidence/trajectory.md",
]

# 只有这两个 harness 有 Trae 会话。miniswe 跑出来没有 session id，
# 这时 trae_session_id 允许留空，其余 harness 一律必填。
TRAE_HARNESSES = ("Trae", "TraeX")

# task.toml 键 -> (底稿列名, 校验类型)。顺序即体检报告里的顺序。
TOML_FIELDS = [
    ("title", TITLE_COLUMN, "title"),
    ("submitter", "提交人", "submitter"),
    ("submit_date", "提交日期", "date"),
    ("language", "主要语言", "language"),
    ("task_type", "任务类型", "select"),
    ("repo_url", "Repo URL", "url"),
    ("base_commit", "Commit/版本", "sha"),
    ("realism_and_difficulty", "真实性与难度说明", "text"),
    ("modules", "可能涉及模块", "text"),
    ("trae_session_id", "Trae Session ID", "session_id"),
    ("effective_turns", "有效轮数", "turns"),
    ("harness", "Harness", "select"),
    ("seed_model", "Seed 模型/版本", "text"),
    ("requirement_met", "是否完成需求", "select"),
    ("run_result", "产物结果", "run_result"),
    ("notes", "备注", "optional_text"),
]

ALLOWED_KEYS = [k for k, _, _ in TOML_FIELDS]

# 模板 instruction.md 里那段写作提示的开头。它不是 <……> 形式，通用规则抓不到，
# 所以单独留一个哨兵，用来发现整段注释没删就提交的情况。
# 其余占位一律由下面的 CJK_PLACEHOLDER 通用规则识别，不再逐条写死模板文案。
PLACEHOLDER_MARKERS = ["写题面时注意"]


class Fail(Exception):
    """体检之外的硬错误：环境、参数、网络。"""


def disp_width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, width):
    return s + " " * max(0, width - disp_width(s))


def load_toml(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    try:
        import tomllib

        return tomllib.loads(raw)
    except ImportError:
        pass
    try:
        import tomli

        return tomli.loads(raw)
    except ImportError:
        pass
    try:
        import toml

        return toml.loads(raw)
    except ImportError:
        raise Fail("环境里没有 TOML 解析库，请先执行：pip install tomli")


def lark(args, cwd=None):
    try:
        proc = subprocess.run(
            ["lark-cli"] + args, capture_output=True, text=True, cwd=cwd
        )
    except FileNotFoundError:
        raise Fail(
            "找不到 lark-cli 命令。本脚本要用它读底稿的选项、写记录、传附件，"
            "请先安装 lark-cli 并执行 lark-cli auth login 完成登录，再重跑。"
        )
    if proc.returncode != 0:
        raise Fail(
            "lark-cli 执行失败（退出码 %d）：lark-cli %s\n%s"
            % (proc.returncode, " ".join(args), (proc.stderr or proc.stdout).strip()[:800])
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise Fail("lark-cli 返回的不是 JSON：\n%s" % proc.stdout[:500])


def fetch_schema(base_token, table_id):
    """实时拉底稿字段结构；单选列取真实选项名，不在脚本里写死。"""
    out = lark(
        [
            "base",
            "+field-list",
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--as",
            "user",
            "--limit",
            "200",
        ]
    )
    schema = {}
    for f in out.get("data", {}).get("fields", []):
        schema[f["name"]] = {
            "id": f["id"],
            "type": f["type"],
            "options": [o["name"] for o in (f.get("options") or [])],
        }
    if not schema:
        raise Fail(
            "没拉到底稿字段结构，请检查 base-token / table-id / 表格权限：%s / %s"
            % (base_token, table_id)
        )
    return schema


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# 模板占位一律写成 <……>，尖括号内含中文就说明没填完。不逐字写死模板文案，
# 否则模板一改措辞检测就整个失效。真实需求里的 Map<String, int>、a < b、
# <T> 这类写法不含中文，不会被误伤。
CJK_PLACEHOLDER = re.compile(r"<[^<>\n]{0,60}[\u4e00-\u9fff][^<>\n]{0,60}>")


def placeholder_hits(value):
    """返回还没填的占位片段，空列表表示已填完。"""
    s = str(value)
    hits = [m.group(0) for m in CJK_PLACEHOLDER.finditer(s)]
    hits += [mk for mk in PLACEHOLDER_MARKERS if mk in s]
    out = []
    for h in hits:
        if h not in out:
            out.append(h)
    return out


def is_placeholder(value):
    return bool(placeholder_hits(value))


class Report(object):
    """逐列体检结果。"""

    def __init__(self):
        self.rows = []
        self.payload = {}

    def ok(self, column, source, note=""):
        self.rows.append([column, source, "OK", note])

    def fail(self, column, source, reason):
        self.rows.append([column, source, "FAIL", reason])

    def skip(self, column, source, note):
        self.rows.append([column, source, "SKIP", note])

    @property
    def failed(self):
        return [r for r in self.rows if r[2] == "FAIL"]

    def render(self):
        w0 = max([disp_width(r[0]) for r in self.rows] + [disp_width("列名")])
        w1 = max([disp_width(r[1]) for r in self.rows] + [disp_width("来源")])
        lines = ["%s  %s  %-4s  %s" % (pad("列名", w0), pad("来源", w1), "状态", "说明")]
        lines.append("-" * (w0 + w1 + 16))
        for column, source, status, note in self.rows:
            lines.append(
                "%s  %s  %-4s  %s" % (pad(column, w0), pad(source, w1), status, note)
            )
        return "\n".join(lines)


def resolve_input(path):
    """返回 (包根目录, 待上传的 zip 路径, 包顶层目录名, 临时目录)。"""
    path = os.path.abspath(path.rstrip(os.sep))
    if not os.path.exists(path):
        raise Fail("路径不存在：%s" % path)

    if os.path.isdir(path):
        name = os.path.basename(path)
        parent = os.path.dirname(path)
        archive = shutil.make_archive(
            os.path.join(tempfile.mkdtemp(), name), "zip", root_dir=parent, base_dir=name
        )
        return path, archive, name, None

    if not path.endswith(".zip"):
        raise Fail("只接受交付包目录或 .zip 文件，收到：%s" % path)

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(path) as zf:
        tops = set()
        for n in zf.namelist():
            head = n.split("/")[0]
            if head in ("__MACOSX", "__MACOSX/"):
                continue
            tops.add(head)
        tops.discard("")
        if len(tops) != 1:
            raise Fail(
                "zip 里必须只有一个顶层目录（即题目名称），当前有 %d 个：%s"
                % (len(tops), "、".join(sorted(tops)) or "（空）")
            )
        zf.extractall(tmp)
    name = tops.pop()
    return os.path.join(tmp, name), path, name, tmp


def check_structure(pkg_dir, report_errors):
    for rel in REQUIRED_FILES:
        p = os.path.join(pkg_dir, rel)
        if not os.path.isfile(p):
            report_errors.append("交付包缺少必需文件：%s" % rel)
        elif os.path.getsize(p) == 0:
            report_errors.append("%s 是空文件，需要补齐内容" % rel)

    # 有其一即可，只要有一个非空就算过。其余留着空占位文件不算错，
    # 否则用 Trae IDE 的人交了 trajectory.md、包里还留着模板自带的空
    # trajectory.jsonl，就会因为一个他本不需要提供的文件被拒。
    filled = [
        rel
        for rel in TRAJECTORY_FILES
        if os.path.isfile(os.path.join(pkg_dir, rel))
        and os.path.getsize(os.path.join(pkg_dir, rel)) > 0
    ]
    if not filled:
        report_errors.append(
            "交付包缺少运行轨迹：%s 有其一即可，且不能是空文件（TraeX 从 "
            ".trae/cli/sessions/ 导出 trajectory.jsonl，Trae IDE 导出会话记录 "
            "Markdown 存成 trajectory.md，miniswe 把 mini-swe-agent 写出的"
            "轨迹存成 trajectory.json）" % " 或 ".join(TRAJECTORY_FILES)
        )

    shots = os.path.join(pkg_dir, "evidence", "screenshots")
    if not os.path.isdir(shots):
        report_errors.append("交付包缺少 evidence/screenshots/ 目录，至少要放一张截图")
    else:
        imgs = [
            f
            for f in os.listdir(shots)
            if not f.startswith(".")
            and os.path.isfile(os.path.join(shots, f))
        ]
        if not imgs:
            report_errors.append("evidence/screenshots/ 是空的，至少要放一张运行截图")


def parse_rubric(path):
    """返回 (拍平文本, 按序 rubric id 列表, 错误列表)。"""
    try:
        import yaml
    except ImportError:
        raise Fail("环境里没有 YAML 解析库，请先执行：pip install pyyaml")

    try:
        doc = yaml.safe_load(read_text(path))
    except Exception as e:
        return None, [], ["tests/nl_rubric.yaml 不是合法 YAML：%s" % e]

    if not isinstance(doc, dict) or not isinstance(doc.get("rubrics"), list):
        return None, [], ["tests/nl_rubric.yaml 顶层必须是 rubrics 列表，参考模板重写"]

    items, errors = doc["rubrics"], []
    if len(items) < 5:
        errors.append(
            "tests/nl_rubric.yaml 至少 5 条 rubric，当前只有 %d 条" % len(items)
        )

    seen, types, parsed = set(), [], []
    for i, it in enumerate(items, 1):
        pos = "tests/nl_rubric.yaml 第 %d 条" % i
        if not isinstance(it, dict):
            errors.append("%s 不是一个 id/type/text 对象" % pos)
            continue
        missing = [k for k in ("id", "type", "text") if it.get(k) in (None, "")]
        if missing:
            errors.append("%s 缺少字段：%s（三个字段都必填）" % (pos, "、".join(missing)))
            continue
        rid, rtype, text = it["id"], str(it["type"]).strip().lower(), str(it["text"]).strip()
        if rtype not in ("f2p", "p2p"):
            errors.append('%s的 type 收到 "%s"，合法值为 f2p / p2p' % (pos, it["type"]))
            continue
        if rid in seen:
            errors.append("%s的 id「%s」与前面重复，id 必须唯一" % (pos, rid))
            continue
        if is_placeholder(text):
            errors.append("%s的 text 还是模板占位内容 %s，请替换成真实判分标准" % (pos, text))
            continue
        seen.add(rid)
        types.append(rtype)
        parsed.append((rid, rtype, text))

    if parsed and "f2p" not in types:
        errors.append(
            "tests/nl_rubric.yaml 至少要有 1 条 f2p（改动后才应该通过的行为），当前全是 p2p"
        )

    if errors:
        return None, [], errors

    def sort_key(item):
        rid = item[0]
        return (0, int(rid), "") if str(rid).isdigit() else (1, 0, str(rid))

    ordered = sorted(parsed, key=sort_key)
    lines = ["[%s] %s: %s" % (t, rid, text) for rid, t, text in ordered]
    return "\n".join(lines), [str(rid) for rid, _, _ in ordered], []


VERDICTS = ("通过", "未通过")


def parse_run_result(raw, rubric_ids, requirement_met):
    """产物结果必须逐条对应 rubric，不能写成一段散文。

    每行 `<rubric id> <通过|未通过> [说明]`，未通过必须给原因。
    返回 (按 rubric 顺序归一化的文本, 错误列表)。
    """
    if not rubric_ids:
        return None, ["tests/nl_rubric.yaml 没解析出 rubric，无法核对产物结果"]

    lines_in = [l.strip() for l in str(raw).splitlines() if l.strip()]
    # 整段散文是最常见的错法（旧规范就是这么要求的），单独给一条明确提示，
    # 否则会把一大截正文当成 rubric id 回显出来
    if lines_in and not any(
        l.split(None, 1)[0].rstrip("：:.、") in rubric_ids for l in lines_in
    ):
        return None, [
            "产物结果要逐条给出 rubric 结论，不能写成整段说明。每行格式 "
            "`<rubric id> <通过|未通过> [说明]`，%d 条 rubric（id：%s）各一行，"
            "未通过的必须写失败原因"
            % (len(rubric_ids), "、".join(rubric_ids))
        ]

    seen, handled, errors = {}, set(), []
    for lineno, line in enumerate(lines_in, 1):
        parts = line.split(None, 2)
        rid = parts[0].rstrip("：:.、")
        verdict = parts[1].strip() if len(parts) > 1 else ""
        reason = parts[2].strip() if len(parts) > 2 else ""
        pos = "产物结果第 %d 行" % lineno

        if rid not in rubric_ids:
            errors.append(
                '%s的 rubric id「%s」在 tests/nl_rubric.yaml 里不存在，'
                "合法 id 为 %s" % (pos, rid, " / ".join(rubric_ids))
            )
            continue
        if rid in handled:
            errors.append("%s的 rubric id「%s」重复了，每条 rubric 只写一行" % (pos, rid))
            continue
        # 这一行已经认领了该 rubric，后面就别再报「漏了这条」
        handled.add(rid)
        if verdict not in VERDICTS:
            errors.append(
                '%s收到「%s」，每行格式为 `<rubric id> <通过|未通过> [说明]`'
                % (pos, line[:40])
            )
            continue
        if verdict == "未通过" and not reason:
            errors.append("%s判为未通过，必须在同一行补上失败原因" % pos)
            continue
        seen[rid] = (verdict, reason)

    missing = [rid for rid in rubric_ids if rid not in handled]
    if missing:
        errors.append(
            "产物结果漏了 rubric %s 的结论，%d 条 rubric 每条都要有一行"
            % ("、".join(missing), len(rubric_ids))
        )

    if errors:
        return None, errors

    failed = [rid for rid in rubric_ids if seen[rid][0] == "未通过"]
    # 和「是否完成需求」交叉核对，避免两列自相矛盾
    if requirement_met == "完成" and failed:
        errors.append(
            "产物结果里 rubric %s 未通过，但 requirement_met 填的是「完成」，两者矛盾"
            % "、".join(failed)
        )
    elif requirement_met and requirement_met != "完成" and not failed:
        errors.append(
            'requirement_met 填的是「%s」，但产物结果里 %d 条 rubric 全部通过，'
            "两者矛盾" % (requirement_met, len(rubric_ids))
        )
    if errors:
        return None, errors

    lines = [
        " ".join(x for x in (rid, seen[rid][0], seen[rid][1]) if x) for rid in rubric_ids
    ]
    return "\n".join(lines), []


def extract(pkg_dir, pkg_name, zip_path, schema):
    report = Report()
    structural = []

    check_structure(pkg_dir, structural)

    toml_path = os.path.join(pkg_dir, "task.toml")
    if not os.path.isfile(toml_path):
        raise Fail("交付包里没有 task.toml：%s" % toml_path)
    data = load_toml(toml_path)

    rub_path = os.path.join(pkg_dir, "tests", "nl_rubric.yaml")
    if os.path.isfile(rub_path):
        rub_flat, rubric_ids, rub_errors = parse_rubric(rub_path)
    else:
        rub_flat, rubric_ids, rub_errors = None, [], ["交付包缺少 tests/nl_rubric.yaml"]

    lowered = {k.lower(): k for k in ALLOWED_KEYS}
    for key in data:
        if key in ALLOWED_KEYS:
            continue
        # 大小写写错是最常见的手误（例如照抄早期草稿写成 Harness），单独给出改法
        if key.lower() in lowered:
            structural.append(
                "task.toml 的键 %s 大小写不对，应写作 %s（键名全部小写）"
                % (key, lowered[key.lower()])
            )
        else:
            structural.append(
                "task.toml 出现规范外的键：%s。键名固定 16 个，请勿增删或改名（合法键：%s）"
                % (key, "、".join(ALLOWED_KEYS))
            )

    # trae_session_id 是否必填取决于 harness，所以先把它取出来。这里不校验取值是否
    # 合法，那由下面 harness 那一列自己负责；harness 没填时 session id 仍按必填处理。
    harness = str(data.get("harness") or "").strip()

    for key, column, kind in TOML_FIELDS:
        source = "task.toml:%s" % key
        # submitter 不写底稿，所以底稿有没有这一列都不该拦住提交
        if kind != "submitter" and column not in schema:
            report.fail(column, source, "底稿里没有这一列，脚本与表结构不同步，请联系维护人")
            continue

        raw = data.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            if kind == "optional_text":
                report.ok(column, source, "留空（本键可选）")
            elif kind == "session_id" and harness and harness not in TRAE_HARNESSES:
                report.ok(column, source, "留空（harness=%s，没有 Trae 会话）" % harness)
            else:
                report.fail(column, source, "task.toml 缺少 %s 或值为空" % key)
            continue

        value = raw.strip() if isinstance(raw, str) else raw

        if kind == "run_result":
            text, errs = parse_run_result(
                value, rubric_ids, str(data.get("requirement_met") or "").strip()
            )
            if errs:
                report.fail(column, source, "；".join(errs))
            else:
                report.payload[column] = text
                report.ok(column, source, "逐条对齐 %d 条 rubric" % len(rubric_ids))
            continue

        if isinstance(value, str) and is_placeholder(value):
            report.fail(
                column,
                source,
                "%s 还是模板里的占位内容 %s，请替换成真实内容" % (key, value),
            )
            continue

        if kind == "submitter":
            # 底稿「提交人」是人员列，只接受 open_id。同名的人可能有几十个，
            # 脚本没法从姓名唯一定位到人，圈错人比不圈更糟，所以这里只校验
            # task.toml 里填了，底稿那一列留给提交人自己圈。
            report.ok(column, source, "不回填底稿，请自行在底稿「提交人」列圈人")

        elif kind == "title":
            if value != pkg_name:
                report.fail(
                    column,
                    source,
                    'title 收到 "%s"，但交付包目录名是 "%s"，两者必须一致' % (value, pkg_name),
                )
                continue
            report.payload[column] = value
            report.ok(column, source)

        elif kind in ("select", "language"):
            options = schema[column]["options"]
            if value not in options:
                report.fail(
                    column,
                    source,
                    '收到 "%s"，合法值为 %s' % (value, " / ".join(options) or "（该列还没配置选项）"),
                )
                continue
            if kind == "language" and value not in BATCH_LANGUAGES:
                report.fail(
                    column,
                    source,
                    '收到 "%s"，本批次只收 %s' % (value, " / ".join(BATCH_LANGUAGES)),
                )
                continue
            report.payload[column] = value
            report.ok(column, source)

        elif kind == "date":
            s = str(value).strip().replace("/", "-").replace("T", " ")
            if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", s):
                y, m, d = s.split("-")
                s = "%s-%02d-%02d 00:00:00" % (y, int(m), int(d))
            m = re.fullmatch(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})(:\d{2})?", s)
            if m:
                s = "%s %s%s" % (m.group(1), m.group(2), m.group(3) or ":00")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", s):
                report.fail(
                    column,
                    source,
                    '收到 "%s"，格式应为 YYYY-MM-DD（例如 2026-09-03）' % value,
                )
                continue
            report.payload[column] = s
            report.ok(column, source, s)

        elif kind == "turns":
            try:
                n = int(str(value).strip())
            except (TypeError, ValueError):
                report.fail(column, source, '收到 "%s"，应为整数（例如 6）' % value)
                continue
            if n < 1:
                report.fail(column, source, "收到 %d，有效轮数至少为 1" % n)
                continue
            report.payload[column] = n
            report.ok(column, source)

        elif kind == "url":
            if not re.match(r"^https?://\S+$", str(value)):
                report.fail(
                    column,
                    source,
                    '收到 "%s"，应为 http(s) 开头的仓库地址' % value,
                )
                continue
            report.payload[column] = str(value)
            report.ok(column, source)

        elif kind == "sha":
            if not re.fullmatch(r"[0-9a-f]{40}", str(value)):
                report.fail(
                    column,
                    source,
                    '收到 "%s"，应为 40 位小写完整 commit SHA（不接受短 SHA、分支名或 tag）' % value,
                )
                continue
            dockerfile = os.path.join(pkg_dir, "environment", "Dockerfile")
            if not os.path.isfile(dockerfile):
                report.fail(column, source, "缺少 environment/Dockerfile，无法核对 ARG BASE_SHA")
                continue
            m = re.search(r"ARG\s+BASE_SHA\s*=\s*([0-9a-fA-F]{7,40})", read_text(dockerfile))
            if not m:
                report.fail(
                    column,
                    source,
                    "environment/Dockerfile 里没找到 ARG BASE_SHA=<40 位 SHA>，时间旅行段请照抄模板",
                )
                continue
            if m.group(1).lower() != str(value).lower():
                report.fail(
                    column,
                    source,
                    "task.toml 的 base_commit（%s）与 environment/Dockerfile 的 "
                    "ARG BASE_SHA（%s）不一致，两处必须是同一个 commit"
                    % (value, m.group(1)),
                )
                continue
            report.payload[column] = str(value)
            report.ok(column, source, "已与 Dockerfile 的 ARG BASE_SHA 核对一致")

        else:
            report.payload[column] = str(value).strip()
            report.ok(column, source)

    # instruction.md -> 需求 Prompt（原文）
    inst = os.path.join(pkg_dir, "instruction.md")
    if not os.path.isfile(inst):
        report.fail(PROMPT_COLUMN, "instruction.md", "交付包缺少 instruction.md")
    else:
        text = read_text(inst).strip()
        hits = placeholder_hits(text)
        if not text:
            report.fail(PROMPT_COLUMN, "instruction.md", "instruction.md 是空的")
        elif hits:
            report.fail(
                PROMPT_COLUMN,
                "instruction.md",
                "instruction.md 里还留着模板占位内容：%s，请替换成真实需求后再提交"
                % "、".join('"%s"' % h for h in hits),
            )
        else:
            report.payload[PROMPT_COLUMN] = text
            report.ok(PROMPT_COLUMN, "instruction.md", "全文原样回填，共 %d 字" % len(text))

    # tests/nl_rubric.yaml -> Verify Rubric
    rub = os.path.join(pkg_dir, "tests", "nl_rubric.yaml")
    if not os.path.isfile(rub):
        report.fail(RUBRIC_COLUMN, "tests/nl_rubric.yaml", "交付包缺少 tests/nl_rubric.yaml")
    else:
        if rub_errors:
            report.fail(RUBRIC_COLUMN, "tests/nl_rubric.yaml", "；".join(rub_errors))
        else:
            report.payload[RUBRIC_COLUMN] = rub_flat
            report.ok(
                RUBRIC_COLUMN,
                "tests/nl_rubric.yaml",
                "拍平 %d 条" % len(rub_flat.splitlines()),
            )

    # 整包 zip -> 交付包（zip）
    if ZIP_COLUMN not in schema:
        report.fail(ZIP_COLUMN, os.path.basename(zip_path), "底稿里没有这一列，脚本与表结构不同步")
    else:
        size = os.path.getsize(zip_path) / 1024.0 / 1024.0
        report.ok(ZIP_COLUMN, os.path.basename(zip_path), "写入记录后上传，%.2f MB" % size)

    for column in REVIEWER_COLUMNS:
        report.skip(column, "reviewer-填写", "质检填写，脚本不写")

    return report, structural


def find_existing(base_token, table_id, title):
    """按题目名称找已有记录，让同一个包重跑是更新而不是新增。"""
    offset, limit = 0, 200
    while True:
        out = lark(
            [
                "base",
                "+record-list",
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--as",
                "user",
                "--field-id",
                TITLE_COLUMN,
                "--format",
                "json",
                "--limit",
                str(limit),
                "--offset",
                str(offset),
            ]
        )
        d = out.get("data", {})
        ids = d.get("record_id_list") or []
        rows = d.get("data") or []
        for rid, row in zip(ids, rows):
            cell = row[0] if isinstance(row, list) and row else row
            if isinstance(cell, list):
                cell = cell[0] if cell else None
            if isinstance(cell, dict):
                cell = cell.get("text")
            if cell and str(cell).strip() == title:
                return rid
        if not d.get("has_more") or not ids:
            return None
        offset += len(ids)


def main():
    ap = argparse.ArgumentParser(
        description="把 Harbor 交付包写成「底稿-Harbor 交付（试行）」的一行"
    )
    ap.add_argument("package", help="交付包目录或 .zip")
    ap.add_argument("--base-token", default=BASE_TOKEN)
    ap.add_argument("--table-id", default=TABLE_ID)
    ap.add_argument("--dry-run", action="store_true", help="只体检并打印将写入的内容，不写表")
    args = ap.parse_args()

    pkg_dir, zip_path, pkg_name, _tmp = resolve_input(args.package)
    schema = fetch_schema(args.base_token, args.table_id)
    report, structural = extract(pkg_dir, pkg_name, zip_path, schema)

    print("交付包体检：%s" % pkg_name)
    print(report.render())

    if structural:
        print("\n交付包结构问题：")
        for s in structural:
            print("  - %s" % s)

    if report.failed or structural:
        sys.stdout.flush()
        print(
            "\n体检不通过：%d 列未通过、%d 个结构问题。修好后重跑，未写入任何内容。"
            % (len(report.failed), len(structural)),
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        "\n体检通过，将写入 %d 列 + 交付包 zip（「提交人」请自己在底稿里圈，"
        "另 %d 列留给质检）。" % (len(report.payload), len(REVIEWER_COLUMNS))
    )
    print(json.dumps(report.payload, ensure_ascii=False, indent=2))

    if args.dry_run:
        print("\n--dry-run：未写入底稿。")
        return

    existing = find_existing(args.base_token, args.table_id, pkg_name)
    cmd = [
        "base",
        "+record-upsert",
        "--base-token",
        args.base_token,
        "--table-id",
        args.table_id,
        "--as",
        "user",
        "--json",
        json.dumps(report.payload, ensure_ascii=False),
    ]
    if existing:
        cmd += ["--record-id", existing]
    out = lark(cmd)

    record = out.get("data", {}).get("record") or {}
    record_id = record.get("record_id") or record.get("id")
    if not record_id:
        ids = record.get("record_id_list") or out.get("data", {}).get("record_id_list") or []
        record_id = ids[0] if ids else existing
    if not record_id:
        raise Fail(
            "写入返回里没有 record_id，请人工核对底稿：%s"
            % json.dumps(out, ensure_ascii=False)[:400]
        )
    print("%s记录 %s" % ("已更新" if existing else "已新建", record_id))

    ignored = out.get("data", {}).get("ignored_fields")
    if ignored:
        print("注意：以下列被表格忽略（只读列）：%s" % json.dumps(ignored, ensure_ascii=False))

    if existing:
        old = lark(
            [
                "base",
                "+record-get",
                "--base-token",
                args.base_token,
                "--table-id",
                args.table_id,
                "--as",
                "user",
                "--record-id",
                record_id,
                "--field-id",
                schema[ZIP_COLUMN]["id"],
                "--format",
                "json",
            ]
        )
        tokens = []
        for row in old.get("data", {}).get("data") or []:
            for cell in row if isinstance(row, list) else []:
                for att in cell if isinstance(cell, list) else []:
                    if isinstance(att, dict) and att.get("file_token"):
                        tokens.append(att["file_token"])
        if tokens:
            remove = [
                "base",
                "+record-remove-attachment",
                "--base-token",
                args.base_token,
                "--table-id",
                args.table_id,
                "--as",
                "user",
                "--record-id",
                record_id,
                "--field-id",
                schema[ZIP_COLUMN]["id"],
                "--yes",
            ]
            for t in tokens:
                remove += ["--file-token", t]
            lark(remove)
            print("已清掉旧的交付包附件 %d 个" % len(tokens))

    # lark-cli 只接受当前目录下的相对路径，所以切到 zip 所在目录再传文件名
    lark(
        [
            "base",
            "+record-upload-attachment",
            "--base-token",
            args.base_token,
            "--table-id",
            args.table_id,
            "--as",
            "user",
            "--record-id",
            record_id,
            "--field-id",
            schema[ZIP_COLUMN]["id"],
            "--file",
            "./" + os.path.basename(zip_path),
        ],
        cwd=os.path.dirname(os.path.abspath(zip_path)),
    )
    print("交付包已上传到「%s」列：%s" % (ZIP_COLUMN, os.path.basename(zip_path)))


if __name__ == "__main__":
    try:
        main()
    except Fail as e:
        print("错误：%s" % e, file=sys.stderr)
        sys.exit(1)
