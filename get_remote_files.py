import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.204', username='dani', password='26021980')

# Get all remote source files for comparison
files_to_check = [
    'src/main.py',
    'src/hardware/st7789.py',
    'src/hardware/gc9a01.py',
    'src/hardware/rotary_encoder.py',
    'src/hardware/audio.py',
    'config/config.json',
]

for fpath in files_to_check:
    print(f"\n{'='*60}")
    print(f"REMOTE: {fpath}")
    print(f"{'='*60}")
    stdin, stdout, stderr = ssh.exec_command(f'cat /home/dani/reloj_despertador/{fpath}')
    content = stdout.read().decode()
    print(content[:3000])
    if len(content) > 3000:
        print(f"... ({len(content)} total chars)")

ssh.close()
