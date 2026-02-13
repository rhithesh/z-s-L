from parentClass.main import DMSLMMain
import re
import numpy as np
import threading
import queue
import requests
from config.constants import voice_message
import json
import time
from time import perf_counter
import time
import sounddevice as sd


# textOutputQueue → _process_text → HTTP TTS
# → audio_queue → _play_audio → speakers


class PiperTTS(DMSLMMain):

    def __init__(self, main):
        self.main = main

        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()

        self.TTS_URL = "http://127.0.0.1:5000/v1/audio/speech"

        # Start text processor
        self.text_processor_thread = threading.Thread(
            target=self._process_text, daemon=True
        )
        self.text_processor_thread.start()

        # Start audio playback
        # self.audio_player_thread = threading.Thread(
        #     target=self._play_audio, daemon=True
        # )
        # self.audio_player_thread.start()

    # ---------------- Text Processing ---------------- #

    def _process_text(self):
        buffer = ""
        sentence_re = re.compile(r"(.+?[.!?])")

        while not self.stop_event.is_set():
            try:
                chunk = self.main.textOutputQueue.get(timeout=0.1)

                if chunk is None:
                    if buffer.strip():
                        self._tts_request(buffer.strip())
                    buffer = ""
                    continue

                if not isinstance(chunk, str):
                    continue

                buffer += chunk

                while True:

                    match = sentence_re.search(buffer)
                    start= time.time()
                    if not match:                        
                        break
                    end=time.time()
                    print("Time to search for a sentence",end-start)

                    sentence = match.group(1).strip()

                    #print("[TTS]", sentence)
                    buffer = buffer[len(match.group(1)):]

                    self._tts_request(sentence)

            except queue.Empty:
                continue
            except Exception as e:
                print("Text processing error:", e)

    # ---------------- HTTP TTS ---------------- #

    def _tts_request(self, text):
        try:
            voice=voice_message
            voice["request"]["parameters"]["chunks"]=text
            self.main.Dataqueue.put(json.dumps(voice).encode("utf-8"))
            start=time.perf_counter()

            payload = {
                "input": text,
                "voice": "default",
                "language": "en",
                "response_format": "pcm"
            }

            with requests.post(
                self.TTS_URL,
                json=payload,
                stream=True,
                timeout=30
            ) as r:




                r.raise_for_status()
                print("TTS",text)

                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        self.main.piper_audio_queue.put(chunk)
                        self.main.last_active_time=time.time()

                self.main.piper_audio_queue.put(b"__TTS_END__")
                end=perf_counter()
                print("Time for pipering on sentence",start-end)

        except Exception as e:
            print("TTS request error:", e)

    # ---------------- Audio Playback ---------------- #

    # def _play_audio(self):
    #     speaking = False
        

    #     stream = sd.OutputStream(
    #         samplerate=22050,
    #         channels=1,
    #         dtype="int16",
    #         blocksize=0
    #     )
    #     stream.start()

    #     while not self.stop_event.is_set():
    #         try:
    #             audio_bytes = self.audio_queue.get(timeout=0.1)
                

    #             if audio_bytes == b"__TTS_END__":
    #                 speaking = False
    #                 self.main.UserCanSpeak = True
    #                 continue

    #             if not speaking:
    #                 self.main.UserCanSpeak = False
    #                 speaking = True
                

    #             audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
    #             print("*********************************************")
    #             stream.write(audio_np)
    #             self.main.last_active_time=time.time()


    #         except queue.Empty:
    #             print("Queue /////")
    #             continue

    #         except Exception as e:
    #             print("Playback error:", e)

    #     stream.stop()
    #     stream.close()



    # ---------------- Cleanup ---------------- #

    def finish(self):
        self.stop_event.set()

        self.main.textOutputQueue.put(None)
        self.text_processor_thread.join()

        self.main.piper_audio_queue.put(None)
        self.audio_player_thread.join()
