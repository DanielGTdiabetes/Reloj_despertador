"""Full diagnosis of the rectangular display."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import paramiko

HOST = "192.168.0.204"
USER = "dani"
PASS = "26021980"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

# 1. Check actual config on Pi
print("=== 1. Config on Pi (offsets) ===")
stdin, stdout, stderr = ssh.exec_command(
    'python3 -c "import json; c=json.load(open(\'/home/dani/reloj_despertador/config/config.json\')); r=c[\'displays\'][\'rect\']; print(f\\"col_offset={r.get(\'col_offset\')}, row_offset={r.get(\'row_offset\')}, bl_pin={r.get(\'bl_pin\')}, cs_pin={r.get(\'cs_pin\')}, dc_pin={r.get(\'dc_pin\')}, rst_pin={r.get(\'rst_pin\')}\\") "'
)
print(stdout.read().decode())
print(stderr.read().decode())

# 2. Stop service, then test display directly
print("=== 2. Stopping service ===")
stdin, stdout, stderr = ssh.exec_command(f'echo {PASS} | sudo -S systemctl stop reloj.service 2>&1')
print(stdout.read().decode())

# 3. Full display test with explicit GPIO control
print("=== 3. Direct display test ===")
test_script = '''
import time
import RPi.GPIO as GPIO
import spidev

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

CS=7; DC=22; RST=27; BL=23
for p in [CS, DC, RST, BL]:
    GPIO.setup(p, GPIO.OUT)

# Reset
GPIO.output(CS, GPIO.HIGH)
GPIO.output(BL, GPIO.HIGH)  # off initially
GPIO.output(RST, GPIO.HIGH); time.sleep(0.01)
GPIO.output(RST, GPIO.LOW);  time.sleep(0.01)
GPIO.output(RST, GPIO.HIGH); time.sleep(0.12)

spi = spidev.SpiDev()
spi.open(0, 1)
spi.max_speed_hz = 4000000
spi.mode = 0
try:
    spi.no_cs = True
except:
    pass

def cmd(c):
    GPIO.output(DC, GPIO.LOW)
    GPIO.output(CS, GPIO.LOW)
    spi.writebytes([c])
    GPIO.output(CS, GPIO.HIGH)

def data(d):
    GPIO.output(DC, GPIO.HIGH)
    GPIO.output(CS, GPIO.LOW)
    if isinstance(d, int):
        spi.writebytes([d])
    else:
        spi.writebytes(list(d))
    GPIO.output(CS, GPIO.HIGH)

def cmd_data(c, d=None):
    cmd(c)
    if d is not None:
        data(d)

# Init sequence
cmd_data(0x01); time.sleep(0.15)  # SWRESET
cmd_data(0x11); time.sleep(0.12)  # SLPOUT

cmd_data(0x36, [0xA8])  # MADCTL
cmd_data(0x3A, [0x05])  # COLMOD RGB565

cmd_data(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33])  # PORCTRL
cmd_data(0xB7, [0x35])  # GCTRL
cmd_data(0xBB, [0x2B])  # VCOMS
cmd_data(0xC0, [0x0C])  # LCMCTRL
cmd_data(0xC2, [0x01])  # VDVVRHEN
cmd_data(0xC3, [0x15])  # VRHS
cmd_data(0xC4, [0x20])  # VDVSET
cmd_data(0xC6, [0x0F])  # FRCTR2
cmd_data(0xD0, [0xA4, 0xA1])  # PWCTRL1

cmd_data(0x21)  # INVON
cmd_data(0x13)  # NORON
cmd_data(0x29)  # DISPON
time.sleep(0.1)

# Set window: recovered physical orientation, col_offset=82, row_offset=18
W, H = 284, 76
co, ro = 82, 18
xs, xe = co, co + W - 1
ys, ye = ro, ro + H - 1
cmd_data(0x2A, [xs >> 8, xs & 0xFF, xe >> 8, xe & 0xFF])
cmd_data(0x2B, [ys >> 8, ys & 0xFF, ye >> 8, ye & 0xFF])

# Fill with bright RED
cmd(0x2C)
buf = bytearray(W * H * 2)
for i in range(0, len(buf), 2):
    # Red in RGB565 = 0xF800
    buf[i] = 0xF8
    buf[i+1] = 0x00

GPIO.output(DC, GPIO.HIGH)
GPIO.output(CS, GPIO.LOW)
spi.writebytes2(buf)
GPIO.output(CS, GPIO.HIGH)

print("Frame sent. Turning BL on...")

# Try BL LOW (active low)
GPIO.output(BL, GPIO.LOW)
time.sleep(1)
print("BL=LOW (should be on if active-low)")

# Also try BL HIGH in case it's active high
# GPIO.output(BL, GPIO.HIGH)
# time.sleep(1)
# print("BL=HIGH")

print("Test done. Screen should show solid RED.")
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{test_script}"', timeout=30)
print("OUT:", stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)

print("\n=== 4. Restarting service ===")
stdin, stdout, stderr = ssh.exec_command(f'echo {PASS} | sudo -S systemctl start reloj.service 2>&1')
print(stdout.read().decode())

ssh.close()
print("Done. Check if you see RED on the rectangular screen.")
