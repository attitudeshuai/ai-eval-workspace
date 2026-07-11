#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
从远程机器回收 SOTA 产物（修改后的源码、截图、日志等）。

远程配置读取 projects/webdev-long-horizon/config.toml 中的 [remote] 段，
密码读取 projects/webdev-long-horizon/secrets.toml（已加入 .gitignore）。

用法示例：
    python scripts/webdev-long-horizon/fetch_remote_results.py \
      --task webdev-task-01.01 \
      --agent codex \
      --session session-sota-2026-07-002-codex

也可以只拉回到当前目录：
    python scripts/webdev-long-horizon/fetch_remote_results.py \
      --task webdev-task-01.01 \
      --output ./
"""

import argparse
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def project_dir(project_id: str) -> Path:
    return workspace_root() / "projects" / project_id


def load_toml(path: Path) -> dict:
    import tomllib
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_remote_config(project_id: str) -> dict:
    """读取 config.toml 和 secrets.toml 合并远程配置。"""
    config_path = project_dir(project_id) / "config.toml"
    defaults = {
        "host": "59.49.28.154",
        "port": 7826,
        "user": "root",
        "remote_dir": "/root/charles",
        "password": "",
    }

    if config_path.exists():
        try:
            data = load_toml(config_path)
            remote = data.get("remote", {})
            for key in ["host", "port", "user", "remote_dir", "secrets_file"]:
                if key in remote:
                    defaults[key] = remote[key]

            secrets_file = remote.get("secrets_file", "secrets.toml")
            secrets_path = project_dir(project_id) / secrets_file
            if secrets_path.exists():
                secrets = load_toml(secrets_path)
                secrets_remote = secrets.get("remote", {})
                if "password" in secrets_remote:
                    defaults["password"] = secrets_remote["password"]
        except Exception as e:
            print(f"警告：读取配置失败，使用默认配置: {e}")

    return defaults


def ensure_paramiko():
    try:
        import paramiko
        return paramiko
    except ImportError:
        print("错误：需要安装 paramiko。请运行：pip install paramiko")
        sys.exit(1)


def ssh_client(config: dict):
    paramiko = ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=config["host"],
        port=int(config["port"]),
        username=config["user"],
        password=config["password"] or None,
    )
    return client


def remote_tar(client, remote_dir: str, task_id: str) -> str:
    """在远程打包任务目录，排除 node_modules 等依赖与构建产物。"""
    tar_name = f"{task_id}-results.tar.gz"
    excludes = " ".join([
        "--exclude='node_modules'",
        "--exclude='.git'",
        "--exclude='dist'",
        "--exclude='build'",
        "--exclude='.cache'",
        "--exclude='*.log'",
    ])
    cmd = f"cd {remote_dir} && tar czvf {tar_name} {excludes} {task_id}"
    print(f"$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(err, file=sys.stderr)
    return f"{remote_dir}/{tar_name}"


def sftp_download(client, remote_path: str, local_path: Path):
    sftp = client.open_sftp()
    print(f"下载 {remote_path} -> {local_path}")
    sftp.get(remote_path, str(local_path))
    sftp.close()


def main():
    # 先解析 project，再读取配置
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--project", default="webdev-long-horizon")
    pre_args, _ = pre_parser.parse_known_args()
    config = load_remote_config(pre_args.project)

    parser = argparse.ArgumentParser(description="从远程机器回收 SOTA 产物")
    parser.add_argument("--task", required=True, help="任务 ID，例如 webdev-task-01.01")
    parser.add_argument("--agent", default="codex", help="Agent 名称，默认 codex")
    parser.add_argument("--project", default="webdev-long-horizon", help="项目 ID，默认 webdev-long-horizon")
    parser.add_argument("--remote-host", default=config["host"], help="远程主机地址")
    parser.add_argument("--remote-port", type=int, default=int(config["port"]), help="远程 SSH 端口")
    parser.add_argument("--remote-user", default=config["user"], help="远程用户名")
    parser.add_argument("--remote-dir", default=config["remote_dir"], help="远程任务所在目录")
    parser.add_argument("--remote-password", default=config["password"], help="远程密码（不建议命令行传入）")
    parser.add_argument("--session", help="本地 session 名称；若提供，产物将整理到 sessions/<session>/...")
    parser.add_argument("--output", help="本地输出目录；与 --session 二选一，默认当前目录")
    args = parser.parse_args()

    task_id = args.task
    project_id = args.project
    agent = args.agent
    remote_dir = args.remote_dir.rstrip("/")

    # 决定本地输出路径
    if args.session and args.output:
        print("错误：--session 和 --output 不能同时使用")
        sys.exit(1)

    if args.session:
        local_base = Path("sessions") / args.session / "projects" / project_id / "submissions" / task_id / agent
        local_base.mkdir(parents=True, exist_ok=True)
        local_temp = local_base
    elif args.output:
        local_base = Path(args.output).resolve()
        local_base.mkdir(parents=True, exist_ok=True)
        local_temp = local_base
    else:
        local_base = Path.cwd()
        local_temp = local_base

    # 1. 连接远程
    print(f"\n[1/4] 连接远程 {args.remote_user}@{args.remote_host}:{args.remote_port} ...")
    client = ssh_client({
        "host": args.remote_host,
        "port": args.remote_port,
        "user": args.remote_user,
        "password": args.remote_password,
    })

    # 2. 远程打包（排除 node_modules 等；sota.log 单独下载保留）
    print(f"\n[2/4] 在远程打包 {remote_dir}/{task_id} ...")
    remote_tar_path = remote_tar(client, remote_dir, task_id)

    # 3. 下载到本地
    local_tar = local_temp / f"{task_id}-results.tar.gz"
    sftp_download(client, remote_tar_path, local_tar)

    # 单独下载 sota.log（tar 包中排除了 *.log）
    remote_log = f"{remote_dir}/{task_id}/sota.log"
    local_log = local_temp / "sota.log"
    try:
        sftp_download(client, remote_log, local_log)
    except Exception as e:
        print(f"警告：无法下载 sota.log: {e}")

    # 4. 本地解压
    print(f"\n[3/4] 解压 {local_tar} ...")
    with tarfile.open(local_tar, "r:gz") as tar:
        tar.extractall(path=local_temp)

    # 5. 整理到标准 session 结构（如果指定了 --session）
    extracted_dir = local_temp / task_id
    if args.session:
        print(f"\n[4/4] 整理到 session 目录 {local_base} ...")
        if extracted_dir.exists():
            source_dir = extracted_dir / "source"
            if source_dir.exists():
                target_source = local_base / "source"
                if target_source.exists():
                    shutil.rmtree(target_source)
                shutil.move(str(source_dir), str(target_source))

            screenshots_dir = extracted_dir / "screenshots"
            if screenshots_dir.exists():
                target_screenshots = local_base / "screenshots"
                if target_screenshots.exists():
                    shutil.rmtree(target_screenshots)
                shutil.move(str(screenshots_dir), str(target_screenshots))

            for name in ["sota.log", "PROMPT.md", "task.md"]:
                src = extracted_dir / name
                if src.exists():
                    dst = local_base / name
                    if dst.exists():
                        dst.unlink()
                    shutil.move(str(src), str(dst))

            shutil.rmtree(extracted_dir)
            local_tar.unlink()
        print(f"产物已整理到：{local_base}")
    else:
        print(f"\n[4/4] 产物已解压到：{extracted_dir}")
        print(f"tar 包保留在：{local_tar}")

    client.close()
    print("\n完成。")


if __name__ == "__main__":
    main()
