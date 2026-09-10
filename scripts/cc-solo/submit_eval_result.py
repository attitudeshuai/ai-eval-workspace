#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 评价结果提交（轨迹上传 + 提交接口）
==========================================
读取 build_eval_result.py 产出的评价结果 JSON，按「一轮 = 一条记录」提交：

 1. 轨迹文件是**附件**：先上传拿远端 path（multipart/form-data，表单字段 file）
 2. 再提交到 https://solo2.jzxhnh.com/api/v1/submissions，请求体：

    {
      "data": { question_type, difficulty, …, score_execution, desc_*, other_issues, x_iteration,
                "trace_file": [{"name": "…-trajectory.jsonl", "path": "uploads/<id>.jsonl", "size": 321940}] },
      "schema_fingerprint": "cc4da53236368ac2"
    }

    响应：{"id":1196,"status":"SUBMITTED","status_label":"已提交","round_no":1,
           "schema_stale":false,"message":"提交成功，正在自动质检，稍后可在列表查看结论"}

用法：
    # 看一眼会提交什么（默认 dry-run，不联网）
    python scripts/cc-solo/submit_eval_result.py --result <评价结果.json>
    python scripts/cc-solo/submit_eval_result.py --result <json> --show-payload    # 打印完整请求体

    # 只上传轨迹并回填远端 path（不提交）
    python scripts/cc-solo/submit_eval_result.py --result <json> --upload-only --commit --write-back

    # 正式提交
    python scripts/cc-solo/submit_eval_result.py --result <json> --commit
    python scripts/cc-solo/submit_eval_result.py --result <json> --record app-001-codegen-01#R01 --commit

配置（projects/cc-solo/secrets.toml，gitignore）：
    [submission]
    submit_url = "https://solo2.jzxhnh.com/api/v1/submissions"   # 缺省取 config.toml [submission]
    cookie = "solo_qa_session=...; solo_qa_csrf=..."             # 也可写 token = "..."（二者等价）
    csrf_header = ""                                             # 若接口要求 X-CSRF-Token
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "cc-solo")
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.toml")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.toml")

try:
    import tomllib
except ImportError:
    tomllib = None


def load_toml(path):
    if not tomllib or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_settings():
    cfg = load_toml(CONFIG_PATH).get("submission", {})
    sec = load_toml(SECRETS_PATH).get("submission", {})
    return cfg, sec


