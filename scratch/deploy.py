import os
import paramiko
import stat

PI_USER = "dani"
PI_HOST = "192.168.0.204"
PI_PASS = "26021980"
PI_PATH = "/home/dani/reloj_despertador"

def put_dir(sftp, local_dir, remote_dir):
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass
    
    for item in os.listdir(local_dir):
        if item == "__pycache__":
            continue
        local_path = os.path.join(local_dir, item)
        remote_path = remote_dir + "/" + item
        if os.path.isfile(local_path):
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            put_dir(sftp, local_path, remote_path)

print("=== Deploying Reloj Despertador via paramiko ===")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PI_HOST, username=PI_USER, password=PI_PASS)

print("Creating directories on Pi...")
dirs = [
    "src/hardware", "src/graphics/icons", "src/ui", "src/services",
    "src/assets/fonts", "src/assets/sounds", "config", "scripts", "tests", "docs"
]
for d in dirs:
    ssh.exec_command(f"mkdir -p {PI_PATH}/{d}")

sftp = ssh.open_sftp()

print("Transferring files...")
put_dir(sftp, "src", PI_PATH + "/src")
put_dir(sftp, "config", PI_PATH + "/config")
put_dir(sftp, "scripts", PI_PATH + "/scripts")
if os.path.exists("requirements.txt"):
    sftp.put("requirements.txt", PI_PATH + "/requirements.txt")

sftp.close()

print("Installing Python dependencies...")
stdin, stdout, stderr = ssh.exec_command(f"pip3 install -r {PI_PATH}/requirements.txt")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
print("=== Deploy complete ===")
print(f"To run: ssh {PI_USER}@{PI_HOST} 'cd {PI_PATH} && python3 src/main.py'")
