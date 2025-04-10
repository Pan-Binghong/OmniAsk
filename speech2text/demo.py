import asyncio
import pyaudio
import wave
import os
import time
from openai import OpenAI
import tkinter as tk
from tkinter import scrolledtext
import threading
from dotenv import load_dotenv

load_dotenv()

# 音频设置
CHUNK = 2048
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 1.5  # 调整为1.5秒

class AudioTranscriber:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'),base_url=os.getenv('OPENAI_BASE_URL'))
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.text_callback = None
        self.previous_text = ""
        self.text_buffer = []

    def transcribe_audio(self, audio_file_path):
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    prompt="这是一段可能包含中文和英文的混合语音"
                )
                return transcript.strip()
        except Exception as e:
            print(f"转录错误: {e}")
            return None

    def process_text(self, text):
        # 如果新文本是之前文本的一部分，则忽略
        if self.previous_text and text in self.previous_text:
            return None
            
        # 更新之前的文本
        self.previous_text = text
        return text

    async def record_and_transcribe(self):
        stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        print("开始录音...")
        self.is_recording = True

        while self.is_recording:
            try:
                self.frames = []
                # 收集音频数据
                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    if not self.is_recording:
                        break
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    self.frames.append(data)

                if self.frames and self.is_recording:
                    temp_wav = f"temp_{int(time.time())}.wav"
                    with wave.open(temp_wav, 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(self.p.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(self.frames))

                    # 转录并处理文本
                    result = self.transcribe_audio(temp_wav)
                    if result:
                        processed_text = self.process_text(result)
                        if processed_text and self.text_callback:
                            self.text_callback(processed_text)

                    os.remove(temp_wav)

            except Exception as e:
                print(f"录音错误: {e}")
                break

        stream.stop_stream()
        stream.close()

    def stop_recording(self):
        self.is_recording = False
        self.p.terminate()

class TranscriberGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("实时语音转文字")
        self.root.geometry("600x400")

        # 文本显示区域
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, width=60, height=20)
        self.text_area.pack(padx=10, pady=10)

        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        # 控制按钮
        self.start_button = tk.Button(
            button_frame, text="开始录音", command=self.start_recording)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            button_frame, text="停止录音", command=self.stop_recording)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.config(state=tk.DISABLED)

        self.transcriber = AudioTranscriber()
        self.transcriber.text_callback = self.update_text

        self.last_update_time = 0

    def update_text(self, text):
        if text.strip():
            current_time = time.time()
            # 控制更新频率
            if current_time - self.last_update_time > 0.1:  # 最小间隔100ms
                self.text_area.insert(tk.END, text + "\n")
                self.text_area.see(tk.END)
                self.last_update_time = current_time

    def start_recording(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.run_async_loop, daemon=True).start()

    def stop_recording(self):
        self.transcriber.stop_recording()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def run_async_loop(self):
        asyncio.run(self.transcriber.record_and_transcribe())

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = TranscriberGUI()
    gui.run()