# ---------------------------------------------------------------- 网络
def post_multipart(url, cookie, file_path, form_field="file", timeout=180):
    """上传文件：multipart/form-data，返回解析后的 JSON（形如 {"name":…,"path":…,"size":…}）。"""
    boundary = "----ccsolo" + uuid.uuid4().hex
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        content = f.read()
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="{form_field}"; filename="{filename}"\r\n'.encode(),
        b"Content-Type: application/octet-stream\r\n\r\n",
        content,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    if cookie:
        req.add_header("Cookie", cookie)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(url, cookie, payload, csrf_header=None, timeout=120):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if cookie:
        req.add_header("Cookie", cookie)
    if csrf_header:
        req.add_header("X-CSRF-Token", csrf_header)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def build_payload(record, field_order, fingerprint):
    """一条记录 → 提交请求体：{"data": {24 字段}, "schema_fingerprint": …}。

    trace_file 为附件数组 [{name,path,size}]，由上传步骤回填；未上传时为空数组。
    """
    data = {k: record["fields"].get(k, "") for k in field_order}
    tf = record["fields"].get("trace_file")
    data["trace_file"] = tf if isinstance(tf, list) else []
    return {"data": data, "schema_fingerprint": fingerprint}


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True, help="评价结果 JSON（build_eval_result.py 产物）")
    ap.add_argument("--url", help="提交接口 URL（覆盖 config/secrets 的 submit_url）")
    ap.add_argument("--cookie", help="整条凭据串（覆盖 secrets.toml [submission].cookie）")
    ap.add_argument("--record", action="append", help="只处理指定 record_key（可多次），如 app-001-codegen-01#R01")
    ap.add_argument("--only-ready", action="store_true", help="只提交 ready=true 的记录（跳过有 error 的）")
    ap.add_argument("--upload-only", action="store_true", help="只上传轨迹、回填附件信息，不提交")
    ap.add_argument("--commit", action="store_true", help="真的发请求；不加则只打印计划（dry-run）")
    ap.add_argument("--show-payload", action="store_true", help="打印完整请求体（含 desc 全文）")
    ap.add_argument("--write-back", action="store_true", help="把上传结果/接口返回回写到结果 JSON")
    args = ap.parse_args()

    with open(args.result, encoding="utf-8") as f:
        data = json.load(f)

    cfg_sec, sec = load_settings()
    cookie = args.cookie or sec.get("cookie") or sec.get("token") or ""
    csrf_header = sec.get("csrf_header") or ""
    upload_api = data.get("upload_api", {}) or {}
    upload_url = sec.get("upload_url") or cfg_sec.get("upload_url") or upload_api.get("url")
    form_field = cfg_sec.get("upload_form_field") or upload_api.get("form_field", "file")
    path_key = cfg_sec.get("upload_response_path_key") or upload_api.get("response_path_key", "path")
    submit_url = args.url or sec.get("submit_url") or cfg_sec.get("submit_url") or (data.get("submit_api") or {}).get("url")
    fingerprint = data.get("field_spec_fingerprint") or (data.get("submit_api") or {}).get("schema_fingerprint")
    max_mb = float(cfg_sec.get("attachment_max_mb") or 20)

    records = data.get("records", [])
    if args.record:
        want = set(args.record)
        records = [r for r in records if r["record_key"] in want]
    if args.only_ready:
        records = [r for r in records if r.get("ready")]

    print("=" * 64)
    print(f"评价结果：{args.result}")
    print(f"会话：{data.get('session')}｜待处理记录：{len(records)}")
    print(f"轨迹上传接口：{upload_url}（表单字段 {form_field}，取返回 {path_key}）")
    print(f"提交接口：{submit_url or '【未配置】'}")
    print(f"schema_fingerprint：{fingerprint or '【缺失】'}")
    print(f"凭据：{'已提供' if cookie else '【缺失】需要从浏览器复制整条 cookie'}"
          f"｜csrf header：{'已设置' if csrf_header else '（未设置）'}")
    print(f"模式：{'正式执行（--commit）' if args.commit else 'DRY-RUN（只打印计划，不发请求）'}")
    print("-" * 64)

    field_order = data.get("field_order") or (list(records[0]["fields"].keys()) if records else [])
    changed = False

    for r in records:
        tag = r["record_key"]
        local = r.get("trace_file_local")
        abs_local = os.path.join(WORKSPACE, local) if local else None
        size = os.path.getsize(abs_local) if abs_local and os.path.exists(abs_local) else 0
        size_mb = size / 1024 / 1024
        blockers = [i for i in r.get("issues", []) if i["level"] == "error"]
        print(f"· {tag}  轨迹={local} ({size_mb:.2f} MB{'  ⚠️超上限' if size_mb > max_mb else ''})")
        if blockers:
            print(f"    阻塞项：{'；'.join(i['message'] for i in blockers)}")

        if not args.commit:
            if args.show_payload:
                print("    请求体：")
                print(json.dumps(build_payload(r, field_order, fingerprint), ensure_ascii=False, indent=2))
            else:
                preview = json.dumps(build_payload(r, field_order, fingerprint), ensure_ascii=False)
                print(f"    请求体（截断）：{preview[:300]}…")
            continue

        # ---- 真发请求 ----
        if not abs_local or not os.path.exists(abs_local):
            print("    [跳过] 轨迹文件不存在")
            continue
        if not upload_url or not cookie:
            print("    [跳过] 缺少上传接口 URL 或凭据")
            continue
        # 已上传过（fields.trace_file 已是附件数组且带远端 path）就不重复传；
        # 注意：结果文件里未提交时 trace_file 可能是本机路径字符串，那种情况仍要上传
        tf = r["fields"].get("trace_file")
        already = isinstance(tf, list) and bool(tf) and bool(tf[0].get("path"))
        if not already:
            try:
                up = post_multipart(upload_url, cookie, abs_local, form_field=form_field)
                remote = up.get(path_key) or (up.get("data") or {}).get(path_key)
                if not remote:
                    print(f"    [失败] 上传返回里没找到 {path_key}：{up}")
                    continue
                att = {
                    "name": up.get("name") or os.path.basename(abs_local),
                    "path": remote,
                    "size": int(up.get("size") or size),
                }
                r["trace_file_uploaded"] = remote
                r["fields"]["trace_file"] = [att]
                changed = True
                print(f"    上传成功 → {remote}（{att['size']} bytes）")
            except urllib.error.HTTPError as e:
                print(f"    [失败] 上传 HTTP {e.code}：{e.read()[:200]!r}")
                continue
            except Exception as e:  # noqa: BLE001
                print(f"    [失败] 上传异常：{e}")
                continue
        else:
            print(f"    轨迹已上传：{r['trace_file_uploaded']}")

        if args.upload_only:
            continue
        if not submit_url:
            print("    [跳过提交] 提交接口 URL 未配置（轨迹已上传）")
            continue
        payload = build_payload(r, field_order, fingerprint)
        try:
            resp = post_json(submit_url, cookie, payload, csrf_header or None)
        except urllib.error.HTTPError as e:
            print(f"    [失败] 提交 HTTP {e.code}：{e.read()[:300]!r}")
            continue
        except Exception as e:  # noqa: BLE001
            print(f"    [失败] 提交异常：{e}")
            continue

        status = str(resp.get("status", "")).upper()
        ok = status == "SUBMITTED" or bool(resp.get("id"))
        r["submit_response"] = resp
        changed = True
        print(f"    {'提交成功' if ok else '提交返回异常'} → id={resp.get('id')} status={resp.get('status')}"
              f" round_no={resp.get('round_no')}")
        if resp.get("message"):
            print(f"    平台消息：{resp['message']}")
        if resp.get("schema_stale"):
            print("    ⚠️ schema_stale=true：表单字段规范已变，请重跑 extract_submit_fields.py 后重新生成并提交")

    if args.commit and args.write_back and changed:
        with open(args.result, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"- 已回写上传结果/接口返回到：{args.result}")

    print("=" * 64)
    if not args.commit:
        print("这是 dry-run：没有发任何请求。确认无误后加 --commit。")
        print("建议顺序：--upload-only --commit --write-back  →  --commit --write-back")
        print("（可用 --show-payload 看完整请求体）")


if __name__ == "__main__":
    main()
