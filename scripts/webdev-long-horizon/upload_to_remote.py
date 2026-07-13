#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
将 webdev-long-horizon 任务的源码、task.md 和必要任务素材上传到远程机器。

SOTA 运行时需要看到参考截图和测试骨架，因此除源码外，还会上传：
  <remote_dir>/<task-id>/              # 源码
  <remote_dir>/<task-id>/PROMPT.md    # SOTA prompt（由 task.md 上传后重命名，可通过 --prompt-file 指定其他文件）
  <remote_dir>/<task-id>/assets/      # 参考截图等任务素材
  <remote_dir>/<task-id>/tests/       # 测试骨架（若存在）
  <remote_dir>/<task-id>/mock-data/   # Mock 数据（若存在）

任务资产中的 rubric.json、metadata.json、target_states.md、README.md 等保留在本地，不上传。

远程配置读取 projects/webdev-long-horizon/config.toml 中的 [remote] 段，
密码读取 projects/webdev-long-horizon/secrets.toml（已加入 .gitignore）。

用法示例：
    python scripts/webdev-long-horizon/upload_to_remote.py --task webdev-task-sxw-01.01
"""

import argparse
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
                # secrets.toml 优先级最高，可覆盖 host/port/user/password
                for key in ["host", "port", "user", "password"]:
                    if key in secrets_remote:
                        defaults[key] = secrets_remote[key]
        except Exception as e:
            print(f"警告：读取配置失败，使用默认配置: {e}")

    return defaults


# 打包时默认忽略的路径
IGNORED_ARCHIVE_NAMES = {
    "node_modules", ".git", "__pycache__", ".cache", "dist", "build",
    ".DS_Store", "Thumbs.db",
}


def tar_filter(member: tarfile.TarInfo) -> tarfile.TarInfo | None:
    """tarfile.add 的过滤函数，排除常见构建产物和依赖目录。"""
    if any(part in IGNORED_ARCHIVE_NAMES for part in Path(member.name).parts):
        return None
    return member


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


def remote_exec(client, cmd: str):
    print(f"$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)


def main():
    # 先解析 project，再读取配置
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--project", default="webdev-long-horizon")
    pre_args, _ = pre_parser.parse_known_args()
    config = load_remote_config(pre_args.project)

    parser = argparse.ArgumentParser(description="上传任务源码和提示词文件到远程机器")
    parser.add_argument("--task", required=True, help="任务 ID，例如 webdev-task-sxw-01.01")
    parser.add_argument("--project", default="webdev-long-horizon", help="项目 ID")
    parser.add_argument("--remote-host", default=config["host"], help="远程主机地址")
    parser.add_argument("--remote-port", type=int, default=int(config["port"]), help="远程 SSH 端口")
    parser.add_argument("--remote-user", default=config["user"], help="远程用户名")
    parser.add_argument("--remote-dir", default=config["remote_dir"], help="远程目标目录")
    parser.add_argument("--remote-password", default=config["password"], help="远程密码（不建议命令行传入）")
    parser.add_argument("--prompt-file", help="本地提示词文件路径，默认用 tasks/<family>/<task-id>/task.md")
    args = parser.parse_args()

    task_id = args.task
    project_id = args.project
    family = task_id.split(".")[0]

    tasks_family_dir = project_dir(project_id) / "tasks" / family
    sources_family_dir = project_dir(project_id) / "sources" / family
    task_dir = tasks_family_dir / task_id
    source_dir = sources_family_dir / task_id

    if args.prompt_file:
        prompt_file = Path(args.prompt_file)
    else:
        # 默认直接用 task.md 作为提示词
        prompt_file = task_dir / "task.md"

    assets_dir = task_dir / "assets"
    tests_dir = task_dir / "tests"
    mock_data_dir = task_dir / "mock-data"

    if not task_dir.exists():
        print(f"错误：任务目录不存在: {task_dir}")
        sys.exit(1)

    if not source_dir.exists():
        print(f"注意：源码目录不存在 ({source_dir})，Greenfield 任务将仅上传 task.md + assets + tests + mock-data")
        has_source = False
    else:
        has_source = True

    if not prompt_file.exists():
        print(f"错误：提示词文件不存在: {prompt_file}")
        sys.exit(1)

    source_tar = Path(f"{task_id}-source.tar.gz")

    # 1. 打包（源码放在 {task-id}/{task-id}/，素材放在 {task-id}/assets/、{task-id}/tests/、{task-id}/mock-data/）
    print(f"\n[1/3] 打包任务素材 {source_tar} ...")
    with tarfile.open(source_tar, "w:gz") as tar:
        if has_source:
            tar.add(source_dir, arcname=f"{task_id}/{task_id}", filter=tar_filter)
            print(f"  包含 {task_id}/{task_id}/: {source_dir}")
        else:
            # Greenfield: 创建空的 {task-id}/{task-id}/ 目录占位
            import io
            empty_dir = tarfile.TarInfo(name=f"{task_id}/{task_id}/")
            empty_dir.type = tarfile.DIRTYPE
            tar.addfile(empty_dir)
            print(f"  创建空目录 {task_id}/{task_id}/ (Greenfield)")
        if assets_dir.exists() and any(assets_dir.iterdir()):
            tar.add(assets_dir, arcname=f"{task_id}/assets", filter=tar_filter)
            print(f"  包含 assets/: {assets_dir}")
        if tests_dir.exists() and any(tests_dir.iterdir()):
            tar.add(tests_dir, arcname=f"{task_id}/tests", filter=tar_filter)
            print(f"  包含 tests/: {tests_dir}")
        if mock_data_dir.exists() and any(mock_data_dir.iterdir()):
            tar.add(mock_data_dir, arcname=f"{task_id}/mock-data", filter=tar_filter)
            print(f"  包含 mock-data/: {mock_data_dir}")

    # 2. SSH 连接并上传
    print(f"\n[2/3] 连接远程 {args.remote_user}@{args.remote_host}:{args.remote_port} ...")
    client = ssh_client({
        "host": args.remote_host,
        "port": args.remote_port,
        "user": args.remote_user,
        "password": args.remote_password,
    })

    remote_dir = args.remote_dir.rstrip("/")
    remote_task_dir = f"{remote_dir}/{task_id}"

    # 创建远程任务目录
    remote_exec(client, f"mkdir -p {remote_task_dir}")

    # 上传源码包
    sftp_upload(client, source_tar, f"{remote_dir}/{source_tar.name}")

    # 上传提示词文件（统一命名为 PROMPT.md，方便 codex 运行时使用）
    remote_prompt_path = f"{remote_task_dir}/PROMPT.md"
    sftp_upload(client, prompt_file, remote_prompt_path)

    # 3. 远程解压整理
    print(f"\n[3/3] 远程解压整理 ...")
    remote_exec(
        client,
        f"cd {remote_dir} && tar xzvf {source_tar.name} && rm -f {source_tar.name}",
    )

    client.close()

    # 清理本地 tar 包
    source_tar.unlink()

    print(f"\n完成。远程目录：{remote_task_dir}/")
    print(f"运行 codex（自动化需加 --dangerously-bypass-approvals-and-sandbox）：")
    print(f"  ssh {args.remote_user}@{args.remote_host} -p {args.remote_port}")
    print(f"  cd {remote_task_dir}/{task_id}")
    print(f"  codex exec -m gpt-5.6-sol --dangerously-bypass-approvals-and-sandbox \\")
    print(f"    < {remote_task_dir}/PROMPT.md \\")
    print(f"    > {remote_task_dir}/sota-run.md 2>&1")


if __name__ == "__main__":
    main()
