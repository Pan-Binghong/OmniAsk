import sounddevice as sd
import numpy as np
import threading
import queue
import time
from openai import OpenAI
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import json
from dotenv import load_dotenv
import os
import tempfile
import soundfile as sf
import psutil
import win32gui
import win32process
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

load_dotenv()

class AudioMonitor:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL')
        )
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.text_callback = None
        self.sample_rate = 16000
        self.channels = 2  # 立体声
        self.chunk_duration = 0.1  # 每次捕获0.1秒
        self.buffer_duration = 2.0  # 缓冲2秒进行处理
        self.audio_buffer = []
        self.latest_audio_data = np.array([])  # 用于可视化的最新音频数据
        
    def get_audio_devices(self):
        """获取所有音频设备"""
        devices = sd.query_devices()
        device_list = []
        
        # 添加输出设备（扬声器）
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:  # 输出设备
                name = f"{device['name']}"
                if device['hostapi'] == 0:  # WASAPI
                    name += " (WASAPI)"
                elif device['hostapi'] == 1:  # DirectSound
                    name += " (DirectSound)"
                device_list.append(("output", i, name))
                
        # 添加输入设备（麦克风等）
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:  # 输入设备
                name = f"{device['name']}"
                if device['hostapi'] == 0:  # WASAPI
                    name += " (WASAPI)"
                elif device['hostapi'] == 1:  # DirectSound
                    name += " (DirectSound)"
                device_list.append(("input", i, name))
                
        return device_list
        
    def get_audio_applications(self):
        """获取所有正在播放音频的应用程序"""
        apps = []
        def enum_windows_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title and process.name() != "explorer.exe":
                        apps.append((pid, f"{process.name()} - {window_title}"))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        win32gui.EnumWindows(enum_windows_callback, [])
        return list(set(apps))  # 去重
        
    def get_available_devices(self):
        """获取所有可用的音频设备和应用程序"""
        devices = self.get_audio_devices()
        
        # 添加应用程序
        for pid, app_name in self.get_audio_applications():
            devices.append(("app", pid, app_name))
            
        return devices
    
    def start_recording(self, device_type, device_id):
        self.is_recording = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"音频回调状态: {status}")
            if np.any(indata):  # 检查是否有任何非零数据
                print(f"接收到音频数据，最大值: {np.max(np.abs(indata))}")
            self.audio_queue.put(indata.copy())
        
        def record_audio():
            try:
                # 获取设备信息
                device_info = sd.query_devices(device_id)
                print(f"使用设备: {device_info['name']}")
                print(f"设备信息: {device_info}")
                
                # 设置采样率匹配设备默认值
                if 'default_samplerate' in device_info:
                    self.sample_rate = int(device_info['default_samplerate'])
                
                # 配置音频流
                stream_config = {
                    'device': device_id,
                    'channels': self.channels,
                    'samplerate': self.sample_rate,
                    'callback': audio_callback,
                    'blocksize': int(self.sample_rate * self.chunk_duration)
                }
                
                # 对于VB-CABLE设备的特殊处理
                if 'CABLE Output' in device_info['name']:
                    stream_config['extra_settings'] = {
                        'wasapi_shared': True,
                        'wasapi_exclusive': False,
                        'autostart': True
                    }
                    print("使用WASAPI共享模式")
                    if self.text_callback:
                        self.text_callback("使用WASAPI共享模式进行录音\n")
                
                # 创建输入流
                stream = sd.InputStream(**stream_config)
                
                with stream:
                    self.text_callback(f"开始录音，使用设备: {device_info['name']}\n")
                    self.text_callback(f"采样率: {self.sample_rate}Hz, 通道数: {self.channels}\n")
                    self.text_callback("请确保：\n1. VB-CABLE Input 被设置为默认播放设备\n2. 在声音设置中启用了'侦听此设备'\n3. 正在播放音频内容\n")
                    
                    while self.is_recording:
                        sd.sleep(int(1000 * self.chunk_duration))
                            
            except Exception as e:
                print(f"录音错误: {e}")
                error_msg = f"""
录音错误: {str(e)}

请按照以下步骤检查：

1. 声音设置检查：
   - 打开Windows声音设置
   - 在"声音控制面板"中找到"录制"标签
   - 找到"CABLE Output"
   - 右键 -> 属性 -> 侦听
   - 勾选"侦听此设备"
   - 选择您的耳机作为回放设备

2. VB-CABLE设置：
   - 确保VB-CABLE驱动正确安装
   - 在播放设备中将"VB-CABLE Input"设为默认设备
   - 确保没有将其静音或音量调至最小

3. 应用程序设置：
   - 确保正在播放音频内容
   - 检查应用程序的音量是否已打开
   - 尝试调高应用程序的音量

4. 如果还是没有声音：
   - 重启应用程序
   - 重新插拔耳机
   - 在设备管理器中重新启用音频设备

当前设备信息：
{device_info}

调试信息：
采样率：{self.sample_rate}Hz
通道数：{self.channels}
块大小：{int(self.sample_rate * self.chunk_duration)}
"""
                print(error_msg)
                if self.text_callback:
                    self.text_callback(error_msg)
                self.is_recording = False
                
        # 启动录音线程
        self.record_thread = threading.Thread(target=record_audio)
        self.record_thread.start()
        
        # 启动处理线程
        self.process_thread = threading.Thread(target=self.process_audio)
        self.process_thread.start()
        
    def stop_recording(self):
        self.is_recording = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        if hasattr(self, 'process_thread'):
            self.process_thread.join()
            
    def process_audio(self):
        buffer_samples = int(self.sample_rate * self.buffer_duration)
        
        while self.is_recording:
            try:
                audio_data = self.audio_queue.get(timeout=1)
                if audio_data.shape[1] == 2:
                    audio_data = np.mean(audio_data, axis=1)
                
                # 更新最新的音频数据用于可视化
                self.latest_audio_data = audio_data
                
                self.audio_buffer.extend(audio_data)
                
                if len(self.audio_buffer) >= buffer_samples:
                    audio_segment = np.array(self.audio_buffer[:buffer_samples])
                    self.audio_buffer = self.audio_buffer[buffer_samples:]
                    
                    volume_level = np.abs(audio_segment).mean()
                    
                    if volume_level > 0.001:
                        if self.text_callback:
                            self.text_callback("检测到声音，开始转录...\n")
                        text = self.transcribe_audio(audio_segment)
                        
                        if text and self.text_callback:
                            if self.is_question(text):
                                self.text_callback(f"问题: {text}\n")
                                answer = self.get_gpt_response(text)
                                self.text_callback(f"回答: {answer}\n")
                            else:
                                self.text_callback(f"文本: {text}\n")
                                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"处理错误: {e}")
                if self.text_callback:
                    self.text_callback(f"错误: {str(e)}\n")
                
    def transcribe_audio(self, audio_data):
        try:
            # 使用唯一的临时文件名
            temp_file_name = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file_name = temp_file.name
                    # 确保文件已关闭
                    temp_file.close()
                    
                # 写入音频数据
                sf.write(temp_file_name, audio_data, self.sample_rate)
                
                # 读取并转录
                with open(temp_file_name, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text",
                        prompt="这是一段中文音频，可能包含问题"
                    )
                
                return transcript.strip()
                
            finally:
                # 确保在任何情况下都尝试删除临时文件
                if temp_file_name and os.path.exists(temp_file_name):
                    try:
                        os.unlink(temp_file_name)
                    except Exception as e:
                        print(f"删除临时文件失败: {e}")
                        
        except Exception as e:
            print(f"转录错误: {e}")
            if self.text_callback:
                self.text_callback(f"转录错误: {str(e)}\n")
            return None
            
    def is_question(self, text):
        # 简单的问题检测逻辑
        question_keywords = ['什么', '如何', '为什么', '怎么', '哪些', '?', '？']
        return any(keyword in text for keyword in question_keywords)
        
    def get_gpt_response(self, question):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "你是一个专业的助手，请简洁地回答问题。"},
                    {"role": "user", "content": question}
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT API 错误: {e}")
            return "抱歉，获取答案时出现错误。"

