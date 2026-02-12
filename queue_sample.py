import queue
import time
import threading

incoming = queue.Queue()

def producer():
    for i in range(10):
        incoming.put(f"item-{i}")
        print("Produced:", i)
        time.sleep(0.1)

def consumer():
    while True:
        obj=incoming.get()
        

threading.Thread(target=producer).start()
threading.Thread(target=consumer).start()
