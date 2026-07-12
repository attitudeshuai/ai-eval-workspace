import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('59.49.28.154', port=7826, username='root', password='kv1PG4eMqFq2Xd7f')

# 创建 source 目录并后台运行 codex
cmd = (
    "mkdir -p /root/charles/webdev-task-sxw-02/source && "
    "cd /root/charles/webdev-task-sxw-02/source && "
    "nohup bash -c 'codex exec -m gpt-5.6-sol --dangerously-bypass-approvals-and-sandbox "
    "< /root/charles/webdev-task-sxw-02/PROMPT.md "
    "> /root/charles/webdev-task-sxw-02/sota.log 2>&1' &>/dev/null & "
    "echo PID=$!"
)
stdin, stdout, stderr = c.exec_command(cmd)
print('stdout:', stdout.read().decode())
print('stderr:', stderr.read().decode())

# 等几秒确认进程已启动
import time
time.sleep(3)
stdin2, stdout2, stderr2 = c.exec_command('ps aux | grep "webdev-task-sxw-02" | grep -v grep; echo DONE')
print('进程检查:', stdout2.read().decode())

c.close()
