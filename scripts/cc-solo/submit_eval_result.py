#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-solo 评价结果提交（轨迹上传 + 表单提交）
==========================================
读取 build_eval_result.py 产出的评价结果 JSON，按「一轮 = 一条记录」提交：

 1. 轨迹文件是**附件**类型，先逐个上传拿远端 path（接口见 fields.json 的 upload_api）
 2. 再带着 24 个字段提交到提交接口

用法：
    # 看一眼会提交什么、会上传哪些文件（默认就是 dry-run，不联网）
    python scripts/cc-solo/submit_eval_result.py --result deliverables/cc-solo/session-0909/评价结果-session-0909-2026-09-10.json

    # 只上传轨迹并回填远端 path（拿到提交接口前可以先做这一步）
    python scripts/cc-solo/submit_eval_result.py --result <json> --upload-only --commit

    # 正式提交（URL 待管理员提供）
    python scripts/cc-solo/submit_eval_result.py --result <json> --url https://.../api/v1/submissions --commit
    python scripts/cc-solo/submit_eval_result.py --result <json> --commit      # 用 secrets.toml [submission].submit_url

配置（projects/cc-solo/secrets.toml，gitignore，勿提交）：
    [submission]
    submit_url = "https://<待补>/api/v1/submissions"   # 提交接口
    upload_url = "https://solo2.jzxhnh.com/api/v1/submissions/upload"  # 可选，默认取 fields.json
    cookie = "solo_qa_session=...; solo_qa_csrf=..."   # 浏览器里复制的整条 cookie
    csrf_header = ""                                   # 若接口需要 X-CSRF-Token，可在此显式指定

⚠️ 待确认（拿到接口文档/抓包后按需改这里的 build_payload）：
    - 提交接口的 URL、方法、请求体结构（当前按「一条记录一个 JSON 对象、字段名 = field_key」实现）
    - 是否需要分批（一次多条）或返回体里带 record_id
    - 轨迹附件的引用方式（当前把上传返回的 path 写进 trace_file 字段）
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

try:
    import tomllib
except ImportError:
    tomllib = None


def load_submission_settings():
    if not tomllib or not os.path.exists(SECRETS_PATH):
        return {}
    with open(SECRETS_PATH, "rb") as f:
        return tomllib.load(f).get("submission", {})


# ---------------------------------------------------------------- 网络
def post_multipart(url, cookie, file_path, form_field="file", timeout=120):
    """上传文件：multipart/form-data，返回解析后的 JSON。"""
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


def post_json(url, cookie, payload, csrf_header=None, timeout=60):
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


