
import wave
import struct
import math
import os

def generate_marimba_alarm(filepath):
    """Tonos ascendentes estilo marimba — suave, alegre, ideal para despertar a niños."""
    sample_rate = 44100
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

    # Escala Do mayor: Do Re Mi Fa Sol La Si Do
    note_freqs = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]
    note_dur   = 0.35   # segundos por nota
    gap_dur    = 0.04   # silencio entre notas
    repeats    = 3      # veces que se repite la escala
    pause_dur  = 0.6    # pausa entre repeticiones

    def make_note(freq, duration):
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            # Marimba: fundamental + 2º armónico suave
            val = math.sin(2 * math.pi * freq * t) + 0.18 * math.sin(2 * math.pi * freq * 2 * t)
            # Envolvente: ataque rápido (5 ms) + caída exponencial (percusión)
            attack = min(t / 0.005, 1.0)
            decay  = math.exp(-4.5 * t / duration)
            sample = int(val * attack * decay * 0.55 * 32767)
            samples.append(struct.pack('<h', sample))
        return samples

    def make_silence(duration):
        n = int(sample_rate * duration)
        return [struct.pack('<h', 0)] * n

    all_samples = []
    for _ in range(repeats):
        for freq in note_freqs:
            all_samples += make_note(freq, note_dur)
            all_samples += make_silence(gap_dur)
        all_samples += make_silence(pause_dur)

    with wave.open(filepath, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for s in all_samples:
            f.writeframesraw(s)

    print(f"Sound generated at {filepath} ({os.path.getsize(filepath)} bytes)")


if __name__ == "__main__":
    generate_marimba_alarm(r"d:\Reloj_despertador\src\assets\alarm.wav")
