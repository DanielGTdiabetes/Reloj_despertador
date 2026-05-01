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

def sync_ui_files():
    """Copia archivos de src/deploy/src/ui/ a src/ui/ antes de empaquetar"""
    import shutil
    src_dir = os.path.join("src", "deploy", "src", "ui")
    dst_dir = os.path.join("src", "ui")
    
    if os.path.exists(src_dir):
        print(f"Syncing UI files from {src_dir} to {dst_dir}...")
        for filename in os.listdir(src_dir):
            if filename.endswith(".py"):
                shutil.copy2(os.path.join(src_dir, filename), os.path.join(dst_dir, filename))
                print(f"  - {filename} synced.")
    else:
        print("Warning: src/deploy/src/ui/ not found. Skipping sync.")

def deploy():
    host = os.environ.get('PI_HOST', '192.168.0.204')
    user = os.environ.get('PI_USER', 'dani')
    password = os.environ.get('PI_PASS', '26021980')
    remote_path = '/home/dani/reloj_despertador'

    # Sincronizar archivos locales primero
    sync_ui_files()
    
    create_tar()

    print(f"Connecting to {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    # 1. Backup remoto
    print("Creating remote backup of src/ui...")
    ssh.exec_command(f"cd {remote_path} && tar czf backup_ui_$(date +%Y%m%d_%H%M).tar.gz src/ui/ 2>/dev/null || echo 'No existing ui to backup'")

    print("Uploading tarball...")
    sftp = ssh.open_sftp()
    sftp.put('project_updated.tar', f'{remote_path}/project_updated.tar')
    sftp.close()

    print("Extracting and verifying...")
    merge_script = f"""
cd {remote_path}
cp config/config.json /tmp/reloj_config_before_deploy.json 2>/dev/null || true
tar -xf project_updated.tar
python3 - <<'PY'
import json, os
before_path = '/tmp/reloj_config_before_deploy.json'
after_path = 'config/config.json'
preserve = {list(PRESERVE_CONFIG_KEYS)!r}
if os.path.exists(before_path) and os.path.exists(after_path):
    with open(before_path, encoding='utf-8') as f:
        before = json.load(f)
    with open(after_path, encoding='utf-8') as f:
        after = json.load(f)
    for key in preserve:
        if key in before:
            after[key] = before[key]
    before_wifi = before.get('wifi', {{}})
    after_wifi = after.get('wifi', {{}})
    before_had_wifi = bool(before_wifi.get('ssid') or before_wifi.get('password'))
    after_has_wifi = bool(after_wifi.get('ssid') or after_wifi.get('password'))
    if before_had_wifi and not after_has_wifi:
        raise SystemExit('Refusing deploy: remote wifi config would be cleared')
    tmp = after_path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(after, f, indent=4, ensure_ascii=False)
    os.replace(tmp, after_path)
PY
cd src && python3 -c "from ui.weather_icons import render_weather_icon; from ui.round_home import RoundHomeScreen; from ui.rect_ui import RectUIScreen; from ui.theme import draw_menu_icon; print('Importaciones OK')"
"""
    stdin, stdout, stderr = ssh.exec_command(merge_script)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err: print(f"STDERR: {err}")
    
    if stdout.channel.recv_exit_status() != 0:
        ssh.close()
        raise SystemExit("Extraction or Verification failed.")

    print("Clearing __pycache__ and restarting service...")
    ssh.exec_command(f'find {remote_path}/src -name "__pycache__" -type d -exec rm -rf {{}} +')
    ssh.exec_command(f'echo "{password}" | sudo -S systemctl restart reloj.service')

    print("Deployment complete. Monitoring logs...")
    stdin, stdout, stderr = ssh.exec_command(f'sudo journalctl -u reloj.service -n 20 --no-pager')
    print(stdout.read().decode())

    ssh.close()

if __name__ == '__main__':
    deploy()

if __name__ == '__main__':
    deploy()
