import os
import sys
import logging


import time
import requests
import json
import os
from parentClass.main import DMSLMMain
from mcpclass.MCPClient import MCPClient
import asyncio
from config.constants import voice_message
import wave
import numpy as np





class Helper(DMSLMMain):
    def __init__(self, main):
        self.main = main

        self.url = "http://127.0.0.1:5000/v1/chat/completions"
        self.model = "google/gemma-3-12b-it"
        self.mcp_client= MCPClient()
        self.mcp = None  # MCP client (singleton)
        self.main.textOutputQueue.put("Sima Powered Up!")

    def _play_wav(self,filename,time_of_file):
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


        

    
    def extract_tool_block(self, response: str):
        if not response.startswith("Tool:"):
            return None, None

        lines = response.splitlines()
        tool_name = lines[0].replace("Tool:", "").strip()
        args = {}

        for line in lines[1:]:
            line = line.strip()

            if not line:
                continue

            if line == "ARGS:":
                continue

            if line.startswith("TEXT:"):
                break

            if ":" in line:
                key, value = line.split(":", 1)
                args[key.strip()] = value.strip()

        return tool_name, args

    async def start_mcp():


        if self.mcp_client.session is None:
            await self.mcp_client.connect_to_server("mcpclass/main.py")






        
    async def tool_check_CALL(self, full_response: str):
        print("=== TOOL CHECK CALLED ===")
    
        # if not full_response.startswith("Tool:"):
        #     print("Response doesn't start with 'Tool:', exiting")
        #     return
        print("Getting MCP instance...")
        # print(full_response)
        try:
            if self.mcp_client.session is None:
                print("None")
                await self.mcp_client.connect_to_server("mcpclass/main.py")
            
            print("THIS IS FULL RESPONSE")
            
            
            tool_name= full_response
            # print("tool_name:",tool_name,"ARGS:",args)
            try:
                result = await self.mcp_client.session.call_tool(tool_name, {})
                print("RAW MCP RESULT:", result)
                print("CONTENT:", result.content)
                #Play alert sound
                self.main.session=False

                self._play_wav("/media/nvme/Hithesh/DMSLM/helper/End_of_Session.wav",1)
                print("--------- END   OF  SESSION --------")

                self.main.clearCacheOnEndOfSession()

                
                self.main.UserCanSpeak=True
                payload = json.loads(result.content[0].text)
                print("Hithesh",json.dumps(payload["event_udp"]).encode("utf-8"))
                self.main.Dataqueue.put(json.dumps(payload["event_udp"]).encode("utf-8"))
            except Exception as e:
                print(e)
            


        
        except Exception as e:
            print(f"ERROR in tool_check_CALL: {e}")
            import traceback
            traceback.print_exc()



    async def get_mcp(self):
        if self.mcp is None:
            self.mcp = await MCPSingleton.get_instance()
        return self.mcp


    async def chatLLM(self, messages):
        """
        Stream chat completion from  Llama 3.3 70B
        messages: [{"role": "system/user/assistant", "content": "..."}]
        """
        print("Sending request to Llama 3.3 8B /phi 3.5-mini via Sima ai...")

        self.main.last_active_time=time.time()
        print("Updated Last active time")

        

        
        payload = {
            "model": self.model,
            "messages": self.main.messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 100,
            "tools":{
                [
  {
    "type": "function",
    "function": {
      "name": "PLAY_SONG",
      "description": "This Function is used to plays a song.'"
    }
  },  {
    "type": "function",
    "function": {
      "name": "CALL_CONTACT",
      "description": "This Function is used to call a contact.'"
    }
  }

]                                
            }
        }

        headers = {
            "Authorization": f"Bearer ",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://driver-monitor.local",
            "X-Title": "Driver Monitoring System"
        }

        try:
            self.main.UserCanSpeak = False

            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=30
            )

            text_prefix_buffer = ""
            text_prefix_handled = False

            full_response = ""
            stream_state = "UNKNOWN"  
            buffer = ""


            for line in response.iter_lines():
                self.main.last_active_time=time.time()


                if not line:
                    continue

                decoded_line = line.decode("utf-8")
                if not decoded_line.startswith("data: "):
                    continue

                data = decoded_line.replace("data: ", "").strip()
                if data == "[DONE]":
                    break

                chunk = json.loads(data)
                #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>Printing the CHUNCK>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                #print(chunk)
                delta = chunk["choices"][0]["delta"].get("content", "")
                #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>Printing the CHUNCK>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


                if not delta:
                    continue

                full_response += delta

                # ---------------- UNKNOWN ----------------
                if stream_state == "UNKNOWN":
                    buffer += delta

                    # Decide as soon as possible
                    if buffer.startswith("PLAY_SONG") or buffer.startswith("CALL_CONTACT"):
                        stream_state = "TOOL"
                        continue

                    if buffer.startswith("TEXT:"):
                        stream_state = "TEXT"
                        spoken = buffer.replace("TEXT:", "", 1)
                        if spoken.strip():
                            self.main.textOutputQueue.put(spoken)
                        continue

                    # Not enough info yet
                    if len(buffer) < 10:
                        continue

                    # Safety fallback → treat as TEXT
                    # if buffer.find("PLAY_SONG")  or buffer.find("PHONE_CALL")

                    stream_state = "TEXT"
                    self.main.textOutputQueue.put(buffer)
                    continue

                if stream_state == "TEXT":
                    self.main.textOutputQueue.put(delta)
                    # print(delta)

                    continue

                if stream_state == "TOOL":
                    # Never speak tool output
                    continue
            print(full_response,"___________________________________________________________")


            full_response = full_response.strip()
            self.main.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
            #print(full_response,"rfwefwfefw")
            if full_response in ["PLAY_SONG","CALL_CONTACT"]:

                print(full_response)
                await self.tool_check_CALL(full_response)
            else:
                print(f"Not a tool call.")


              
                self.main.event_queue.put(full_response)
            
            self.main.textOutputQueue.put(None)


            
        

        except requests.exceptions.Timeout:
            print("Request timed out")

        except Exception as e:
            print(f"Error calling OpenRouter: {e}")
            import traceback
            traceback.print_exc()
