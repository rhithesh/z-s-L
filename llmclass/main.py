


import threading
import requests
from scipy.io import wavfile
from scipy.signal import resample_poly
import numpy as np
import time
from config.constants import SYSTEMPROMPT
from parentClass.main import DMSLMMain
import wave
import  sounddevice as sd
import numpy as np





#__init__() → initializes variables and launches analyze_llm_call_need() in a background thread.
#analyze_llm_call_need() → continuously reads eye-state frames from processdImageJsonQueue, counts closed-eye streaks, and triggers LLM when threshold is reached.
#add more sofisticated logic to when call the llm
#Rename the class LLMTrigger    



class LLMClass(DMSLMMain):
    """A class which keeps analyzing the current input whether the drivers eyes are open or closed and over time if the speaker is attentive it speaks to it normally."""


    
    def play_wav(self,filename,time_of_file):
        #print("*****************************************")
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
            #self.main.piper_audio_queue.put(**audio)
            self.main.piper_audio_queue.put(frames)
            self.main.piper_audio_queue.put(b"__TTS_END__")
            time.sleep(time_of_file)


            # if n_channels > 1:
            #     audio = audio.reshape(-1, n_channels)

            # sd.stop()
            # sd.play(audio, samplerate=sample_rate)
            # sd.wait()



    
    
    def clear_queue_and_stop(q, num_consumers):
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass

        for _ in range(num_consumers):
            q.put(None)


    def __init__(self,main):



        self.fail_rate=0
        self.main=main
        self.closed_counter=0
        self.stoper=1
        # self.sr, self.data = wavfile.read("/media/nvme/Hithesh/DMSLM/llmclass/drowwake.wav")
        # self.alert_audio = self.load_wav_48k("/media/nvme/Hithesh/DMSLM/llmclass/alert.wav")
        # # self.drow_audio = self.load_wav_48k("/media/nvme/Hithesh/DMSLM/llmclass/drowwake.wav")
        # self.emergency_audio = self.load_wav_48k("/media/nvme/Hithesh/DMSLM/llmclass/emergencyvoice.wav")



        # if self.data.dtype != np.float32:
        #     self.data =self.data.astype(np.float32) / np.max(np.abs(self.data))
        self.drow_event_time=[]
        threading.Thread(target=self.analyze_llm_call_need, daemon=True).start()



    def analyze_llm_call_need(self):
        print("Started analyze LLM Function")
        
        while True:
            try:

                obj = self.main.processdImageJsonQueue.get()
                left = obj["left_eye"]
                right = obj["right_eye"]
                #print(left,right,self.closed_counter)
                if left == "closed" and right == "closed":
                    self.closed_counter += 1
                    self.main.event_queue.put({"closed_counter":self.closed_counter})
                else:
                    self.closed_counter = 0
                #print({"fail_rate":self.fail_rate,"user_can_speak":self.main.UserCanSpeak,"Session_Active":self.main.session,"last_active_time":self.main.last_active_time})


                # if self.fail_rate>=4 and self.main.session==False:
                #     self.fail_rate=0
                #     #clear_queue_and_stop(self.main.textOutputQueue,100)
                #     self.main.last_active_time=time.time()
                #     self.play_wav("/media/nvme/Hithesh/DMSLM/llmclass/emergencyvoice.wav",5)
                #     print("SOS PLAYED")

                    
                
                    
                
                if self.closed_counter >= 10 and not self.main.session:
                    
                    try:

                        self.fail_rate= self.fail_rate+1
                        self.main.UserCanSpeak=False
                        print("___________________ Drowsenes Detected __________________")
                        print("___________________ Session-Activated ___________________")

                        if self.fail_rate>=3 and self.main.session==False:
                            self.fail_rate=0
                            #clear_queue_and_stop(self.main.textOutputQueue,100)
                            self.main.last_active_time=time.time()
                            self.play_wav("/media/nvme/Hithesh/DMSLM/llmclass/emergencyvoice.wav",10.7)
                            print("SOS PLAYED")

                        else:

                            #make sure to stay here until complete audio is played look at .wav file
                            #it is expected 
                            self.play_wav("/media/nvme/Hithesh/DMSLM/llmclass/drowwake.wav",9)
                        self.main.last_active_time=time.time()

                        
                        self.main.messages=[]
                        self.main.messages.append(SYSTEMPROMPT)
                        self.main.messages.append({"role":"assistant","content":"Hey you seem to be drowsy do you want me to play a song or call a friend? Let me know."})
                        self.main.session=True
                        self.main.UserCanSpeak=True
                        self.main.event_queue.put({"llm_Status":"active"})
                        

                    except Exception as e:
                        print("Error Playing a file:", e)
                
            except Exception as e:
                print("Error in analyze_llm_call_need:", e)
                continue

    
        

                        # content = "CAR:ALERT THE DRIVER HE SEEMS TO BE DROWSY"
                        # url = "http://127.0.0.1:8001/message"
                        # response = requests.post(url,json=content)
                        # result= response.json()
                        # if response.status_code!=200:
                        #     print("ERROR")
                        #     print(f"API Error {response.status_code}: {response.reason}")

                        # if self.main.messages:
                           # self.main.messages.extend(messages)



        
        

    
