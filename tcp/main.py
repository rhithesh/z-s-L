import socket
import time
import json
from parentClass.main import DMSLMMain
import threading


class TCP(DMSLMMain):
    def __init__(self,main):
        self.main=main

        self.SERVER_IP = "192.168.1.3"
        self.SERVER_PORT = 8050
        self.sock = None

        self.connect()
        data="Hello"
        data = json.dumps(data).encode("utf-8")

        #self.send_data(data)

        self.runthread = threading.Thread(
            target=self.run, daemon=True
        )
        self.runthread.start()




    def connect(self):
        try:
            print("Initializing UDP socket...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.SERVER_IP, self.SERVER_PORT))
            time.sleep(0.4)
            #self.send_data(b"UDP socket ready testing verified hithesh here")

            print("UDP socket ready")
        except socket.error as e:
            print("Error initializing UDP socket:", e)

    def send_data(self, data: bytes):
        try:
            ans=self.sock.sendall(data)
            print(ans,data,"Sucessfully sent")
        except socket.error:
            print("UDP send error. Reinitializing...")
            self.connect()
            try:
                ans = self.sock.sendall(data)
                data= self.sock.recv(5120) 
                print(ans)
            except socket.error as e:
                print("Failed to send UDP data:", e)
        finally:
            self.sock.close()


    def run(self):
        while True:
            if not self.main.Dataqueue.empty():
                data = self.main.Dataqueue.get()

                if isinstance(data, str):
                    data = data.encode()

                self.send_data(data)

            time.sleep(0.01)  
    
