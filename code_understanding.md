# Class Explanations

## 1. __DMSLMMain__ (parentClass/main.py)

__Base Parent Class for the Driver Monitoring System__

This is the foundational class that provides shared infrastructure for all other classes:

- __Queues__: Manages multiple data queues for inter-thread communication:

  - `imageQueue`: Stores incoming video frames
  - `processdImageJsonQueue`: Contains processed eye detection results
  - `textOutputQueue`: Holds text to be converted to speech
  - `event_queue`: General event communication channel

- __State Management__:

  - `UserCanSpeak`: Boolean flag controlling when user input is allowed
  - `messages`: LLM conversation history with system prompt

- __Background Thread__: Runs `display_queue()` to periodically log system state and broadcast events

## 2. __dMonitoring__ (mlmodels/main.py)

__Driver Eye State Detector (Open/Closed Detection)__

Real-time eye monitoring system using computer vision:

    `def update_bbox(self, frame):
        import time
        now=time.time()
        if now - self.last_updated < self.update_rate :
            return`
    update rate  self.update_rate = 1.0 / 8.0


normal_img_processing time: 1.5ms - 3.5 ms
when update_bbox() function is used: 15 ms - 30 ms

Idea is predict_eye() accepts only the crroped paret of each eye,
we call update_bbox() 8 times every second, we belive face-posture does not change that quickly function which detects eyes is detect_eyes() function.
      

- __Eye Detection__: Uses MediaPipe Face Mesh to detect and track eye regions

- __ONNX Model__: Runs an ONNX neural network to classify each eye as "open" or "closed"

- __Adaptive Bounding Boxes__: Updates eye region bounding boxes at 8 FPS to handle head movement

- __Continuous Processing__: Background thread (`continuscheck`) that:

  - Fetches frames from `imageQueue`
  - Decodes JPEG images
  - Updates bounding boxes when needed
  - Crops eye regions and classifies them
  - Outputs results to `processdImageJsonQueue` and `event_queue`

## 3. __LLMClass__ (llmclass/main.py)

__Drowsiness Detection & LLM Alert System__

Monitors driver alertness and triggers conversational interventions:

- __Eye State Tracking__: Continuously reads from `processdImageJsonQueue`

- __Drowsiness Detection__:

  - Counts consecutive closed-eye frames
  - Triggers alert when both eyes closed for 9+ frames (at 30 FPS ≈ 0.3 seconds)

- __LLM Integration__: When drowsiness detected and user can speak:

  - Calls Helper class to interact with LLM
  - Initiates a voice conversation to check driver alertness
  - Provides context about closed eye duration

## 4. __PiperTTS__ (pipertts/main.py)

__Text-to-Speech Audio Output System__

Converts LLM text responses to spoken audio:

- __Piper Voice Model__: Uses Piper neural TTS (amy-medium voice)

- __Dual Thread Architecture__:

  1. __Text Processor Thread__:

     - Reads from `textOutputQueue`
     - Buffers text and splits into sentences
     - Synthesizes audio for complete sentences

  2. __Audio Player Thread__:

     - Plays queued audio chunks sequentially
     - Sets `UserCanSpeak=False` during playback to prevent interruptions
     - Re-enables user input after playback completes

- __Intelligent Processing__: Sentence-based synthesis for natural pauses in speech

## System Flow

1. Video frames → `dMonitoring` → Eye state detection
2. Eye states → `LLMClass` → Drowsiness monitoring
3. Drowsiness detected → LLM generates response text
4. Text → `PiperTTS` → Audio playback via speakers
5.Chat -> `Helper`-> class the LLM api

##Help required immediately(Bharath,Hemanth,Jainendra,Hithesh):
check if MODALIX supports 30fps img/video encoding it says it does have not tried it yet.
Implement time in ms everywhere queue in/out, time to first token, avg tps. (only img processing time is ready as of now), Make a parentClass method to do this or use a simple timerun library.
self.main.UserCanSpeak is misbehaving, more in(transcribing llm output via speaker to) pipertts/main.py
pipertts needs to do audio_playback based on words and not sentences. pipertts/main.py

##thing to think about:
Look into Hemanth's imlementation for better approach ON voice modulation.
Implement LLM activation only on start words like Hey Siri!, Hey alexa!.
RAG implementation (to be discussed with Bharath, jainendra), which model's support Tool-calling  (to be discussed with hemanth)
With tool calling enabled we can implement a lot of things like paying music, changing navigation, reading latest news, giving the exact traffic update and more so (discuss with jainendra).


DEMO video:
(will done by tmrw afternoon DEC 2nd )


