#!/usr/bin/env python3
"""
SWE-like 交付包离线体检（swe-like 专用）。

实现 docs/SWE-like Repo-v3.md 第 7 节「退回红线」中可离线校验的部分，
作为 toml2base.py --dry-run 的前置自查（toml2base.py 本身在底稿附件中，不在本仓库）。

用法：
    python3 preflight_check.py [--stage create|delivery] <题目目录> [<题目目录>...]

阶段：
    create    出题完成、待运行：不检查 evidence/ 与运行字段
    delivery  交付前（默认）：全量检查（含 evidence/、run_result 与 requirement_met 一致性）

依赖：Python 3.11+（tomllib）+ pyyaml
"""

import re
import sys
import tomllib
from pathlib import Path

import yaml

TASK_TOML_KEYS = {
    "title", "submitter", "submit_date", "language", "task_type", "repo_url",
    "base_commit", "realism_and_difficulty", "modules", "trae_session_id",
    "effective_turns", "harness", "seed_model", "requirement_met",
    "run_result", "notes",
}
LANGUAGES = {"Python", "Go"}
TASK_TYPES = {"功能新增", "Bug 修复", "测试增强", "重构/性能", "配置/工具链", "其他"}
HARNESSES = {"Trae", "TraeX", "miniswe"}
REQUIREMENT_MET = {"完成", "部分完成", "未完成", "无法判断"}
PLACEHOLDER_RE = re.compile(r"<[^<>\n]{1,40}>")


