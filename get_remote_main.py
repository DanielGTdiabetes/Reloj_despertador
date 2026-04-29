import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.204', username='dani', password='26021980')

# Get full remote main.py
stdin, stdout, stderr = ssh.exec_command('cat /home/dani/reloj_despertador/src/main.py')
remote_main = stdout.read().decode()
print(remote_main)

print("\n\n=== Syntax check ===")
stdin, stdout, stderr = ssh.exec_command('python3 -m py_compile /home/dani/reloj_despertador/src/main.py 2>&1; echo "EXIT:$?"')
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
