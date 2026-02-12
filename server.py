from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from controller import create_controller  
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi import Body
import queue
import os
from fastapi.staticfiles import StaticFiles
import logging
import warnings

logging.disable(logging.CRITICAL)
warnings.filterwarnings("ignore")
from fastapi.responses import HTMLResponse

from fastapi.responses import StreamingResponse
from config.constants import SYSTEMPROMPT
app = FastAPI()

# Mount songs directory
os.makedirs("mcpclass/songs", exist_ok=True)
app.mount("/songs", StaticFiles(directory="mcpclass/songs"), name="songs")

@app.get("/api/songs")
def get_songs():
    try:
        files = [f for f in os.listdir("mcpclass/songs") if f.endswith(".mp3")]
        return {"songs": files}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

controller, monitor, llm, tts, helper, tcp = create_controller()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/image")
async def image(
    image: UploadFile = File(...),
    time: str = Form(...)
):
    try:

        content = await image.read()

        controller.imageQueue.put({
            "filename": image.filename,
            "time": time,
            "bytes": content,
        })

        return JSONResponse(content={"msg": "queued"}, status_code=200)


    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.post("/message")
async def send_message(data: str = Body(...)):
    try:
#         controller.messages.append({
#             "role": "user",
#             "content":  f"""
# YOR NAME IS LTTS EDGE.
# You MUST respond in ONLY one of the following format, based on USER_PROMPT :

# 1. For Tool:

# Tool: <TOOL_NAME>
# ARGS:
# <key>: <value>

# 2. For TEXT:
# TEXT: <response>

# Allowed Tool:
# - PLAY_SONG(song_name: str)
# - CALL_CONTACT(name: str)

# Rules:
# - YOU MUST ALWAYS start with either TEXT or Tool
# - Do NOT explain tools
# - Do NOT mix TEXT and Tool
# - DO NOT MAKE UP NEW TOOLS

# USER_PROMPT: {data}
# """
#         })

        # result = controller.messages[-3:] if len(controller.messages) >= 3 else controller.messages
        if len(controller.messages)>3:
            result=[SYSTEMPROMPT,*controller.messages[-3:]]
        else:
            result=controller.messages

        print(result, "CONTROLLER MESSAGES")

        await helper.chatLLM(result)

        return {"status": "ok"}
    except Exception as e:
        print(f"Error processing message: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    







########
#FRONTEND


from fastapi import WebSocket, WebSocketDisconnect
import asyncio

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                # Non-blocking get from queue
                data = controller.event_queue.get_nowait()
                await websocket.send_json(data)
            except queue.Empty:
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        import traceback
        traceback.print_exc()



from fastapi.responses import HTMLResponse

@app.get("/realcam")
def viewer():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
  <title>Live Stream</title>
</head>
<body>
  <h2>Real-Time Eye Monitor</h2>
  <img id="frame" />

<script>
const ws = new WebSocket(`ws://${location.host}/ws`);
const img = document.getElementById("frame");

ws.onmessage = (event) => {
    const d = JSON.parse(event.data);


    // ✅ only display image if it exists
    if (d.image) {
        img.src = `data:image/jpeg;base64,${d.image}`;
    }
};
</script>

</body>
</html>
""")
