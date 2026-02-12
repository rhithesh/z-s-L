import sounddevice as sd
import numpy as np
import queue, time
from silero_vad import load_silero_vad, get_speech_timestamps
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
WINDOW_SIZE = int(SAMPLE_RATE * 1.5)  # 1.5 second window for VAD
SILENCE_TIMEOUT = 0.5

q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(indata.copy())

def mic_stream(device_index):
    with sd.InputStream(
        samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
        channels=1, dtype="float32", callback=callback, device=device_index
    ):
        print("🎤 Listening...")
        while True:
            yield q.get()

model = WhisperModel("base.en", device="cpu", compute_type="int8")
vad_model = load_silero_vad()

def transcribe_realtime(device_index):
    vad_buffer = np.array([], dtype=np.float32)  # Sliding window for VAD
    speech_buffer = np.array([], dtype=np.float32)  # Accumulates all speech
    last_voice_time = time.time()
    speaking = False

    for chunk in mic_stream(device_index):
        # Flatten chunk to ensure 1D array
        chunk_flat = chunk.flatten()
        
        # Add to VAD buffer (sliding window)
        vad_buffer = np.append(vad_buffer, chunk_flat)
        if len(vad_buffer) > WINDOW_SIZE:
            vad_buffer = vad_buffer[-WINDOW_SIZE:]

        # Convert to int16 for VAD
        audio_int16 = (vad_buffer * 32767).astype(np.int16)
        
        # Ensure it's a 1D array
        if audio_int16.ndim == 0:
            audio_int16 = np.array([audio_int16])
        elif audio_int16.ndim > 1:
            audio_int16 = audio_int16.flatten()

        timestamps = get_speech_timestamps(audio_int16, vad_model, sampling_rate=SAMPLE_RATE)
        
        has_speech = len(timestamps) > 0
        
        if has_speech:
            # If just started speaking, clear old speech buffer
            if not speaking:
                print("🎤 Speech detected, recording...")
                speech_buffer = np.array([], dtype=np.float32)
                speaking = True
            
            # Accumulate ALL audio while speaking
            speech_buffer = np.append(speech_buffer, chunk_flat)
            last_voice_time = time.time()
        
        # Check for silence after speech
        if speaking and not has_speech and time.time() - last_voice_time > SILENCE_TIMEOUT:
            speaking = False
            
            print(f"Transcribing... ({len(speech_buffer)/SAMPLE_RATE:.1f}s of audio)")
            
            if len(speech_buffer) > 0:
                try:
                    # Convert accumulated speech to int16 then float32 for Whisper
                    speech_int16 = (speech_buffer * 32767).astype(np.int16)
                    audio_float = speech_int16.astype(np.float32) / 32767.0
                    
                    segments, _ = model.transcribe(audio_float)
                    text = "".join([s.text for s in segments]).strip()
                    
                    if text:
                        print("🎤 Final:", text)
                    else:
                        print("(no speech detected)")
                        
                except Exception as e:
                    print(f"Transcription error: {e}")
                    import traceback
                    traceback.print_exc()

            # Reset buffers
            speech_buffer = np.array([], dtype=np.float32)
            vad_buffer = np.array([], dtype=np.float32)
            print("\n🎤 Listening again...\n")


if __name__ == "__main__":
    transcribe_realtime(device_index=1)