def build_payload(record, field_order):
    """一条记录 → 提交请求体。字段顺序固定，未取值填空字符串。"""
    return {k: record["fields"].get(k, "") for k in field_order}


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True, help="评价结果 JSON（build_eval_result.py 产物）")
    ap.add_argument("--url", help="提交接口 URL（覆盖 secrets.toml [submission].submit_url）")
    ap.add_argument("--cookie", help="整条 cookie 串（覆盖 secrets.toml [submission].cookie）")
    ap.add_argument("--record", action="append", help="只提交指定 record_key（可多次），如 h5-demo-feature-01#R01")
    ap.add_argument("--only-ready", action="store_true", help="只提交 ready=true 的记录（跳过有 error 的）")
    ap.add_argument("--upload-only", action="store_true", help="只上传轨迹、回填 path，不提交")
    ap.add_argument("--commit", action="store_true", help="真的发请求；不加则只打印计划（dry-run）")
    ap.add_argument("--write-back", action="store_true", help="上传成功后把远端 path 回写结果 JSON")
    args = ap.parse_args()

    with open(args.result, encoding="utf-8") as f:
        data = json.load(f)

    sec = load_submission_settings()
    # 凭据：cookie / token 两个键都认（secrets.toml [submission]）
    cookie = args.cookie or sec.get("cookie") or sec.get("token") or ""
    csrf_header = sec.get("csrf_header") or ""
    upload_api = data.get("upload_api", {}) or {}
    upload_url = sec.get("upload_url") or upload_api.get("url")
    form_field = upload_api.get("form_field", "file")
    path_key = upload_api.get("response_path_key", "path")
    submit_url = args.url or sec.get("submit_url") or (data.get("submit_api") or {}).get("url")

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
    print(f"提交接口：{submit_url or '【未配置】—— 拿到 URL 后写入 secrets.toml [submission].submit_url'}")
    print(f"cookie：{'已提供' if cookie else '【缺失】需要从浏览器复制整条 cookie'}"
          f"｜csrf header：{'已设置' if csrf_header else '（未设置）'}")
    print(f"模式：{'正式执行（--commit）' if args.commit else 'DRY-RUN（只打印计划）'}")
    print("-" * 64)

    field_order = data.get("field_order", list(records[0]["fields"].keys()) if records else [])

    for r in records:
        tag = r["record_key"]
        local = r.get("trace_file_local")
        abs_local = os.path.join(WORKSPACE, local) if local else None
        size = os.path.getsize(abs_local) if abs_local and os.path.exists(abs_local) else None
        size_mb = (size or 0) / 1024 / 1024
        max_mb = 20
        blockers = [i for i in r.get("issues", []) if i["level"] == "error"]
        print(f"· {tag}  轨迹={local} ({size_mb:.2f} MB {'OK' if size_mb <= max_mb else '超上限'})"
              f"{'  已上传=' + str(r.get('trace_file_uploaded')) if r.get('trace_file_uploaded') else ''}")
        if blockers:
            print(f"    阻塞项：{'；'.join(i['message'] for i in blockers)}")
        if not args.commit:
            demo = build_payload(r, field_order)
            demo.update({k: (v[:40] + '…' if isinstance(v, str) and len(v) > 40 else v)
                         for k, v in list(demo.items())})
            print(f"    将提交字段（截断展示）：{json.dumps(demo, ensure_ascii=False)[:400]}…")
            continue

        # ---- 真提交 ----
        if not local or not abs_local or not os.path.exists(abs_local):
            print("    [跳过] 轨迹文件不存在")
            continue
        if not upload_url or not cookie:
            print("    [跳过] 缺少上传接口 URL 或 cookie")
            continue
        try:
            up = post_multipart(upload_url, cookie, abs_local, form_field=form_field)
            remote = up.get(path_key) or (up.get("data") or {}).get(path_key)
            if not remote:
                print(f"    [失败] 上传返回里没找到 {path_key}：{up}")
                continue
            print(f"    上传成功 → {remote}")
            r["trace_file_uploaded"] = remote
            r["fields"]["trace_file"] = remote
        except urllib.error.HTTPError as e:
            print(f"    [失败] 上传 HTTP {e.code}：{e.read()[:200]!r}")
            continue
        except Exception as e:  # noqa: BLE001
            print(f"    [失败] 上传异常：{e}")
            continue

        if args.upload_only:
            continue
        if not submit_url:
            print("    [跳过提交] 提交接口 URL 未配置（轨迹已上传，path 见上）")
            continue
        try:
            resp = post_json(submit_url, cookie, build_payload(r, field_order), csrf_header or None)
            ok = resp.get("code") in (0, 200, None) and not resp.get("error")
            print(f"    {'提交成功' if ok else '提交返回异常'} → {json.dumps(resp, ensure_ascii=False)[:300]}")
        except urllib.error.HTTPError as e:
            print(f"    [失败] 提交 HTTP {e.code}：{e.read()[:300]!r}")
        except Exception as e:  # noqa: BLE001
            print(f"    [失败] 提交异常：{e}")

    if args.commit and args.write_back:
        with open(args.result, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"- 已回写远端轨迹 path 到：{args.result}")

    print("=" * 64)
    if not args.commit:
        print("这是 dry-run：没有发任何请求。确认无误后加 --commit。")
        print("首次正式提交前建议先只传轨迹：--upload-only --commit --write-back")


if __name__ == "__main__":
    main()
