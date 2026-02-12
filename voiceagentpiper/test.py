import queue
import threading
import sounddevice as sd
import numpy as np
from piper import PiperVoice
import re

class RealtimeTTS:
    def __init__(self, model_path, config_path):
        self.voice = PiperVoice.load(
            model_path=model_path,
            config_path=config_path
        )
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Start worker threads
        self.text_processor_thread = threading.Thread(target=self._process_text, daemon=True)
        self.audio_player_thread = threading.Thread(target=self._play_audio, daemon=True)
        self.text_processor_thread.start()
        self.audio_player_thread.start()
    
    def _process_text(self):
        """Process text chunks and generate audio"""
        buffer = ""
        
        while not self.stop_event.is_set():
            try:
                chunk = self.text_queue.get(timeout=0.1)
                
                if chunk is None:  # Sentinel value to process remaining buffer
                    if buffer.strip():
                        self._synthesize_and_queue(buffer)
                    break
                
                buffer += chunk
                
                # Split on sentence boundaries (. ! ? followed by space or newline)
                sentences = re.split(r'(?<=[.!?])\s+', buffer)
                
                # Process all complete sentences, keep the last one in buffer
                if len(sentences) > 1:
                    for sentence in sentences[:-1]:
                        if sentence.strip():
                            print(f"Speaking: {sentence}")
                            self._synthesize_and_queue(sentence)
                    buffer = sentences[-1]
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Text processing error: {e}")
                import traceback
                traceback.print_exc()
    
    def _synthesize_and_queue(self, text):
        """Synthesize text and add to audio queue"""
        try:
            # Combine all chunks from a single synthesis into one audio buffer
            audio_chunks = []
            for chunk in self.voice.synthesize(text):
                audio_chunks.append(chunk.audio_int16_bytes)
            
            if audio_chunks:
                combined_audio = b"".join(audio_chunks)
                print(f"Queued audio: {len(combined_audio)} bytes")
                self.audio_queue.put(combined_audio)
        except Exception as e:
            print(f"Synthesis error: {e}")
            import traceback
            traceback.print_exc()
    
    def _play_audio(self):
        """Play audio chunks as they become available"""
        while not self.stop_event.is_set():
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                
                if audio_data is None:  # Sentinel value to stop
                    break
                
                print(f"Playing audio: {len(audio_data)} bytes")
                
                try:
                    # Convert bytes to numpy array (int16)
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Convert to float32 in range [-1, 1] for sounddevice
                    audio_float = audio_array.astype(np.float32) / 32768.0
                    
                    # Play audio (blocking)
                    sd.play(audio_float, samplerate=22050, blocking=True)
                    print("Audio playback complete")
                    
                except Exception as e:
                    print(f"Audio play error: {e}")
                    import traceback
                    traceback.print_exc()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Playback error: {e}")
                import traceback
                traceback.print_exc()
    
    def add_text(self, text_chunk):
        """Add LLM token/chunk to processing queue"""
        self.text_queue.put(text_chunk)
    
    def finish(self):
        """Signal that all text has been added and wait for completion"""
        self.text_queue.put(None)  # Sentinel to process remaining buffer
        self.text_processor_thread.join()
        
        self.audio_queue.put(None)  # Sentinel to stop audio
        self.audio_player_thread.join()
    
    def stop(self):
        """Stop all processing immediately"""
        self.stop_event.set()
        sd.stop()  # Stop any playing audio
        self.text_processor_thread.join(timeout=1)
        self.audio_player_thread.join(timeout=1)


# Example usage with simulated LLM streaming
def simulate_llm_streaming():
    """Simulates streaming tokens from an LLM"""
    text = "Hello! This is a real-time text to speech system. It processes tokens as they arrive from the language model. Each sentence is spoken as soon as it's complete. This creates a natural, flowing conversation experience."
    
    import time
    for char in text:
        yield char
        time.sleep(0.01)  # Simulate realistic streaming delay


if __name__ == "__main__":
    # Initialize TTS system
    tts = RealtimeTTS(
        model_path="voiceagentpiper/en_US-amy-medium.onnx",
        config_path="voiceagentpiper/config.json"
    )
    
    print("Streaming text to speech...")
    
    # Simulate LLM token streaming
    for token in simulate_llm_streaming():
        tts.add_text(token)
    
    # Wait for all audio to finish
    tts.finish()
    print("Done!")