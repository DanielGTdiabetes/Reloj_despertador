import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.204', username='dani', password='26021980')

# Download all remote source files that differ from local
files_to_sync = [
    'src/main.py',
    'src/hardware/st7789.py',
    'src/hardware/gc9a01.py',
    'src/hardware/rotary_encoder.py',
    'src/hardware/audio.py',
    'src/hardware/__init__.py',
    'src/services/clock.py',
    'src/services/weather.py',
    'src/services/lunar.py',
    'src/services/sun.py',
    'src/services/alarm.py',
    'src/services/alerts.py',
    'src/services/__init__.py',
    'src/ui/clock_rect.py',
    'src/ui/weather_round.py',
    'src/ui/forecast_round.py',
    'src/ui/__init__.py',
    'src/graphics/renderer.py',
    'src/graphics/colors.py',
    'src/graphics/__init__.py',
    'src/__init__.py',
    'config/config.json',
    'requirements.txt',
    'README.md',
    'scripts/deploy.sh',
    'scripts/reloj.service',
]

import os
import hashlib

print("Syncing remote files to local...\n")
for fpath in files_to_sync:
    remote_full = f'/home/dani/reloj_despertador/{fpath}'
    local_full = f'D:\\Reloj_despertador\\{fpath}'

    # Get remote content
    stdin, stdout, stderr = ssh.exec_command(f'cat {remote_full}')
    remote_content = stdout.read().decode()
    remote_err = stderr.read().decode()

    if 'No such file' in remote_err:
        print(f"  SKIP (not found): {fpath}")
        continue

    # Check if local exists and differs
    try:
        with open(local_full, 'r', encoding='utf-8') as f:
            local_content = f.read()
        if remote_content == local_content:
            print(f"  OK (same): {fpath}")
            continue
    except (FileNotFoundError, UnicodeDecodeError):
        pass

    # Write remote content to local
    os.makedirs(os.path.dirname(local_full), exist_ok=True)
    with open(local_full, 'w', encoding='utf-8') as f:
        f.write(remote_content)
    print(f"  UPDATED: {fpath}")

print("\nSync complete.")
ssh.close()
