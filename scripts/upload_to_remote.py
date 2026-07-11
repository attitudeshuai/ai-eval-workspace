#!/usr/bin/env python3
"""
将 webdev-long-horizon 任务资产和源码打包并上传到远程机器。

远程配置读取 projects/webdev-long-horizon/config.toml 中的 [remote] 段，
密码读取 projects/webdev-long-horizon/secrets.toml（已加入 .gitignore）。

用法示例：
    python scripts/upload_to_remote.py --task webdev-task-01.01
"""

import argparse
import subprocess
import sys
import tarfile
from pathlib import Path


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[1]


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

            # 读取 secrets 文件
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


def run(cmd, check=True):
    """运行本地 shell 命令。"""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, text=True)
    return result


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


def sftp_upload(client, local_path: Path, remote_path: str):
    sftp = client.open_sftp()
    print(f"上传 {local_path} -> {remote_path}")
    sftp.put(str(local_path), remote_path)
    sftp.close()


def main():
    # 先解析 project，再读取配置
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--project", default="webdev-long-horizon")
    pre_args, _ = pre_parser.parse_known_args()
    config = load_remote_config(pre_args.project)

    parser = argparse.ArgumentParser(description="打包并上传任务到远程机器")
    parser.add_argument("--task", required=True, help="任务 ID，例如 webdev-task-01.01")
    parser.add_argument("--project", default="webdev-long-horizon", help="项目 ID")
    parser.add_argument("--remote-host", default=config["host"], help="远程主机地址")
    parser.add_argument("--remote-port", type=int, default=int(config["port"]), help="远程 SSH 端口")
    parser.add_argument("--remote-user", default=config["user"], help="远程用户名")
    parser.add_argument("--remote-dir", default=config["remote_dir"], help="远程目标目录")
    parser.add_argument("--remote-password", default=config["password"], help="远程密码（不建议命令行传入）")
    args = parser.parse_args()

    task_id = args.task
    project_id = args.project
    family = task_id.split(".")[0]

    tasks_family_dir = project_dir(project_id) / "tasks" / family
    sources_family_dir = project_dir(project_id) / "sources" / family

    if not (tasks_family_dir / task_id).exists():
        print(f"错误：任务目录不存在: {tasks_family_dir / task_id}")
        sys.exit(1)

    if not (sources_family_dir / task_id).exists():
        print(f"错误：源码目录不存在: {sources_family_dir / task_id}")
        sys.exit(1)

    asset_tar = Path(f"{task_id}.tar.gz")
    source_tar = Path(f"{task_id}-source.tar.gz")

    # 1. 打包任务资产
    print(f"\n[1/4] 打包任务资产 {asset_tar} ...")
    with tarfile.open(asset_tar, "w:gz") as tar:
        tar.add(tasks_family_dir / task_id, arcname=task_id)

    # 2. 打包源码
    print(f"\n[2/4] 打包源码 {source_tar} ...")
    with tarfile.open(source_tar, "w:gz") as tar:
        tar.add(sources_family_dir / task_id, arcname=task_id)

    # 3. SSH 连接并上传
    print(f"\n[3/4] 连接远程 {args.remote_user}@{args.remote_host}:{args.remote_port} ...")
    client = ssh_client({
        "host": args.remote_host,
        "port": args.remote_port,
        "user": args.remote_user,
        "password": args.remote_password,
    })

    remote_dir = args.remote_dir.rstrip("/")
    sftp_upload(client, asset_tar, f"{remote_dir}/{asset_tar.name}")
    sftp_upload(client, source_tar, f"{remote_dir}/{source_tar.name}")

    # 4. 远程解压整理
    print(f"\n[4/4] 远程解压整理 ...")
    cmd = (
        f"mkdir -p {remote_dir} && cd {remote_dir} && "
        f"tar xzvf {asset_tar.name} && tar xzvf {source_tar.name} && "
        f"mv {task_id}-source {task_id}/source"
    )
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(err, file=sys.stderr)
    client.close()

    # 清理本地 tar 包
    asset_tar.unlink()
    source_tar.unlink()

    print(f"\n完成。远程目录：{remote_dir}/{task_id}/")
    print(f"运行 codex：")
    print(f"  ssh {args.remote_user}@{args.remote_host} -p {args.remote_port}")
    print(f"  cd {remote_dir}/{task_id}/source")
    print(f"  codex --model gpt-5.6-sonnet --prompt-file {remote_dir}/{task_id}/PROMPT.md")


if __name__ == "__main__":
    main()
