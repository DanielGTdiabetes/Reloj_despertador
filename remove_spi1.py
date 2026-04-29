import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.204', username='dani', password='26021980')

# Remove spi1 overlay
cmd = 'echo 26021980 | sudo -S sed -i "/dtoverlay=spi1-3cs/d" /boot/firmware/config.txt'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('Removed spi1 overlay')

# Verify
stdin, stdout, stderr = ssh.exec_command('cat /boot/firmware/config.txt | grep -i spi')
print('SPI config:', stdout.read().decode('utf-8', errors='replace').strip())

# Reboot
stdin, stdout, stderr = ssh.exec_command('echo 26021980 | sudo -S reboot')
print('Rebooting...')

ssh.close()
