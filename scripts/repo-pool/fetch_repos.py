#!/usr/bin/env python3
"""
开源仓库池（repo-pool）：按标准从 GitHub 搜索、拉取、去重开源仓库。

命令：
    list                 按 [criteria] 搜索候选仓库（不 clone）
    pull <owner/repo>    快照拉取 + 去重 + 写 manifest
    status               盘点 manifest 与本地目录一致性

配置：
    标准 / 路径：projects/repo-pool/config.toml
    凭证（可选 github_pat）：projects/repo-pool/secrets.toml

仅标准库（Python 3.11+，需 tomllib）。
"""

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_BASE = "https://api.github.com"
CODELOAD_BASE = "https://codeload.github.com"
USER_AGENT = "repo-pool-fetcher"

WS_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = WS_ROOT / "projects" / "repo-pool"


def fail(msg, code=1):
    print(f"错误：{msg}", file=sys.stderr)
    sys.exit(code)


def load_toml(path):
    import tomllib
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config():
    cfg_path = PROJECT_DIR / "config.toml"
    if not cfg_path.exists():
        fail(f"config.toml 不存在：{cfg_path}")
    return load_toml(cfg_path)


def load_token():
    sec_path = PROJECT_DIR / "secrets.toml"
    if not sec_path.exists():
        return ""
    try:
        return (load_toml(sec_path).get("github_pat") or "").strip()
    except Exception:
        return ""


def http_get(url, token):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        fail(f"HTTP {e.code} {url}\n{detail[:500]}")
    except urllib.error.URLError as e:
        fail(f"网络错误 {url}: {e.reason}")


def load_manifest(cfg):
    manifest_path = WS_ROOT / cfg["paths"]["manifest"]
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fail(f"manifest 解析失败：{manifest_path}")
    return {"session": "repo-pool", "repos": []}


