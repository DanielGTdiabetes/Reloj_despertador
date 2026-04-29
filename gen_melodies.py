import wave, struct, math, os

def gen(fp, notes):
    sr = 44100
    samples = []
    for freq, dur in notes:
        n = int(sr * dur)
        fi = int(sr * 0.02)
        fo = int(sr * 0.05)
        for i in range(n):
            t = i / sr
            env = i/fi if i < fi else ((n-i)/fo if i > n-fo else 1.0)
            samples.append(int(20000 * env * math.sin(2 * math.pi * freq * t)))
        samples.extend([0] * int(sr * 0.05))
    os.makedirs(os.path.dirname(os.path.abspath(fp)), exist_ok=True)
    with wave.open(fp, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for s in samples:
            wf.writeframes(struct.pack("<h", s))
    print("OK:", fp)

base = "src/assets/sounds"
gen(base+"/melody1.wav", [(523.25,0.25),(659.25,0.25),(783.99,0.25),(1046.50,0.35),(783.99,0.25),(659.25,0.25)])
gen(base+"/melody2.wav", [(523.25,0.3),(783.99,0.3),(659.25,0.3),(1046.50,0.4),(659.25,0.3),(783.99,0.3)])
gen(base+"/melody3.wav", [(523.25,0.15),(659.25,0.15),(783.99,0.15),(659.25,0.15),(783.99,0.15),(1046.50,0.15),(880,0.15),(1046.50,0.4)])
print("Done!")
