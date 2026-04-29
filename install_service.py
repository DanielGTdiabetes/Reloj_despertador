import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.204', username='dani', password='26021980')

# 1. Install systemd service
print("1. Installing systemd service...")
service_content = """[Unit]
Description=Reloj Despertador
After=network.target

[Service]
User=dani
WorkingDirectory=/home/dani/reloj_despertador
ExecStart=/usr/bin/python3 -u src/main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONDONTWRITEBYTECODE=1

[Install]
WantedBy=multi-user.target
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/reloj.service', 'w') as f:
    f.write(service_content)

# Copy to systemd and enable
stdin, stdout, stderr = ssh.exec_command('sudo cp /tmp/reloj.service /etc/systemd/system/reloj.service && sudo systemctl daemon-reload && sudo systemctl enable reloj.service 2>&1')
out = stdout.read().decode()
err = stderr.read().decode()
print(f"  Enable: {out}{err}")

# 2. Start the service
print("2. Starting service...")
stdin, stdout, stderr = ssh.exec_command('sudo systemctl start reloj.service 2>&1')
print(f"  Start: {stdout.read().decode()}{stderr.read().decode()}")

# 3. Check status after 5 seconds
import time
time.sleep(5)
stdin, stdout, stderr = ssh.exec_command('sudo systemctl status reloj.service --no-pager 2>&1')
status = stdout.read().decode()
print(f"3. Status:\n{status}")

# 4. Check recent logs
print("4. Recent logs:")
stdin, stdout, stderr = ssh.exec_command('journalctl -u reloj.service --no-pager -n 20 2>&1')
logs = stdout.read().decode()
print(logs)

ssh.close()
