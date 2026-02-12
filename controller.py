from parentClass.main import DMSLMMain
from mlmodels.main import dMonitoring
from llmclass.main import LLMClass
from pipertts.main import PiperTTS
from helper.chat import Helper
from whispermodule.main import VoiceInput
from tcp.main import TCP
from cameraRL.main import CameraRL
from udpClient.main import IVIClient


#we are creating a controller so we can keep the server.py part clean


def create_controller():
    controller = DMSLMMain()
    monitor = dMonitoring(controller)
    llm = LLMClass(controller)
    tts = PiperTTS(controller)
    helper = Helper(controller)
    voice = VoiceInput(controller)
    tcp = TCP(controller)
    camerarl=CameraRL(controller)
    iviclient=IVIClient(controller)

    return controller, monitor, llm, tts, helper, tcp