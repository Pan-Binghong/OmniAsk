import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from queue import Queue
import threading
import time
from pynput import keyboard

class RealtimeASR:
    def __init__(self):
        # 初始化Whisper模型
        self.model = WhisperModel(
            r"faster-whisper\model\faster-whisper-large-v3",
            device="cuda",
            compute_type="float16"
        )
        
        # 音频参数设置
        self.sample_rate = 16000
        self.chunk_duration = 3  # 每个音频片段的持续时间(秒)
        self.audio_queue = Queue()
        self.is_recording = False
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_duration = 30
        self.is_paused = True
        self.last_text = ""
        self.current_session_texts = []  # 新增：存储当前会话的所有文本
        
        # 设置按键监听
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()
    
    def on_press(self, key):
        """按键处理函数"""
        try:
            if key.char == 'r':
                self.is_paused = not self.is_paused
                if not self.is_paused:
                    # 开始录音时清空所有状态
                    self.audio_buffer = np.array([], dtype=np.float32)
                    self.last_text = ""
                    self.current_session_texts = []  # 清空当前会话文本
                    while not self.audio_queue.empty():
                        self.audio_queue.get()
                    print(f"\n开始录音...")
                else:
                    # 暂停录音时输出完整内容
                    if self.current_session_texts:
                        full_text = "".join(self.current_session_texts)
                        print(f"\n暂停录音...")
                        print(f"本次录音内容为：{full_text}")
                    else:
                        print(f"\n暂停录音...")
                        print("本次录音没有内容")
            elif key.char == 'q':
                self.is_recording = False
                return False
        except AttributeError:
            pass
    
    def on_release(self, key):
        pass

    def audio_callback(self, indata, frames, time, status):
        """音频流回调函数"""
        if status:
            print(status)
        if not self.is_paused:
            audio_chunk = indata.flatten().astype(np.float32)
            self.audio_buffer = np.concatenate([self.audio_buffer, audio_chunk])
            
            # 当累积的音频数据达到指定长度时，放入队列处理
            chunk_samples = int(self.chunk_duration * self.sample_rate)
            if len(self.audio_buffer) >= chunk_samples:
                self.audio_queue.put(self.audio_buffer[-chunk_samples:].copy())
                # 保留最后一部分音频数据，以实现平滑过渡
                self.audio_buffer = self.audio_buffer[-chunk_samples:]
    
    def process_audio(self):
        """处理音频队列中的数据"""
        while self.is_recording:
            if not self.audio_queue.empty() and not self.is_paused:
                audio_data = self.audio_queue.get()
                
                try:
                    segments, info = self.model.transcribe(
                        audio_data,
                        beam_size=5,
                        language='zh',
                        vad_filter=True,
                        vad_parameters=dict(
                            min_silence_duration_ms=500,
                            speech_pad_ms=400,
                        )
                    )
                    
                    # 处理识别结果
                    for segment in segments:
                        if segment.text != self.last_text:
                            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
                            self.last_text = segment.text
                            # 将新的文本添加到当前会话中
                            self.current_session_texts.append(segment.text)
                except Exception as e:
                    print(f"转写出错: {str(e)}")
            time.sleep(0.1)
    
    def start(self):
        """开始实时语音识别"""
        self.is_recording = True
        
        process_thread = threading.Thread(target=self.process_audio)
        process_thread.start()
        
        print("控制键说明：")
        print("- 按 'r' 键开始/暂停录音")
        print("- 按 'q' 键退出程序")
        
        with sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            callback=self.audio_callback
        ):
            while self.is_recording:
                time.sleep(0.1)
        
        self.listener.stop()
        process_thread.join()

if __name__ == "__main__":
    asr = RealtimeASR()
    asr.start()
