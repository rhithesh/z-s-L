import socket
import threading
import json


VALID_SERVICES = ["PlaySong", "StopSong", "PauseSong", "VoiceOver", "PhoneCall"]


class IVIClient:
    """
    UDP receiver that listens on port 8090 for messages from any IP.
    """

    def __init__(self, port=8090):
        self.port = port
        self.stop_event = threading.Event()
        self.sock = None

        self.listener_thread = threading.Thread(
            target=self._listen_udp, daemon=False
        )
        self.listener_thread.start()

    def _listen_udp(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.port))
        self.sock.settimeout(0.5)

        print(f"IVIClient listening for UDP on port {self.port}...")

        while not self.stop_event.is_set():
            try:
                data, addr = self.sock.recvfrom(4096)
                message = data.decode(errors='ignore')
                print(f"Received from {addr}: {message}")
                self.on_message(message, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"UDP error: {e}")

        self.sock.close()

    def on_message(self, message, addr):
        """Handle received UDP messages."""
        # Check if received message is a valid JSON with the version number
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print(f"Invalid JSON received from {addr}")
            return

        if "version" not in data:
            print(f"Missing version in message from {addr}")
            return

        if "response" in data:
            service_name = data["response"].get("service_name")
            if service_name in VALID_SERVICES:

                # check is there is no active conversation.
                self.handle_response(data, addr)
            else:
                print(f"Unknown service in response: {service_name}")

    def handle_response(self, data, addr):
        """Handle incoming service responses."""
        service_name = data["response"]["service_name"]
        response_status = data["response"].get("response")
        reason = data["response"].get("reason")
        slist = data["response"].get("available_songs", "")
        print(f"Response: {service_name} - {response_status} ({reason})")
        self.handle_music_response(reason, slist)

    def handle_music_response(self, sts, song_list):
        sts
        if sts == "Media Not Available":
            #Play the audio file and enable the conversation
            msg = f"Media player is busy or not avilable, would like me to crack a joke, call a friend? "
            print ("** Media Not available **")
            pass

        if sts == "Song Not Available":
            msg = f"Requested song is not available, but these are available: {song_list}"
            #post the string to piper and enable the conversation.

    def finish(self):
        self.stop_event.set()
        self.listener_thread.join()


print ("UDP Listener started...")
client = IVIClient()
client.finish