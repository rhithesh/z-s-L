import os
import sys
import logging


# 1. Kill TensorFlow / MediaPipe C++ logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"


from parentClass.main import DMSLMMain
import cv2
import threading
import time
import os


class CameraRL(DMSLMMain):
    def __init__(self, main, fps=7):
        self.main = main
        self.fps = fps
        self.running = True

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Camera is not open")

        # Start capture thread
        self.thread = threading.Thread(target=self.read_images, daemon=True)
        self.thread.start()

    

    def read_images(self):
        print("📷 Camera thread started")

        frame_interval = 1.0 / self.fps


        while self.running:
            start = time.time()

            ret, frame = self.cap.read()
            if not ret:
                continue
            t=str(int(time.time() * 1000))

            # Encode frame to JPEG (like canvas.toBlob)
            framenew= cv2.resize(frame,(320,240))
            #cv2.imwrite(path, framenew)

            success, encoded = cv2.imencode(".jpg", framenew, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if not success:
                continue

            self.main.imageQueue.put({
                "filename": "frame.jpg",
                "time": str(int(time.time() * 1000)),
                "bytes": encoded.tobytes(),
            })

            # FPS control
            elapsed = time.time() - start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()
