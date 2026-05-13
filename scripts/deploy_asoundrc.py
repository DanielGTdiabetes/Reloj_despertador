"""Deploy .asoundrc to Pi for stereo→mono mix on the USB sound card."""
import paramiko

PI_HOST = "192.168.0.204"
PI_USER = "dani"
PI_PASS = "26021980"

# Routes both stereo channels to a single mono output so one speaker works
# regardless of which jack (L or R) it is connected to.
ASOUNDRC = """\
pcm.ugreen_route {
    type route
    slave.pcm "plughw:2,0"
    slave.channels 2
    ttable.0.0 1.0
    ttable.0.1 1.0
    ttable.1.0 1.0
    ttable.1.1 1.0
}

pcm.ugreen {
    type plug
    slave.pcm "ugreen_route"
}

ctl.ugreen {
    type hw
    card 2
}

pcm.!default {
    type plug
    slave.pcm "ugreen"
}
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(PI_HOST, username=PI_USER, password=PI_PASS, timeout=10)

sftp = client.open_sftp()
with sftp.open("/home/dani/.asoundrc", "w") as f:
    f.write(ASOUNDRC)
sftp.close()

# Verify
_, out, _ = client.exec_command("cat ~/.asoundrc")
print(out.read().decode())

# Quick smoke test: play beep via the mono device
_, out, err = client.exec_command(
    "aplay -D ugreen /home/dani/reloj_despertador/src/assets/sounds/beep.wav 2>&1"
)
result = out.read().decode() + err.read().decode()
print("aplay test:", result if result else "OK (no error output)")

client.close()
print("Done.")