class AudioVisualizer:
    def __init__(self, frame, audio_monitor):
        self.frame = frame
        self.audio_monitor = audio_monitor
        self.setup_plot()
        
    def setup_plot(self):
        # 创建图形
        self.fig = Figure(figsize=(8, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_ylim(-1, 1)
        self.ax.set_xlim(0, 100)
        self.ax.set_title('音频波形')
        self.line, = self.ax.plot([], [], lw=2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # 初始化数据
        self.data = np.zeros(100)
        self.animation = animation.FuncAnimation(
            self.fig, self.update_plot, interval=50, blit=True)
            
    def update_plot(self, frame):
        if hasattr(self.audio_monitor, 'latest_audio_data'):
            # 更新数据
            new_data = self.audio_monitor.latest_audio_data
            if len(new_data) > 0:
                self.data = np.roll(self.data, -len(new_data))
                self.data[-len(new_data):] = new_data
        
        self.line.set_data(np.arange(len(self.data)), self.data)
        return self.line,

class MonitorGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("实时音频监控系统")
        self.root.geometry("800x600")
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.monitor = AudioMonitor()
        self.monitor.latest_audio_data = np.array([])
        
        self.create_widgets()
        
    def create_widgets(self):
        # 顶部控制区域
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(fill="x", padx=10, pady=5)
        
        # 设备选择
        self.devices = self.monitor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            if device_type == "output":
                prefix = "输出: "
            elif device_type == "input":
                prefix = "输入: "
            else:
                prefix = "应用: "
            device_names.append(f"{device_type}:{id}:{prefix}{name}")
        
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            self.control_frame, 
            textvariable=self.device_var,
            values=device_names,
            width=40
        )
        if device_names:
            self.device_combo.set(device_names[0])
        self.device_combo.pack(side="left", padx=5)
        
        # 控制按钮
        self.refresh_button = ctk.CTkButton(
            self.control_frame,
            text="刷新",
            width=60,
            command=self.refresh_devices
        )
        self.refresh_button.pack(side="left", padx=5)
        
        self.start_button = ctk.CTkButton(
            self.control_frame,
            text="开始",
            width=60,
            command=self.start_monitoring
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(
            self.control_frame,
            text="停止",
            width=60,
            command=self.stop_monitoring,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)
        
        # 音频可视化区域
        self.viz_frame = ctk.CTkFrame(self.root)
        self.viz_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.visualizer = AudioVisualizer(self.viz_frame, self.monitor)
        
        # 简化的文本显示区域
        self.text_area = ctk.CTkTextbox(
            self.root,
            wrap="word",
            height=150
        )
        self.text_area.pack(fill="x", padx=10, pady=5)
        
        # 设置回调
        self.monitor.text_callback = self.update_text
        
    def update_text(self, text):
        if "当前音量级别" not in text:  # 不显示音量级别信息
            self.text_area.insert("end", text)
            self.text_area.see("end")
            
            # 保持最新的几行
            content = self.text_area.get("1.0", "end-1c").split("\n")
            if len(content) > 10:  # 只保留最新的10行
                self.text_area.delete("1.0", "end")
                self.text_area.insert("1.0", "\n".join(content[-10:]) + "\n")
    
    def refresh_devices(self):
        self.devices = self.monitor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            if device_type == "output":
                prefix = "输出: "
            elif device_type == "input":
                prefix = "输入: "
            else:
                prefix = "应用: "
            device_names.append(f"{device_type}:{id}:{prefix}{name}")
            
        self.device_combo.configure(values=device_names)
        if device_names:
            self.device_combo.set(device_names[0])
        self.update_text("已刷新设备列表\n")
        
    def start_monitoring(self):
        if not self.device_var.get():
            self.update_text("请先选择音频来源！\n")
            return
            
        try:
            device_type, device_id, _ = self.device_var.get().split(':', 2)
            device_id = int(device_id)
            
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.monitor.start_recording(device_type, device_id)
            self.update_text("开始监听...\n")
        except Exception as e:
            self.update_text(f"启动失败: {str(e)}\n")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
        
    def stop_monitoring(self):
        self.monitor.stop_recording()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_text("停止监听。\n")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = MonitorGUI()
    gui.run() 