class Checker:
    def __init__(self, task_dir: Path, stage: str):
        self.dir = task_dir
        self.stage = stage
        self.failures = []

    def fail(self, msg):
        self.failures.append(msg)

    def check_file(self, rel, must_be_nonempty=True):
        p = self.dir / rel
        if not p.exists():
            self.fail(f"必需文件缺失：{rel}")
            return None
        if must_be_nonempty and (p.is_dir() or p.stat().st_size == 0):
            self.fail(f"必需文件为空：{rel}")
            return None
        return p

    def run(self):
        # ---- task.toml ----
        toml_path = self.check_file("task.toml")
        data = {}
        if toml_path:
            try:
                data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as e:
                self.fail(f"task.toml 解析失败：{e}")
                data = None
        rubrics = []
        if data is not None:
            rubrics = self.check_task_toml(data)
        # ---- instruction.md / Dockerfile / rubric ----
        ins = self.check_file("instruction.md")
        if ins:
            text = ins.read_text(encoding="utf-8")
            m = PLACEHOLDER_RE.search(text)
            if m:
                self.fail(f"instruction.md 残留 <……> 占位：{m.group(0)}")
        self.check_file("environment/Dockerfile")
        if data is not None:
            self.check_dockerfile(data)
        rubric_path = self.check_file("tests/nl_rubric.yaml")
        if rubric_path:
            rubrics = self.check_rubric(rubric_path)
        # ---- run_result 与 requirement_met（delivery 阶段）----
        if data is not None and rubrics and self.stage == "delivery":
            self.check_run_result(data, rubrics)
        # ---- evidence（delivery 阶段）----
        if self.stage == "delivery":
            self.check_file("evidence/model.patch")
            traj = [self.dir / "evidence" / n for n in
                    ("trajectory.jsonl", "trajectory.json", "trajectory.md")]
            if not any(p.exists() and p.stat().st_size > 0 for p in traj):
                self.fail("evidence/trajectory.jsonl、trajectory.json 与 trajectory.md 全都不存在或全为空")
            shots = self.dir / "evidence" / "screenshots"
            if not shots.is_dir() or not any(shots.iterdir()):
                self.fail("evidence/screenshots/ 为空")
        return self.failures

    def check_task_toml(self, d):
        keys = set(d.keys())
        if keys != TASK_TOML_KEYS:
            extra = keys - TASK_TOML_KEYS
            missing = TASK_TOML_KEYS - keys
            if extra:
                self.fail(f"task.toml 含规范外的键：{sorted(extra)}")
            if missing:
                self.fail(f"task.toml 缺少键：{sorted(missing)}")
        if d.get("title") != self.dir.name:
            self.fail(f"title（{d.get('title')!r}）与交付包目录名（{self.dir.name!r}）不一致")
        if d.get("language") not in LANGUAGES:
            self.fail(f"language 非法：{d.get('language')!r}（仅 {sorted(LANGUAGES)}）")
        if d.get("task_type") not in TASK_TYPES:
            self.fail(f"task_type 非法：{d.get('task_type')!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d.get("submit_date", ""))):
            self.fail(f"submit_date 非法：{d.get('submit_date')!r}（须 YYYY-MM-DD）")
        if not re.fullmatch(r"[0-9a-f]{40}", str(d.get("base_commit", ""))):
            self.fail(f"base_commit 须为 40 位完整 SHA：{d.get('base_commit')!r}")
        if d.get("harness") not in HARNESSES:
            self.fail(f"harness 非法：{d.get('harness')!r}")
        if d.get("requirement_met") not in REQUIREMENT_MET:
            self.fail(f"requirement_met 非法：{d.get('requirement_met')!r}")
        if not isinstance(d.get("effective_turns"), int) or d.get("effective_turns", -1) < 0:
            self.fail(f"effective_turns 须为非负整数：{d.get('effective_turns')!r}")
        if self.stage == "delivery":
            if d.get("harness") in {"Trae", "TraeX"} and not str(d.get("trae_session_id", "")).strip():
                self.fail("harness 填 Trae/TraeX 却没填 trae_session_id")
            if not d.get("effective_turns"):
                self.fail("effective_turns 为 0（delivery 阶段须为实际轮数）")
            if not str(d.get("realism_and_difficulty", "")).strip():
                self.fail("realism_and_difficulty 为空")
            if not str(d.get("modules", "")).strip():
                self.fail("modules 为空")
        return []

    def check_dockerfile(self, d):
        p = self.dir / "environment" / "Dockerfile"
        if not p.exists():
            return
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^\s*ARG\s+BASE_SHA=(\S*)", text, re.M)
        if not m or not m.group(1):
            self.fail("environment/Dockerfile 缺少 ARG BASE_SHA")
        elif m.group(1) != d.get("base_commit"):
            self.fail(f"base_commit 与 Dockerfile 的 ARG BASE_SHA 不一致：{m.group(1)!r}")

    def check_rubric(self, path):
        try:
            rubrics = yaml.safe_load(path.read_text(encoding="utf-8"))["rubrics"]
        except Exception as e:
            self.fail(f"tests/nl_rubric.yaml 解析失败：{e}")
            return []
        if not isinstance(rubrics, list) or len(rubrics) < 5:
            self.fail(f"rubric 少于 5 条（当前 {len(rubrics) if isinstance(rubrics, list) else 0} 条）")
            return rubrics if isinstance(rubrics, list) else []
        ids = [r.get("id") for r in rubrics]
        if len(ids) != len(set(ids)):
            self.fail(f"rubric id 重复：{ids}")
        types = [r.get("type") for r in rubrics]
        bad = [t for t in types if t not in ("f2p", "p2p")]
        if bad:
            self.fail(f"rubric type 非法（仅 f2p/p2p）：{bad}")
        if "f2p" not in types:
            self.fail("rubric 无 f2p 条目")
        if "p2p" not in types:
            self.fail("rubric 无 p2p 条目")
        for r in rubrics:
            text = str(r.get("text", ""))
            if not text.strip():
                self.fail(f"rubric id={r.get('id')} 的 text 为空")
            else:
                m = PLACEHOLDER_RE.search(text)
                if m:
                    self.fail(f"rubric id={r.get('id')} 残留 <……> 占位：{m.group(0)}")
        return rubrics

    def check_run_result(self, d, rubrics):
        run_result = str(d.get("run_result", ""))
        lines = [l.strip() for l in run_result.strip().splitlines() if l.strip()]
        seen = {}
        for line in lines:
            m = re.match(r"^(\d+)\s+(通过|未通过)\b\s*(.*)$", line)
            if not m:
                self.fail(f"run_result 行格式非法（应为「id 通过/未通过 [原因]」）：{line!r}")
                continue
            rid, verdict, reason = int(m.group(1)), m.group(2), m.group(3).strip()
            seen[rid] = (verdict, reason)
            if verdict == "未通过" and not reason:
                self.fail(f"run_result rubric id={rid} 未通过但未给原因")
        expect_ids = {r.get("id") for r in rubrics}
        if set(seen) != expect_ids:
            self.fail(f"run_result 未逐条对应 rubric：期望 id {sorted(expect_ids)}，实际 {sorted(seen)}")
        met = d.get("requirement_met")
        verdicts = [v[0] for _, v in sorted(seen.items()) if _ in expect_ids] if seen else []
        if seen and len(verdicts) == len(expect_ids):
            all_pass = all(v == "通过" for v in verdicts)
            if met == "完成" and not all_pass:
                self.fail("矛盾：requirement_met=完成，但 run_result 存在未通过条目")
            if met in {"未完成", "无法判断"} and all_pass:
                self.fail(f"矛盾：run_result 全部通过，但 requirement_met={met}")
            if met == "部分完成" and all_pass:
                self.fail("矛盾：run_result 全部通过，但 requirement_met=部分完成")


def main():
    args = sys.argv[1:]
    stage = "delivery"
    if "--stage" in args:
        i = args.index("--stage")
        stage = args[i + 1]
        del args[i:i + 2]
    if stage not in ("create", "delivery") or not args:
        print(__doc__)
        sys.exit(2)
    rc = 0
    for arg in args:
        d = Path(arg)
        if not d.is_dir():
            print(f"[FAIL] {arg}：目录不存在")
            rc = 1
            continue
        failures = Checker(d, stage).run()
        if failures:
            rc = 1
            print(f"[FAIL] {d.name}（stage={stage}）")
            for f in failures:
                print(f"  - {f}")
        else:
            print(f"[PASS] {d.name}（stage={stage}）")
    sys.exit(rc)


if __name__ == "__main__":
    main()
