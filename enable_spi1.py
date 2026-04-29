import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.204', username='dani', password='26021980')

# Add SPI1 overlay
cmd = 'echo 26021980 | sudo -S bash -c "echo dtoverlay=spi1-3cs >> /boot/firmware/config.txt"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('stdout:', stdout.read().decode('utf-8', errors='replace'))
print('stderr:', stderr.read().decode('utf-8', errors='replace'))

# Verify
stdin, stdout, stderr = ssh.exec_command('cat /boot/firmware/config.txt | grep spi')
print('SPI config:', stdout.read().decode('utf-8', errors='replace'))

# Reboot
stdin, stdout, stderr = ssh.exec_command('echo 26021980 | sudo -S reboot')
print('Rebooting...')

ssh.close()
