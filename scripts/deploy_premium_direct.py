import errno
import json
import os

import paramiko

def deploy_premium():
    host = '192.168.0.204'
    user = 'dani'
    password = '26021980'
    remote_root = '/home/dani/reloj_despertador'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    print("1. Preparing remote folders...")
    ssh.exec_command(f'rm -rf {remote_root}/src/ui {remote_root}/src/assets/menu_icons')
    ssh.exec_command(
        f'mkdir -p {remote_root}/src/ui {remote_root}/src/assets/menu_icons '
        f'{remote_root}/src/hardware {remote_root}/src/services {remote_root}/config'
    )

    sftp = ssh.open_sftp()

    def upload_if_exists(local, remote):
        if os.path.exists(local):
            sftp.put(local, remote)
            print(f"  Uploaded {local}")
        else:
            print(f"  Skipped missing file {local}")

    def remote_exists(remote):
        try:
            sftp.stat(remote)
            return True
        except OSError as exc:
            if getattr(exc, "errno", None) in (errno.ENOENT, None):
                return False
            raise

    def sync_config_safely(local, remote):
        if not os.path.exists(local):
            print(f"  Skipped missing file {local}")
            return

        if not remote_exists(remote):
            sftp.put(local, remote)
            print(f"  Seeded missing remote config from {local}")
            return

        with open(local, encoding="utf-8") as local_file:
            local_config = json.load(local_file)

        with sftp.open(remote, "r") as remote_file:
            remote_data = remote_file.read()
        if isinstance(remote_data, bytes):
            remote_data = remote_data.decode("utf-8")
        remote_config = json.loads(remote_data)

        local_ups = local_config.get("ups", {})
        remote_ups = remote_config.setdefault("ups", {})
        changed = False

        for key, value in local_ups.items():
            if key not in remote_ups:
                remote_ups[key] = value
                changed = True

        if not changed:
            print("  Preserved existing remote config runtime settings")
            return

        tmp_remote = f"{remote}.tmp"
        with sftp.open(tmp_remote, "w") as remote_file:
            json.dump(remote_config, remote_file, indent=4, ensure_ascii=False)
            remote_file.write("\n")
        sftp.rename(tmp_remote, remote)
        print("  Merged missing UPS config defaults without overwriting runtime settings")

    print("2. Uploading UI files...")
    ui_files = ['round_home.py', 'rect_ui.py', 'theme.py', 'weather_icons.py']
    for f in ui_files:
        src = os.path.join('src', 'ui', f)
        dst = f"{remote_root}/src/ui/{f}"
        sftp.put(src, dst)
        print(f"  Uploaded {f}")
        
    print("3. Uploading Icons...")
    icon_dir = 'src/assets/menu_icons'
    for f in os.listdir(icon_dir):
        if f.endswith('.png'):
            src = os.path.join(icon_dir, f)
            dst = f"{remote_root}/src/assets/menu_icons/{f}"
            sftp.put(src, dst)
            print(f"  Uploaded icon {f}")

    print("4. Uploading UPS battery support files...")
    support_files = [
        ('src/hardware/ups_hat.py', f'{remote_root}/src/hardware/ups_hat.py'),
        ('src/hardware/__init__.py', f'{remote_root}/src/hardware/__init__.py'),
        ('src/services/battery.py', f'{remote_root}/src/services/battery.py'),
        ('src/services/__init__.py', f'{remote_root}/src/services/__init__.py'),
        ('requirements.txt', f'{remote_root}/requirements.txt'),
        ('diag_battery.py', f'{remote_root}/diag_battery.py'),
    ]
    sync_config_safely('config/config.json', f'{remote_root}/config/config.json')
    for local, remote in support_files:
        upload_if_exists(local, remote)

    sftp.close()

    print("5. Restarting service...")
    ssh.exec_command(f'echo "{password}" | sudo -S systemctl restart reloj.service')
    ssh.close()
    print("Done!")

if __name__ == "__main__":
    deploy_premium()