def save_manifest(cfg, manifest):
    manifest_path = WS_ROOT / cfg["paths"]["manifest"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def hit_forbidden(repo, keywords):
    haystack = " ".join([
        repo.get("full_name") or "",
        repo.get("name") or "",
        repo.get("description") or "",
        " ".join(repo.get("topics") or []),
    ]).lower()
    for kw in keywords:
        if kw.lower() in haystack:
            return kw
    return None


def truncated(s, n=60):
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def cmd_list(cfg, args):
    token = load_token()
    langs = cfg["criteria"]["languages"]
    min_stars = cfg["criteria"]["min_stars"]
    max_inactive = cfg["criteria"]["max_inactive_days"]
    since = (datetime.now(timezone.utc) - timedelta(days=max_inactive)).strftime("%Y-%m-%d")
    keywords = cfg["criteria"]["forbidden_keywords"]
    s = cfg["criteria"]["search"]
    seen = set()
    print(f"# 拉取标准：语言={langs}  stars>{min_stars}  pushed>{since}  每语言最多 {s['max_pages']} 页")
    print()
    for lang in langs:
        q_raw = f"language:{lang} stars:>{min_stars} pushed:>{since}"
        q = urllib.parse.quote(q_raw, safe="")
        for page in range(1, s["max_pages"] + 1):
            url = (f"{API_BASE}/search/repositories?q={q}"
                   f"&sort={s['sort']}&order={s['order']}&per_page={s['per_page']}&page={page}")
            data = http_get(url, token)
            items = data.get("items") or []
            if not items:
                break
            for repo in items:
                fn = repo["full_name"]
                if fn in seen:
                    continue
                seen.add(fn)
                if hit_forbidden(repo, keywords):
                    continue
                topics = ",".join(repo.get("topics") or [])[:40]
                print(f"{fn:<40} ★{repo['stargazers_count']:<7} "
                      f"{(repo.get('language') or '-'):<10} "
                      f"{truncated(repo.get('description')):<62} {topics}")
        print()
    if token:
        print(f"共输出 {len(seen)} 个候选（已过滤严禁关键词）。")
    else:
        print(f"共输出 {len(seen)} 个候选（已过滤严禁关键词）。提示：配置 github_pat 可提升 Search API 额度。")


def cmd_pull(cfg, args):
    token = load_token()
    full_name = args.repo.strip().strip("/")
    if full_name.count("/") != 1:
        fail("仓库参数格式应为 owner/repo，例如 itwanger/paicoding")
    owner, repo = full_name.split("/", 1)

    meta = http_get(f"{API_BASE}/repos/{owner}/{repo}", token)
    default_branch = meta.get("default_branch") or "main"
    keywords = cfg["criteria"]["forbidden_keywords"]
    kw = hit_forbidden(meta, keywords)
    if kw:
        print(f"警告：命中严禁关键词「{kw}」，仍继续拉取（因你明确指定了该仓库）。")

    # 去重：manifest
    manifest = load_manifest(cfg)
    existing = next((r for r in manifest["repos"] if r.get("full_name") == full_name), None)
    if existing and not args.force:
        fail(f"已在 manifest 中：{full_name}（本地 {existing.get('local_path')}）。重拉请加 --force。")

    # 去重：本地目录
    pool_root = WS_ROOT / cfg["paths"]["pool_root"]
    target = pool_root / repo / f"{repo}-origin"
    if target.exists():
        print(f"警告：本地目录已存在 {target}，将覆盖。")
        shutil.rmtree(target)

    print(f"快照拉取 {full_name}（分支 {default_branch}）…")
    tarball_url = f"{CODELOAD_BASE}/{owner}/{repo}/tar.gz/refs/heads/{default_branch}"

    with tempfile.TemporaryDirectory() as tmp:
        tgz = Path(tmp) / "snapshot.tar.gz"
        headers = {"User-Agent": USER_AGENT}
        if token:
            headers["Authorization"] = f"token {token}"
        req = urllib.request.Request(tarball_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(tgz, "wb") as f:
                shutil.copyfileobj(resp, f)
        except urllib.error.HTTPError as e:
            fail(f"下载 tarball 失败 HTTP {e.code}：{tarball_url}（分支 {default_branch} 可能不存在）")

        extract_dir = Path(tmp) / "extract"
        extract_dir.mkdir()
        with tarfile.open(tgz, "r:gz") as tar:
            members = tar.getmembers()
            for m in members:
                if m.name.startswith("/") or ".." in m.name.split("/"):
                    fail(f"tarball 含非法路径：{m.name}")
            tar.extractall(extract_dir)
        tops = [p for p in extract_dir.iterdir() if p.is_dir()]
        src = tops[0] if len(tops) == 1 else extract_dir
        target.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            shutil.move(str(item), str(target / item.name))
        if src != extract_dir:
            shutil.rmtree(src)

    # 重新 init 成干净 origin 仓
    _git(target, "init", "-q")
    _git(target, "add", "-A")
    _git(target, "-c", "user.name=repo-pool", "-c", "user.email=repo-pool@localhost",
         "commit", "-q", "-m", "initial snapshot")

    entry = {
        "full_name": full_name,
        "repo_name": repo,
        "clone_url": meta.get("clone_url") or f"https://github.com/{owner}/{repo}.git",
        "default_branch": default_branch,
        "language": meta.get("language"),
        "framework": args.framework or "",
        "domain": args.domain or "",
        "task_types": [t.strip() for t in (args.task_types or "").split(",") if t.strip()],
        "stars": meta.get("stargazers_count"),
        "pushed_at": meta.get("pushed_at"),
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "local_path": f"sessions/repo-pool/repos/{repo}/{repo}-origin",
    }
    manifest["repos"] = [r for r in manifest["repos"] if r.get("full_name") != full_name]
    manifest["repos"].append(entry)
    save_manifest(cfg, manifest)

    print(f"已拉取：{full_name} → {target}")
    print(f"manifest 已更新（当前池内 {len(manifest['repos'])} 个仓库）。")
    print("下一步：人工 copy 到评估项目 session 的 source code/ 下再出题。")


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"git {' '.join(args)} 失败：{r.stderr.strip()[:500]}")


def cmd_status(cfg, args):
    manifest = load_manifest(cfg)
    pool_root = WS_ROOT / cfg["paths"]["pool_root"]
    entries = manifest.get("repos", [])
    known_repo_names = {e.get("repo_name") for e in entries}

    ok, missing = [], []
    for e in entries:
        path = WS_ROOT / e.get("local_path", "")
        if path.exists() and (path / ".git").exists():
            ok.append(e)
        else:
            missing.append(e)

    orphans = []
    if pool_root.exists():
        for proj in sorted(pool_root.iterdir()):
            if not proj.is_dir():
                continue
            origin = proj / f"{proj.name}-origin"
            if origin.exists() and proj.name not in known_repo_names:
                orphans.append(proj.name)

    print(f"池内 manifest 记录 {len(entries)} 个。")
    print(f"\n[正常] {len(ok)} 个：")
    for e in ok:
        print(f"  {e['full_name']:<40} {(e.get('language') or '-'):<10} {e.get('domain') or ''}")
    print(f"\n[清单有但目录缺] {len(missing)} 个：")
    for e in missing:
        print(f"  {e['full_name']:<40} {e.get('local_path')}")
    print(f"\n[目录有但清单缺（孤儿）] {len(orphans)} 个：")
    for n in orphans:
        print(f"  {n}")


def main():
    ap = argparse.ArgumentParser(description="开源仓库池：搜索/拉取/盘点 GitHub 仓库")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="按标准搜索候选仓库（不 clone）")

    p_pull = sub.add_parser("pull", help="快照拉取 + 去重")
    p_pull.add_argument("repo", help="owner/repo")
    p_pull.add_argument("--domain", help="业务领域标签（如 全栈Web应用）")
    p_pull.add_argument("--framework", help="技术栈标签（如 Spring Boot + Vue）")
    p_pull.add_argument("--task-types", help="可适配任务类型，逗号分隔")
    p_pull.add_argument("--force", action="store_true", help="manifest 已存在时强制重拉")

    sub.add_parser("status", help="盘点一致性")

    args = ap.parse_args()
    cfg = load_config()
    if args.cmd == "list":
        cmd_list(cfg, args)
    elif args.cmd == "pull":
        cmd_pull(cfg, args)
    elif args.cmd == "status":
        cmd_status(cfg, args)


if __name__ == "__main__":
    main()
