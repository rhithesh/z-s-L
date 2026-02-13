import os
import sys
import logging

import time
from config.constants import SYSTEMPROMPT
from scipy.io import wavfile
import sounddevice as sd

import queue
import time
import threading
import json
import numpy as np
import wave
import numpy as np
import requests

#
# def watch_text_queue(q, name="TEXT"):
#     last = -1
#     while True:
#         size = q.qsize()
#         if size != last:
#             print(f"[{name} QUEUE] size = {size}")
#             last = size
#         time.sleep(0.05)


#this is for debuging we use this to se what is going inside and outside the queue in real time
class DebugQueue(queue.Queue):
    def put(self, item, *args, **kwargs):
        print(f"[QUEUE PUT] {item!r}")
        super().put(item, *args, **kwargs)

    def get(self, *args, **kwargs):
        item = super().get(*args, **kwargs)
        print(f"[QUEUE GET] {item!r}")
        return item

#No Changes required 
class  DMSLMMain():




    def __init__(self):
        
        self.FRAME_HEIGHT = 480
        self.FRAME_WIDTH = 640
        self.FRAME_CHANNELS = 3
        self.RING_BUFFER_SIZE = 3
        self.sr, self.data = wavfile.read("/media/nvme/Hithesh/DMSLM/helper/End_of_Session.wav")



        self.shared_frames=np.zeros(
            (self.RING_BUFFER_SIZE,
             self.FRAME_HEIGHT,
             self.FRAME_WIDTH,
             self.FRAME_CHANNELS),
            dtype=np.uint8
        )

        
        self.UserCanSpeak=True
        self.messages=[SYSTEMPROMPT]
        self._last_messages_count=0

        self.imageQueue=queue.Queue()
        self.processdImageJsonQueue=queue.Queue()
        
        self.textOutputQueue=queue.Queue()
        
        
        
        self.event_queue=queue.Queue()

        #udp
        self.Dataqueue=queue.Queue()

        self.piper_audio_queue=queue.Queue()
        
        self.toolResponseCacheq=queue.Queue()
        self.last_active_time=time.time() - 50
        self.session=False
        self.clearCacheOnEndOfSession()
        
        
        self.audio_player_thread = threading.Thread(
            target=self._main_play_audio, daemon=True
        )
        self.audio_player_thread.start()

        threading.Thread(target=self.display_queue, daemon=True).start()
#         threading.Thread(
#     target=watch_text_queue,
#     args=(self.textOutputQueue, "TEXT"),
#     daemon=True
# ).start()






    def display_queue(self):
        """ This method is used to monitor the session and end it if there is no activity for 7 seconds, This is run as a thread on line 94"""

        print("Starting display queue thread...")
        while True:
            
          #print("Session-Active",self.session)
          #print("User-Can-Speak",self.UserCanSpeak)
          #print(time.time() - self.last_active_time )
          
          #if session is true and no activity for 7 seconds then end the session and play the end of session audio
          if self.session and time.time() - self.last_active_time > 7:
                sd.stop()
                sd.play(self.data, self.sr)
                sd.wait()   
                print("--------- END   OF  SESSION --------")


                self.clearCacheOnEndOfSession()                   
                self.session = False  
                self.last_active_time=time.time() 
               

    def enable_session_nd_mic(self):
      """ This is a public method is used to enable the session and mic"""
      self.last_active_time=time.time() 
      self.UserCanSpeak=True
      self.messages=[]
      self.messages.append(SYSTEMPROMPT)
      self.session=True

    # @staticmethod
    # def play_wav(filename):

  

    #     with wave.open(filename, 'rb') as wf:
    #         sample_rate = wf.getframerate()
    #         n_channels = wf.getnchannels()
    #         frames = wf.readframes(wf.getnframes())

    #         dtype = {
    #             1: np.int8,
    #             2: np.int16,
    #             4: np.int32
    #         }[wf.getsampwidth()]

    #         audio = np.frombuffer(frames, dtype=dtype)

    #         if n_channels > 1:
    #             audio = audio.reshape(-1, n_channels)

    #         sd.stop()
    #         sd.play(audio, samplerate=sample_rate)
    #         sd.wait()

    def _main_play_audio(self):
        speaking = False
        

        stream = sd.OutputStream(
            samplerate=22050,
            channels=1,
            dtype="int16",
            blocksize=0
        )
        stream.start()

        while True:
            try:
                audio_bytes = self.piper_audio_queue.get(timeout=0.1)
                

                if audio_bytes == b"__TTS_END__":
                    speaking = False
                    self.UserCanSpeak = True
                    continue

                if not speaking:
                    self.UserCanSpeak = False
                    speaking = True
                

                audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
                stream.write(audio_np)
                self.last_active_time=time.time()


            except queue.Empty:
                continue

            except Exception as e:
                print("Playback error:", e)

        stream.stop()
        stream.close()


    def clearCacheOnEndOfSession(self):
        """ This method clears the llm token cache. It is  important to clear the cache on end of every session,
          so it is like a new conversation with a new context"""

        request_url="http://127.0.0.1:5000/clear-history"


        print("Cleared the llm cache")
        try:
            response=requests.post(request_url,json="")
            if response.status_code==200:
                print("Cache cleared sucessfully")
        except Exception as e:
            print("failed to clear cache")







    
    


        








