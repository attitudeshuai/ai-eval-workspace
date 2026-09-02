#!/usr/bin/env python3
"""
仓库拉取器（repo-fetcher）：从 GitHub 搜索、快照拉取、去重开源仓库，黑名单跳过已用过的仓库。

命令：
    list                       按 [criteria] 搜索候选（排除黑名单与已拉取，不 clone）
    pull <owner/repo>          快照拉取单个仓库（黑名单 / manifest 自动跳过）
    pull --file <清单>         从清单批量拉取（每行 owner/repo，# 开头为注释）
    blacklist add <owner/repo>    把仓库加入黑名单（标记已用过）
    blacklist remove <owner/repo> 把仓库移出黑名单
    blacklist list                查看黑名单
    task <owner/repo> <次数>      记录仓库做题次数（0 表示清除）
    table                      生成 repos.md 状态表（仓库地址/是否做题/次数/黑名单）
    status                     盘点 manifest 与本地目录一致性

配置：projects/repo-fetcher/config.toml（[criteria] 标准 + [paths] 路径）
凭证：projects/repo-fetcher/secrets.toml（github_pat，可选但建议配置）
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
USER_AGENT = "repo-fetcher"

WS_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = WS_ROOT / "projects" / "repo-fetcher"


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


# ---------------- manifest ----------------

def load_manifest(cfg):
    manifest_path = WS_ROOT / cfg["paths"]["manifest"]
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fail(f"manifest 解析失败：{manifest_path}")
    return {"session": "repo-fetcher", "repos": []}


def save_manifest(cfg, manifest):
    manifest_path = WS_ROOT / cfg["paths"]["manifest"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------- 黑名单 ----------------

def _normalize(full_name):
    """统一成 owner/repo：去掉空白、末尾斜杠与 github.com 前缀。"""
    s = full_name.strip().strip("/")
    low = s.lower()
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if low.startswith(prefix):
            s = s[len(prefix):]
            break
    return s.strip("/")


def load_blacklist(cfg):
    """返回黑名单 owner/repo 列表（保序去重）。"""
    path = WS_ROOT / cfg["paths"]["blacklist"]
    if not path.exists():
        return []
    names, seen = [], set()
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = _normalize(ln)
        if s and not ln.lstrip().startswith("#") and s not in seen:
            seen.add(s)
            names.append(s)
    return names


def save_blacklist(cfg, names):
    path = WS_ROOT / cfg["paths"]["blacklist"]
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# 黑名单：已经用过的仓库，每行一个 GitHub 地址，# 开头为注释。",
        "# 搜索（list）与拉取（pull）会自动跳过这些仓库。",
        "# 一个仓库用完（提交满任务/不再复用）后，执行：",
        "#   python scripts/repo-fetcher/fetch.py blacklist add <owner/repo>",
    ]
    lines = header + sorted(f"https://github.com/{_normalize(n)}" for n in names)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_tasks(cfg):
    """返回 {owner/repo: 做题次数}。"""
    path = WS_ROOT / cfg["paths"]["tasks"]
    tasks = {}
    if not path.exists():
        return tasks
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        name = _normalize(parts[0])
        if not name or name.count("/") != 1:
            continue
        try:
            cnt = int(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            cnt = 0
        if cnt > 0:
            tasks[name] = cnt
    return tasks


def save_tasks(cfg, tasks):
    path = WS_ROOT / cfg["paths"]["tasks"]
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# 做题次数记录（owner/repo 空格 次数），每行一条，# 开头为注释。",
        "# 用 fetch.py task <owner/repo> <次数> 更新；用 fetch.py table 生成 repos.md。",
    ]
    lines = header + [f"{n} {c}" for n, c in sorted(tasks.items()) if c > 0]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------- 过滤 ----------------

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


# ---------------- list ----------------

def cmd_list(cfg, args):
    token = load_token()
    blacklist = set(load_blacklist(cfg))
    pulled = {r.get("full_name") for r in load_manifest(cfg).get("repos", [])}
    langs = cfg["criteria"]["languages"]
    min_stars = cfg["criteria"]["min_stars"]
    max_inactive = cfg["criteria"]["max_inactive_days"]
    since = (datetime.now(timezone.utc) - timedelta(days=max_inactive)).strftime("%Y-%m-%d")
    keywords = cfg["criteria"]["forbidden_keywords"]
    s = cfg["criteria"]["search"]
    seen = set()
    shown = 0
    print(f"# 拉取标准：语言={langs}  stars>{min_stars}  pushed>{since}  每语言最多 {s['max_pages']} 页")
    print(f"# 已排除：黑名单 {len(blacklist)} 个、已拉取 {len(pulled)} 个")
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
                if fn in blacklist:
                    continue
                if fn in pulled:
                    continue
                if hit_forbidden(repo, keywords):
                    continue
                shown += 1
                topics = ",".join(repo.get("topics") or [])[:40]
                print(f"{fn:<40} ★{repo['stargazers_count']:<7} "
                      f"{(repo.get('language') or '-'):<10} "
                      f"{truncated(repo.get('description')):<62} {topics}")
        print()
    print(f"共输出 {shown} 个候选（已过滤严禁关键词 + 黑名单 + 已拉取）。")


# ---------------- pull ----------------

def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"git {' '.join(args)} 失败：{r.stderr.strip()[:500]}")


def _pull_one(cfg, args, full_name, token, manifest, blacklist):
    """拉取单个仓库并更新 manifest（不落盘）。返回 True 表示本次新拉取。"""
    full_name = _normalize(full_name)
    if full_name.count("/") != 1:
        print(f"跳过：格式非法「{full_name}」（应为 owner/repo）")
        return False
    if full_name in blacklist:
        print(f"跳过（黑名单·已用过）：{full_name}")
        return False

    existing = next((r for r in manifest["repos"] if r.get("full_name") == full_name), None)
    if existing and not args.force:
        print(f"跳过（已在 manifest）：{full_name} → {existing.get('local_path')}。重拉加 --force。")
        return False

    owner, repo = full_name.split("/", 1)
    meta = http_get(f"{API_BASE}/repos/{owner}/{repo}", token)
    default_branch = meta.get("default_branch") or "main"
    kw = hit_forbidden(meta, cfg["criteria"]["forbidden_keywords"])
    if kw:
        print(f"警告：{full_name} 命中严禁关键词「{kw}」，仍继续拉取（因你明确指定）。")

    pool_root = WS_ROOT / cfg["paths"]["pool_root"]
    target = pool_root / repo / f"{repo}-origin"
    if target.exists():
        print(f"警告：本地目录已存在 {target}，将覆盖。")
        shutil.rmtree(target)

    print(f"快照拉取 {full_name}（分支 {default_branch}）…")
    tarball_url = f"{CODELOAD_BASE}/{owner}/{repo}/tar.gz/refs/heads/{default_branch}"

    tmp_base = WS_ROOT / "sessions" / "repo-fetcher" / ".tmp"
    tmp_base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(tmp_base)) as tmp:
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
            for m in tar.getmembers():
                if m.name.startswith("/") or ".." in m.name.split("/"):
                    fail(f"tarball 含非法路径：{m.name}")
            tar.extractall(extract_dir, filter="data")
        tops = [p for p in extract_dir.iterdir() if p.is_dir()]
        src = tops[0] if len(tops) == 1 else extract_dir
        target.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            shutil.move(str(item), str(target / item.name))
        if src != extract_dir:
            shutil.rmtree(src)

    _git(target, "init", "-q")
    _git(target, "add", "-A")
    _git(target, "-c", "user.name=repo-fetcher", "-c", "user.email=repo-fetcher@localhost",
         "commit", "-q", "-m", "initial snapshot")

    entry = {
        "full_name": full_name,
        "repo_name": repo,
        "clone_url": meta.get("clone_url") or f"https://github.com/{owner}/{repo}.git",
        "html_url": meta.get("html_url") or f"https://github.com/{owner}/{repo}",
        "default_branch": default_branch,
        "language": meta.get("language"),
        "domain": args.domain or "",
        "framework": args.framework or "",
        "task_types": [t.strip() for t in (args.task_types or "").split(",") if t.strip()],
        "stars": meta.get("stargazers_count"),
        "pushed_at": meta.get("pushed_at"),
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "local_path": f"sessions/repo-fetcher/repos/{repo}/{repo}-origin",
    }
    manifest["repos"] = [r for r in manifest["repos"] if r.get("full_name") != full_name]
    manifest["repos"].append(entry)
    print(f"已拉取：{full_name} → {target}")
    return True


def _read_list_file(path):
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = _normalize(ln)
        if s and not ln.lstrip().startswith("#"):
            out.append(s)
    return out


def cmd_pull(cfg, args):
    token = load_token()
    manifest = load_manifest(cfg)
    blacklist = set(load_blacklist(cfg))

    if args.file:
        path = Path(args.file)
        if not path.exists():
            fail(f"清单文件不存在：{path}")
        repos = _read_list_file(path)
        if not repos:
            fail(f"清单文件为空或只有注释：{path}")
        print(f"从清单读取 {len(repos)} 个仓库：{path}\n")
        done = skipped = 0
        for fn in repos:
            try:
                if _pull_one(cfg, args, fn, token, manifest, blacklist):
                    done += 1
                else:
                    skipped += 1
            except (SystemExit, Exception) as e:
                skipped += 1
                msg = str(e).strip() if str(e).strip() else type(e).__name__
                print(f"  …{fn} 拉取失败（{msg}），继续下一个。")
            print()
        save_manifest(cfg, manifest)
        print(f"批量拉取完成：新拉取 {done} 个、跳过/失败 {skipped} 个；池内共 {len(manifest['repos'])} 个仓库。")
        return

    if not args.repo:
        fail("请提供 owner/repo，或用 --file 指定清单文件。")
    _pull_one(cfg, args, args.repo, token, manifest, blacklist)
    save_manifest(cfg, manifest)
    print(f"manifest 已更新（当前池内 {len(manifest['repos'])} 个仓库）。")
    print("下一步：人工 copy 到评估项目 session 的 source code/ 下再出题。")


# ---------------- blacklist ----------------

def cmd_blacklist(cfg, args):
    names = load_blacklist(cfg)
    if args.action == "list":
        if not names:
            print("黑名单为空。")
        else:
            print(f"黑名单共 {len(names)} 个仓库：")
            for n in names:
                print(f"  https://github.com/{n}")
        return

    if not args.repo:
        fail("add / remove 需要提供 owner/repo")
    fn = _normalize(args.repo)
    if args.action == "add":
        if fn in names:
            print(f"已在黑名单：{fn}")
        else:
            names.append(fn)
            save_blacklist(cfg, names)
            print(f"已加入黑名单：{fn}")
    elif args.action == "remove":
        if fn in names:
            names.remove(fn)
            save_blacklist(cfg, names)
            print(f"已移出黑名单：{fn}")
        else:
            print(f"不在黑名单：{fn}")


# ---------------- task / table ----------------

def cmd_task(cfg, args):
    fn = _normalize(args.repo)
    if fn.count("/") != 1:
        fail("格式应为 owner/repo")
    tasks = load_tasks(cfg)
    if args.count <= 0:
        tasks.pop(fn, None)
    else:
        tasks[fn] = args.count
    save_tasks(cfg, tasks)
    print(f"已记录 {fn} 做题次数 = {args.count}")


def cmd_table(cfg, args):
    wish_path = WS_ROOT / cfg["paths"]["wishlist"]
    wish = _read_list_file(wish_path) if wish_path.exists() else []
    tasks = load_tasks(cfg)
    blacklist = set(load_blacklist(cfg))

    names, seen = [], set()
    for n in list(wish) + list(tasks.keys()) + sorted(blacklist):
        n = _normalize(n)
        if n and n.count("/") == 1 and n not in seen:
            seen.add(n)
            names.append(n)
    names.sort()

    lines = [
        "# 仓库状态总览",
        "",
        "| 仓库地址 | 是否做了题 | 做题次数 | 是否在黑名单 |",
        "|----------|:---:|:---:|:---:|",
    ]
    for n in names:
        cnt = tasks.get(n, 0)
        done = "是" if cnt > 0 else "否"
        in_bl = "是" if n in blacklist else "否"
        lines.append(f"| https://github.com/{n} | {done} | {cnt} | {in_bl} |")

    path = WS_ROOT / cfg["paths"]["table"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成状态表（{len(names)} 行）：{path}")


# ---------------- status ----------------

def cmd_status(cfg, args):
    manifest = load_manifest(cfg)
    pool_root = WS_ROOT / cfg["paths"]["pool_root"]
    blacklist = set(load_blacklist(cfg))
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

    print(f"池内 manifest 记录 {len(entries)} 个；黑名单 {len(blacklist)} 个。")
    print(f"\n[正常] {len(ok)} 个：")
    for e in ok:
        mark = "（黑名单）" if e["full_name"] in blacklist else ""
        url = e.get("html_url") or f"https://github.com/{e['full_name']}"
        print(f"  {e['full_name']:<38} {(e.get('language') or '-'):<10} {url}{mark}")
    print(f"\n[清单有但目录缺] {len(missing)} 个：")
    for e in missing:
        print(f"  {e['full_name']:<40} {e.get('local_path')}")
    print(f"\n[目录有但清单缺（孤儿）] {len(orphans)} 个：")
    for n in orphans:
        print(f"  {n}")


# ---------------- main ----------------

def main():
    ap = argparse.ArgumentParser(description="仓库拉取器：搜索/拉取/去重/黑名单 GitHub 仓库")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="按标准搜索候选（排除黑名单与已拉取，不 clone）")

    p_pull = sub.add_parser("pull", help="快照拉取 + 去重（单个或从清单批量）")
    p_pull.add_argument("repo", nargs="?", help="owner/repo（用 --file 批量时省略）")
    p_pull.add_argument("--file", help="从清单批量拉取（每行 owner/repo，# 开头为注释）")
    p_pull.add_argument("--domain", help="业务领域标签")
    p_pull.add_argument("--framework", help="技术栈标签")
    p_pull.add_argument("--task-types", help="可适配任务类型，逗号分隔")
    p_pull.add_argument("--force", action="store_true", help="manifest 已存在时强制重拉")

    p_bl = sub.add_parser("blacklist", help="黑名单管理（已用过的仓库）")
    p_bl.add_argument("action", choices=["add", "remove", "list"], help="add / remove / list")
    p_bl.add_argument("repo", nargs="?", help="owner/repo（add/remove 时必填）")

    p_task = sub.add_parser("task", help="记录仓库做题次数")
    p_task.add_argument("repo", help="owner/repo")
    p_task.add_argument("count", type=int, help="做题次数（0 表示清除）")

    sub.add_parser("table", help="生成 repos.md 状态表")

    sub.add_parser("status", help="盘点 manifest 与本地目录一致性")

    args = ap.parse_args()
    cfg = load_config()
    if args.cmd == "list":
        cmd_list(cfg, args)
    elif args.cmd == "pull":
        cmd_pull(cfg, args)
    elif args.cmd == "blacklist":
        cmd_blacklist(cfg, args)
    elif args.cmd == "task":
        cmd_task(cfg, args)
    elif args.cmd == "table":
        cmd_table(cfg, args)
    elif args.cmd == "status":
        cmd_status(cfg, args)


if __name__ == "__main__":
    main()
