import sounddevice as sd
import numpy as np
import queue
import time
import threading
import requests
import tempfile
import os
import wave
import asyncio
import requests
import difflib
import time
from config.constants import SYSTEMPROMPT
import time

from parentClass.main import DMSLMMain


class VoiceInput(DMSLMMain):
    def __init__(self, main, device_index=None, device_name_hint=None):
        self.main = main
        self.wakeWords=["Hey Friend","Hello Friend ","Hi Friend","Heyy friend"]


        # ---------------- Audio config ---------------- #
        self.SAMPLE_RATE = 48000
        self.BLOCK_SIZE = 2048
        self.SILENCE_TIMEOUT = 0.7

        self.RMS_THRESHOLD = 0.015     # tune per mic
        self.MIN_SPEECH_SEC = 0.30     # ignore short noise

        self.transcription_api_url = "http://127.0.0.1:5000/v1/audio/transcriptions"
        self.transcription_language = "en"

        self.audio_queue = queue.Queue()
        self.speech_buffer = np.array([], dtype=np.float32)

        self.last_voice_time = time.time()
        self.speaking = False
        self.stop_event = threading.Event()


        self.device_index = 0

        self.listener_thread = threading.Thread(
            target=self._listen, daemon=True
        )
        self.listener_thread.start()
    
    def wakeWorDetector(self,text):
        

        matches=difflib.get_close_matches(text, self.wakeWords, n=1, cutoff=0.6)

        return bool(matches)






    def _rms(self, audio: np.ndarray) -> float:
        return np.sqrt(np.mean(audio ** 2))


    def _resolve_device_index(self, device_index, name_hint):
        try:
            devices = sd.query_devices()
        except Exception as e:
            print(f"Device query failed: {e}")
            return None

        # 1️⃣ Explicit index
        if device_index is not None:
            try:
                sd.check_input_settings(
                    device=device_index,
                    samplerate=self.SAMPLE_RATE,
                    channels=1,
                )
                print(f"Using device index {device_index}")
                return device_index
            except Exception:
                pass

        # 2️⃣ Name hint
        if name_hint:
            for idx, dev in enumerate(devices):
                if name_hint.lower() in dev["name"].lower():
                    try:
                        sd.check_input_settings(
                            device=idx,
                            samplerate=self.SAMPLE_RATE,
                            channels=1,
                        )
                        print(f"Using device '{dev['name']}' (index {idx})")
                        return idx
                    except Exception:
                        continue

        print("Using default input device")
        return None

    # ---------------- Audio I/O ---------------- #

    def _audio_callback(self, indata, frames, time_info, status):
        if not getattr(self.main, "UserCanSpeak", True):
            return

        if status:
            print(f"Audio status: {status}")

        try:
            self.audio_queue.put_nowait(indata.copy())
        except queue.Full:
            pass

    def _listen(self):
        print("🎤 Voice input started")

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.BLOCK_SIZE,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
            device=self.device_index,
        ):
            while not self.stop_event.is_set():
                if not getattr(self.main, "UserCanSpeak", True):
                    self._clear_audio_state()
                    #self.last_active_time=time.time()
                    time.sleep(0.2)
                    continue

                try:
                    chunk = self.audio_queue.get(timeout=0.1)
                    self._process_audio_chunk(chunk)

                except queue.Empty:
                    if (
                        self.speaking
                        and time.time() - self.last_voice_time
                        > self.SILENCE_TIMEOUT
                    ):
                        self._transcribe_and_send()

                except Exception as e:
                    print("Listen loop error:", e)

    # ---------------- RMS Speech Detection ---------------- #

    def _process_audio_chunk(self, chunk):
        chunk_flat = chunk.flatten()
        rms = self._rms(chunk_flat)
        # if time.time() - self.last_voice_time > 5:
        #     #exit
        
        if rms > self.RMS_THRESHOLD:
            #user is talking
            #Stop the Timer
            if not self.speaking:
                print("Speech detected (RMS)")
                self.speaking = True
                self.speech_buffer = np.array([], dtype=np.float32)

            self.speech_buffer = np.append(self.speech_buffer, chunk_flat)
            self.last_voice_time = time.time()
            #self.last_active_time=time.time()

        elif self.speaking:
            self.main.last_active_time=time.time()
            if time.time() - self.last_voice_time > self.SILENCE_TIMEOUT:


                duration = len(self.speech_buffer) / self.SAMPLE_RATE
                if duration >= self.MIN_SPEECH_SEC:

                    self._transcribe_and_send()
                else:
                    print("Ignored short noise")
                    self._clear_audio_state()

    # ---------------- Transcription + LLM ---------------- #

    def _transcribe_and_send(self):
        print("Processing transcription...")
        self.speaking = False
        duration = len(self.speech_buffer) / self.SAMPLE_RATE
        print(f"Transcribing ({duration:.1f}s)")

        if len(self.speech_buffer) == 0:
            self._clear_audio_state()
            return

        try:
            # Convert float32 → PCM16
            audio_int16 = np.clip(
                self.speech_buffer * 32767,
                -32768,
                32767,
            ).astype(np.int16)

            # Write temp WAV (stdlib only)
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp_path = tmp.name

            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())

            # Call transcription API
            with open(tmp_path, "rb") as audio_file:
                files = {"file": audio_file}
                data = {"language": self.transcription_language}
                print(files)




                response = requests.post(
                    self.transcription_api_url,
                    files=files,
                    data=data,
                    timeout=30,
                )

            os.remove(tmp_path)

            if response.status_code != 200:
                print("Transcription API error:", response.text)
                self._clear_audio_state()
                return

            result = response.json()

            # Adjust if your API response format differs
            text = (
                result.get("text")
                or result.get("transcription")
                or ""
            ).strip()

            if not text:
                print("(empty transcription)")
                self._clear_audio_state()
                return

            print("User said:", text)

            wakeOut=self.wakeWorDetector(text)
            print({"Wakeword":wakeOut})
            now=time.time()

            print(now-self.main.last_active_time>5,"crossed 5 second")



            # if wakeOut and not self.main.session:
            #     self.main.last_active_time=time.time()
            #     print("Hi Friend wake-word detected, I shall start a conversation")
            #     self.main.session=True
            #     #print("Session-Active",self.main.session)
                
            #     if not hasattr(self.main, "messages"):
            #         self.main.messages = [
            #            SYSTEMPROMPT
            #         ]
            # elif self.main.session:
            #     self.main.last_active_time = now

            if self.main.session:
                self.main.last_active_time = now
            elif wakeOut:
                print("Hi Friend wake-word detected, I shall start a conversation")

                self.main.last_active_time=time.time()
                self.main.session=True

                if not hasattr(self.main, "messages"):
                    self.main.messages = [
                       SYSTEMPROMPT
                    ]

                




            

            if self.main.session:
                self.main.messages.append(
                    {"role": "user", "content": text}
                )

                url = "http://127.0.0.1:8001/message"
                response = requests.post(url,json=text)
                print(response.status_code)
                
                    


             





            # from server import helper
            # asyncio.run(helper.chatLLM(self.main.messages))


        except Exception as e:
            print("Transcription error:", e)

        finally:
            self._clear_audio_state()
            print("Ready for next input\n")


    def _clear_audio_state(self):
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
        self.speech_buffer = np.array([], dtype=np.float32)
        self.speaking = False

    def stop(self):
        print("Stopping voice input")
        self.stop_event.set()
        self.listener_thread.join(timeout=2)
        self._clear_audio_state()
