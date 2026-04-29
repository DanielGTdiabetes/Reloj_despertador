import paramiko
import os
import sys
import tarfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


PRESERVE_CONFIG_KEYS = ("wifi",)


def create_tar():
    print("Creating tarball...")
    with tarfile.open('project_updated.tar', 'w') as t:
        for f in ['src', 'config', 'scripts', 'requirements.txt', 'README.md']:
            if os.path.exists(f):
                t.add(f, filter=exclude_pycache)
    print("Tarball created.")

def exclude_pycache(tarinfo):
    """Exclude __pycache__ directories and .pyc files from tarball"""
    if '__pycache__' in tarinfo.name or tarinfo.name.endswith('.pyc'):
        return None
    return tarinfo

def deploy():
    host = os.environ.get('PI_HOST', '192.168.0.204')
    user = os.environ.get('PI_USER', 'dani')
    password = os.environ.get('PI_PASS', '26021980')
    remote_path = '/home/dani/reloj_despertador'

    create_tar()

    print(f"Connecting to {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    # Make sure remote dir exists
    ssh.exec_command(f'mkdir -p {remote_path}')

    print("Uploading tarball...")
    sftp = ssh.open_sftp()
    sftp.put('project_updated.tar', f'{remote_path}/project_updated.tar')
    sftp.close()

    print("Extracting tarball on device...")
    merge_script = " && ".join([
        f"cd {remote_path}",
        "cp config/config.json /tmp/reloj_config_before_deploy.json 2>/dev/null || true",
        "tar -xf project_updated.tar",
        (
            "python3 - <<'PY'\n"
            "import json, os\n"
            "before_path = '/tmp/reloj_config_before_deploy.json'\n"
            "after_path = 'config/config.json'\n"
            f"preserve = {list(PRESERVE_CONFIG_KEYS)!r}\n"
            "if os.path.exists(before_path) and os.path.exists(after_path):\n"
            "    with open(before_path, encoding='utf-8') as f:\n"
            "        before = json.load(f)\n"
            "    with open(after_path, encoding='utf-8') as f:\n"
            "        after = json.load(f)\n"
            "    for key in preserve:\n"
            "        if key in before:\n"
            "            after[key] = before[key]\n"
            "    before_wifi = before.get('wifi', {})\n"
            "    after_wifi = after.get('wifi', {})\n"
            "    before_had_wifi = bool(before_wifi.get('ssid') or before_wifi.get('password'))\n"
            "    after_has_wifi = bool(after_wifi.get('ssid') or after_wifi.get('password'))\n"
            "    if before_had_wifi and not after_has_wifi:\n"
            "        raise SystemExit('Refusing deploy: remote wifi config would be cleared')\n"
            "    tmp = after_path + '.tmp'\n"
            "    with open(tmp, 'w', encoding='utf-8') as f:\n"
            "        json.dump(after, f, indent=4, ensure_ascii=False)\n"
            "    os.replace(tmp, after_path)\n"
            "PY"
        ),
    ])
    stdin, stdout, stderr = ssh.exec_command(merge_script)
    merge_out = stdout.read().decode()
    print(merge_out)
    err = stderr.read().decode()
    if err:
        print(f"STDERR: {err}")
    merge_status = stdout.channel.recv_exit_status()
    if merge_status != 0:
        ssh.close()
        raise SystemExit(f"Deploy aborted while merging config, exit code {merge_status}")

    print("Running fresh-install bootstrap if available...")
    stdin, stdout, stderr = ssh.exec_command(
        f'cd {remote_path} && if [ -x scripts/bootstrap_fresh_pi.sh ]; then '
        f'echo "{password}" | sudo -S scripts/bootstrap_fresh_pi.sh; '
        f'elif [ -f scripts/bootstrap_fresh_pi.sh ]; then '
        f'chmod +x scripts/bootstrap_fresh_pi.sh && echo "{password}" | sudo -S scripts/bootstrap_fresh_pi.sh; '
        f'else echo "No bootstrap script found"; fi 2>&1'
    )
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err:
        print(f"STDERR: {err}")

    # Clear __pycache__ to prevent stale bytecode issues
    print("Clearing __pycache__...")
    stdin, stdout, stderr = ssh.exec_command(f'find {remote_path}/src -name "__pycache__" -type d -exec rm -rf {{}} + 2>&1')
    print(stdout.read().decode())

    # Restart the service to pick up changes
    print("Restarting service...")
    stdin, stdout, stderr = ssh.exec_command(f'echo "{password}" | sudo -S systemctl restart reloj.service 2>&1')
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err:
        print(f"STDERR: {err}")

    print("Deployment complete. Service restarting...")

    ssh.close()

if __name__ == '__main__':
    deploy()
