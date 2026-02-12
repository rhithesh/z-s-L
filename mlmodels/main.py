import logging
import mediapipe as mp
import onnxruntime as ort

# Silence TensorFlow / MediaPipe C++ logs
import os
import sys
import logging
logging.disable(logging.INFO)

import os

# Kill TensorFlow C++ logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 0=all, 1=INFO, 2=WARNING, 3=ERROR

# Kill MediaPipe / absl logs
os.environ["GLOG_minloglevel"] = "3"      # 0=INFO, 1=WARNING, 2=ERROR, 3=FATAL
os.environ["GLOG_logtostderr"] = "1"
# --- HARD SILENCE: redirect OS-level stderr ---
devnull = os.open(os.devnull, os.O_WRONLY)
os.dup2(devnull, 2)   # fd 2 = stderr
os.close(devnull)
import cv2
import time
import numpy as np
import base64
from parentClass.main import DMSLMMain
import threading

#Please check with SimaAI
#if mediapipe,jaxlib,ml-dtypes library works with Modalix as we got errors while installing.!!
#if it is not compatible find a go around to mediapipe.
#check if onnxruntime works on modalix

import warnings
from absl import logging
logging.set_verbosity(logging.ERROR)
logging.set_stderrthreshold(logging.ERROR)

warnings.filterwarnings("ignore")
so = ort.SessionOptions()
so.log_severity_level = 4   # 0=verbose, 1=info, 2=warning, 3=error, 4=fatal (silent)


def detect_eyes(image):
    h, w, _ = image.shape
    mp_face_mesh = mp.solutions.face_mesh

    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as face_mesh:
        results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            return None, None, None, None

        landmarks = results.multi_face_landmarks[0]

        # Mesh IDs for each eye region
        left_ids = [33, 133, 160, 159, 158, 153]
        right_ids = [362, 263, 387, 386, 385, 380]

        def extract_bbox(ids):
            xs = [int(landmarks.landmark[i].x * w) for i in ids]
            ys = [int(landmarks.landmark[i].y * h) for i in ids]
            x1, x2 = min(xs) - 5, max(xs) + 5
            y1, y2 = min(ys) - 5, max(ys) + 5
            return (x1, y1, x2, y2)

        left_bbox = extract_bbox(left_ids)
        right_bbox = extract_bbox(right_ids)

        left_eye = image[left_bbox[1]:left_bbox[3], left_bbox[0]:left_bbox[2]]
        right_eye = image[right_bbox[1]:right_bbox[3], right_bbox[0]:right_bbox[2]]

        return left_eye, right_eye, left_bbox, right_bbox


class dMonitoring(DMSLMMain):
    """
    Driver Monitoring System Eye Detector
    Tracks eyes with bounding-box updates every frame, only ONNX inference on eye patches.
    """

    def __init__(self,main, model_path="ocec_p.onnx"):
        self.main=main
        self.session = ort.InferenceSession(model_path,sess_options=so)
        self.input_name = self.session.get_inputs()[0].name
        # store bounding boxes
        self.last_updated = 0
        self.update_rate = 1.0 / 4.0
        self.bbox = {"left": None, "right": None}
        
        threading.Thread(target=self.continuscheck, daemon=True).start()


    def preprocess(self, img):
        img = cv2.resize(img, (40, 24))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = img[np.newaxis, :, :, :]
        return img
    

    def predict_eye(self, img):
        img = self.preprocess(img)
        output = self.session.run(None, {self.input_name: img})[0]
        prob = float(output)
        return "open" if prob > 0.3 else "closed"

    def update_bbox(self, frame):
        import time
        now=time.time()
        if now - self.last_updated < self.update_rate :
            return
        
        

        self.last_updated = now


        left_eye, right_eye, left_bbox, right_bbox = detect_eyes(frame)
        if left_eye is None or right_eye is None:
            return

        def need_update(old, new):
            if old is None:
                return True
            return (abs(old[0] - new[0]) > 2 or abs(old[1] - new[1]) > 2)

        if need_update(self.bbox['left'], left_bbox):
            self.main.event_queue.put({"event":"bbox_update","bbox":left_bbox})
            self.bbox['left'] = left_bbox

        if need_update(self.bbox['right'], right_bbox):
            self.main.event_queue.put({"event":"bbox_update","bbox":left_bbox})
            self.bbox['right'] = right_bbox

    def crop_from_bbox(self, frame, bbox):
        x1, y1, x2, y2 = bbox
        return frame[y1:y2, x1:x2]

    def check(self, frame):
        if self.bbox['left'] is None or self.bbox['right'] is None:
            return {"error": "bbox not initialized"}

        left_crop = self.crop_from_bbox(frame, self.bbox['left'])
        right_crop = self.crop_from_bbox(frame, self.bbox['right'])

        left_state = self.predict_eye(left_crop)
        right_state = self.predict_eye(right_crop)
      




        return {
            "time": time.time(),
            "left_eye": left_state,
            "right_eye": right_state,
            "left_bbox":self.bbox['left'],
            "right_bbox":self.bbox['right']
        }
    def continuscheck(self):
        import numpy as np, cv2
        drow=0

        while True:
            try:
                item = self.main.imageQueue.get()   # FIXED: no tuple unpack
                #print("Fetched data from queue:", item["time"])
                start = time.perf_counter()


                jpg = np.frombuffer(item["bytes"], dtype=np.uint8)
                frame = cv2.imdecode(jpg, cv2.IMREAD_COLOR)
                if frame is None:
                    print("failed in decoding frame ")
                    continue
                
                self.update_bbox(frame)
                result = self.check(frame)
                end = time.perf_counter()
                

                
                self.main.processdImageJsonQueue.put(result)
                diff=(end-start)*1000


                
                if result["right_eye"]=="closed" and result["left_eye"]=="closed" and drow >= 15 and not self.main.session:
                    drow=0
                    bboxes = [result["left_bbox"], result["right_bbox"]]
                    for (x1, y1, x2, y2) in bboxes:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    success, buffer = cv2.imencode(".jpg", frame)

                    if not success:
                        raise RuntimeError("Failed to encode frame")

                    frame_b64 = base64.b64encode(buffer).decode("utf-8")
                    result["image"]=frame_b64
                drow=drow+1

                



                self.main.event_queue.put({"imp":diff,**result })



            except Exception as e:
                print("Error in continuscheck from CLASS mlmodels:", e)
                continue


