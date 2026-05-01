
import wave
import struct
import math
import os

def generate_premium_alarm(filepath):
    sample_rate = 44100
    duration = 4.0
    num_samples = int(sample_rate * duration)
    
    # Abrir archivo wave
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, 'w') as f:
        f.setnchannels(1) # Mono
        f.setsampwidth(2) # 16-bit
        f.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # Acorde armónico (La Mayor)
            val = (math.sin(2 * math.pi * 440 * t) + 
                   math.sin(2 * math.pi * 554 * t) * 0.5 + 
                   math.sin(2 * math.pi * 659 * t) * 0.3)
            
            # Envolvente (Fade in/out)
            env = min(t / 1.0, 1.0) * min((duration - t) / 0.5, 1.0)
            
            # Escalar a 16-bit
            sample = int(val * env * 0.5 * 32767)
            f.writeframesraw(struct.pack('<h', sample))
            
    print(f"Sound generated at {filepath}")

if __name__ == "__main__":
    generate_premium_alarm(r"d:\Reloj_despertador\src\assets\alarm.wav")
