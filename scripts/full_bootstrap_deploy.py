
import paramiko
import os
import sys
import time

# Host details
HOST = '192.168.0.204'
USER = 'dani'
PASS = '26021980'
REMOTE_DIR = '/home/dani/reloj_despertador'

def upload_dir(sftp, local_dir, remote_dir):
    """Recursively uploads a directory."""
    print(f"Syncing {local_dir} -> {remote_dir}")
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass  # Directory likely already exists

    for item in os.listdir(local_dir):
        if item in ['.git', '__pycache__', '.pytest_cache', '.vscode', '.claude']:
            continue
        
        local_path = os.path.join(local_dir, item)
        remote_path = remote_dir + '/' + item
        
        if os.path.isfile(local_path):
            print(f"  Uploading {item}...")
            if item.endswith('.sh'):
                with open(local_path, 'rb') as f:
                    content = f.read().replace(b'\r\n', b'\n')
                with sftp.file(remote_path, 'wb') as f:
                    f.write(content)
            else:
                sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            upload_dir(sftp, local_path, remote_path)

def full_bootstrap_deploy():
    print(f"--- STARTING FULL BOOTSTRAP DEPLOY TO {HOST} ---")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        ssh.connect(HOST, username=USER, password=PASS, timeout=10)
        sftp = ssh.open_sftp()
        
        # 1. Prepare directory structure
        print("Cleaning up / Creating remote directory...")
        stdin, stdout, stderr = ssh.exec_command(f"rm -rf {REMOTE_DIR}")
        stdout.channel.recv_exit_status()
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
        stdout.channel.recv_exit_status()
        
        # 2. Upload everything
        # folders = ['src', 'config', 'scripts']
        # For simplicity and to ensure we don't miss anything, we'll upload the main folders
        for folder in ['src', 'config', 'scripts', 'assets']:
            if os.path.isdir(folder):
                upload_dir(sftp, folder, f"{REMOTE_DIR}/{folder}")
            else:
                # Handle assets if they are in the root
                if folder == 'assets':
                    # Check if it's in src/assets
                    if os.path.isdir('src/assets'):
                        pass # Already uploaded via src
        
        # Upload requirements
        if os.path.exists('requirements.txt'):
            print("Uploading requirements.txt...")
            sftp.put('requirements.txt', f"{REMOTE_DIR}/requirements.txt")
        
        sftp.close()
        
        # 3. Run Bootstrap
        print("\n--- RUNNING BOOTSTRAP ON PI ---")
        print("This may take several minutes as it installs system packages...")
        
        bootstrap_cmd = f"cd {REMOTE_DIR} && chmod +x scripts/bootstrap_fresh_pi.sh && echo '{PASS}' | sudo -S bash scripts/bootstrap_fresh_pi.sh"
        
        stdin, stdout, stderr = ssh.exec_command(bootstrap_cmd, get_pty=True)
        
        # Stream the output
        while True:
            line = stdout.readline()
            if not line:
                break
            print(f"[PI] {line.strip()}")
            
        # 4. Final check
        print("\n--- DEPLOY COMPLETED ---")
        print("The system has been configured. The Pi will now reboot to apply hardware changes.")
        ssh.exec_command(f"echo '{PASS}' | sudo -S reboot")
        print("Rebooting... Wait 30-60 seconds for the app to start.")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    full_bootstrap_deploy()
