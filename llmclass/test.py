import sounddevice as sd
import wave
import numpy as np
import sys


def play_wav(filename):
    with wave.open(filename, 'rb') as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        frames = wf.readframes(wf.getnframes())

        dtype = {
            1: np.int8,
            2: np.int16,
            4: np.int32
        }[wf.getsampwidth()]

        audio = np.frombuffer(frames, dtype=dtype)

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels)

        sd.play(audio, samplerate=sample_rate)
        sd.wait()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python play_wav.py <file.wav>")
        sys.exit(1)

    play_wav(sys.argv[1])
