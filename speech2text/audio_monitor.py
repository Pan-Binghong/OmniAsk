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
        self.volume_callback = None  # 新增音量回调函数
        self.sample_rate = 16000
        self.channels = 2  # 立体声
        self.chunk_duration = 0.1  # 每次捕获0.1秒
        self.buffer_duration = 2.0  # 缓冲2秒进行处理
        self.audio_buffer = []
        self.current_volume = 0.0  # 当前音量水平
        
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
            
            # 计算当前音量级别
            if np.any(indata):
                volume_level = np.abs(indata).mean()
                self.current_volume = volume_level
                if self.volume_callback:
                    self.volume_callback(volume_level)
                    
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
        """流式获取GPT回复"""
        try:
            # 更适合会议记录的系统提示
            system_prompt = """你是一个专业的AI助手，现在正在参加一个会议。
            请用简练、专业的语言回答问题，保持回答的条理性和易读性。
            回答要有逻辑性，可以使用段落、列表等方式组织内容，以提高可读性。
            回答应当是完整的、有深度的，并避免过于冗长。
            字数控制在150字左右，除非问题需要更详细的解答。"""
            
            # 使用stream=True来获取流式响应
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                stream=True  # 启用流式输出
            )
            
            # 发送一个特殊标记表示开始新的回答
            if self.text_callback:
                self.text_callback("回答: ")
            
            # 用于累积完整的回答
            full_response = ""
            
            # 逐个处理流式响应的内容
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # 发送带有特殊标记的增量更新
                    if self.text_callback:
                        self.text_callback(f"<stream>{content}")
                    # 小延迟，避免过快刷新
                    time.sleep(0.01)
            
            return full_response
            
        except Exception as e:
            print(f"GPT API 错误: {e}")
            if self.text_callback:
                self.text_callback(f"<stream>抱歉，获取答案时出现错误。")
            return "抱歉，获取答案时出现错误。"

class VolumeIndicator:
    """简单的音量指示器，替代复杂的波形图"""
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, fg_color="#262626", height=25)
        self.frame.pack(side="right", padx=5, pady=5, fill="x", expand=True)
        
        # 创建多个块状指示灯
        self.indicators = []
        self.colors = ["#00B4D8", "#009FB9", "#008B9A", "#00777B", "#00535C"]
        
        self.indicator_frame = ctk.CTkFrame(self.frame, fg_color="#262626")
        self.indicator_frame.pack(fill="both", expand=True)
        
        for i in range(10):
            color = self.colors[min(i//2, len(self.colors)-1)]
            indicator = ctk.CTkFrame(
                self.indicator_frame, 
                width=5, 
                height=15, 
                fg_color="#333333",
                corner_radius=1
            )
            indicator.pack(side="left", padx=1, pady=0)
            self.indicators.append(indicator)
    
    def update(self, volume):
        """更新音量指示器"""
        # 将音量值(通常很小)转换为0-10的范围
        level = min(10, int(volume * 400))
        
        # 更新指示灯状态
        for i, indicator in enumerate(self.indicators):
            if i < level:
                color = self.colors[min(i//2, len(self.colors)-1)]
                indicator.configure(fg_color=color)
            else:
                indicator.configure(fg_color="#333333")

class MonitorGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("实时语音助手")
        self.root.geometry("900x600")
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.monitor = AudioMonitor()
        
        # 打字机效果相关变量
        self.typing_speed = 20  # 打字速度（毫秒）
        self.typing_queue = queue.Queue()  # 用于存储待显示的文本
        self.is_typing = False  # 是否正在显示打字效果
        
        self.create_widgets()
        
        # 设置音量回调
        self.monitor.volume_callback = self.volume_indicator.update
        
        # 启动打字机效果处理线程
        self.typing_thread = threading.Thread(target=self.process_typing_queue, daemon=True)
        self.typing_thread.start()
        
    def create_widgets(self):
        # 创建两列布局
        self.root.grid_columnconfigure(0, weight=4)  # 左侧占40%
        self.root.grid_columnconfigure(1, weight=6)  # 右侧占60%
        
        # 左侧面板 - 控制区域和问题显示
        self.left_frame = ctk.CTkFrame(self.root)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        self.left_frame.grid_rowconfigure(1, weight=1)  # 文本区域占满剩余空间
        
        # 右侧面板 - 回答显示
        self.right_frame = ctk.CTkFrame(self.root)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)
        self.right_frame.grid_rowconfigure(1, weight=1)  # 文本区域占满剩余空间
        
        # 左侧顶部 - 控制区域
        self.control_frame = ctk.CTkFrame(self.left_frame)
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # 状态指示器区域
        self.status_frame = ctk.CTkFrame(self.left_frame)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        # 状态文本
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="就绪",
            height=25
        )
        self.status_label.pack(side="left", padx=5)
        
        # 音量指示器 - 替代波形图
        self.volume_indicator = VolumeIndicator(self.status_frame)
        
        # 左侧文本区域标题
        self.question_title_frame = ctk.CTkFrame(self.left_frame, fg_color="#2B2B2B", height=35)
        self.question_title_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(5,0))
        
        self.question_label = ctk.CTkLabel(
            self.question_title_frame,
            text="识别文本",
            font=("微软雅黑", 12, "bold"),
            text_color="#00B4D8"
        )
        self.question_label.pack(side="left", padx=10, pady=5)
        
        # 左侧文本区域
        self.question_frame = ctk.CTkFrame(self.left_frame, fg_color="#262626")
        self.question_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        self.left_frame.grid_rowconfigure(4, weight=1)
        
        self.question_area = ctk.CTkTextbox(
            self.question_frame,
            wrap="word",
            font=("微软雅黑", 11),
            fg_color="#262626",
            border_width=0
        )
        self.question_area.pack(fill="both", expand=True, padx=3, pady=3)
        
        # 右侧标题
        self.answer_title_frame = ctk.CTkFrame(self.right_frame, fg_color="#2B2B2B", height=35)
        self.answer_title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.answer_label = ctk.CTkLabel(
            self.answer_title_frame,
            text="AI 回复",
            font=("微软雅黑", 12, "bold"),
            text_color="#98FB98"
        )
        self.answer_label.pack(side="left", padx=10, pady=5)
        
        # 右侧文本区域
        self.answer_frame = ctk.CTkFrame(self.right_frame, fg_color="#262626")
        self.answer_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.answer_area = ctk.CTkTextbox(
            self.answer_frame,
            wrap="word",
            font=("微软雅黑", 11),
            fg_color="#262626",
            border_width=0
        )
        self.answer_area.pack(fill="both", expand=True, padx=3, pady=3)
        
        # 定义文本标签样式
        self.question_area.tag_configure("question", foreground="#00B4D8", font=("微软雅黑", 11, "bold"))
        self.question_area.tag_configure("transcription", foreground="#E0E0E0", font=("微软雅黑", 11))
        self.question_area.tag_configure("system", foreground="#888888", font=("微软雅黑", 10))
        self.question_area.tag_configure("error", foreground="#FF6B6B", font=("微软雅黑", 10))
        
        self.answer_area.tag_configure("answer", foreground="#98FB98", font=("微软雅黑", 11))
        self.answer_area.tag_configure("error", foreground="#FF6B6B", font=("微软雅黑", 10))
        
        # 设备选择和控制按钮
        self.create_control_widgets()
        
        # 设置回调
        self.monitor.text_callback = self.update_text
        
    def create_control_widgets(self):
        # 设备选择标签
        self.device_label = ctk.CTkLabel(
            self.control_frame,
            text="音频源:",
            width=60
        )
        self.device_label.pack(side="left", padx=(5, 2))
        
        # 设备选择
        self.devices = self.monitor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            if device_type == "output":
                prefix = "🔊 输出: "
            elif device_type == "input":
                prefix = "🎤 输入: "
            else:
                prefix = "📱 应用: "
            device_names.append(f"{device_type}:{id}:{prefix}{name}")
        
        self.device_var = tk.StringVar()
        
        # 自定义下拉框样式
        style = ttk.Style()
        style.configure(
            "Custom.TCombobox",
            background="#2B2B2B",
            fieldbackground="#2B2B2B",
            foreground="#FFFFFF",
            arrowcolor="#FFFFFF"
        )
        
        self.device_combo = ttk.Combobox(
            self.control_frame, 
            textvariable=self.device_var,
            values=device_names,
            width=30,  # 减小宽度
            style="Custom.TCombobox"
        )
        if device_names:
            self.device_combo.set(device_names[0])
        self.device_combo.pack(side="left", padx=5)
        
        # 控制按钮
        self.button_frame = ctk.CTkFrame(self.control_frame)
        self.button_frame.pack(side="right", padx=5)
        
        self.refresh_button = ctk.CTkButton(
            self.button_frame,
            text="刷新",
            width=60,
            height=28,
            command=self.refresh_devices,
            fg_color="#2B5B65",
            hover_color="#1B4B55"
        )
        self.refresh_button.pack(side="left", padx=2)
        
        self.start_button = ctk.CTkButton(
            self.button_frame,
            text="开始",
            width=60,
            height=28,
            command=self.start_monitoring,
            fg_color="#2B652B",
            hover_color="#1B551B"
        )
        self.start_button.pack(side="left", padx=2)
        
        self.stop_button = ctk.CTkButton(
            self.button_frame,
            text="停止",
            width=60,
            height=28,
            command=self.stop_monitoring,
            state="disabled",
            fg_color="#652B2B",
            hover_color="#551B1B"
        )
        self.stop_button.pack(side="left", padx=2)
        
        # 添加打字速度控制滑块
        self.speed_frame = ctk.CTkFrame(self.control_frame)
        self.speed_frame.pack(side="right", padx=10)
        
        self.speed_label = ctk.CTkLabel(
            self.speed_frame,
            text="打字速度",
            font=("微软雅黑", 10)
        )
        self.speed_label.pack(side="left", padx=5)
        
        self.speed_slider = ctk.CTkSlider(
            self.speed_frame,
            from_=10,
            to=50,  # 缩小范围，加快打字速度
            number_of_steps=40,
            width=80,
            command=self.adjust_typing_speed
        )
        self.speed_slider.set(self.typing_speed)
        self.speed_slider.pack(side="left", padx=5)
        
    def update_text(self, text):
        if "当前音量级别" not in text:
            # 处理流式输出
            if text.startswith("<stream>"):
                content = text[8:]  # 移除<stream>标记
                # 将流式内容添加到打字队列
                self.typing_queue.put((content, "answer", True))
                return
            
            # 根据内容类型将文本添加到相应的区域
            if "问题:" in text:
                self.typing_queue.put((text + "\n", "question", False))
            elif "文本:" in text:
                self.typing_queue.put((text + "\n", "transcription", False))
            elif "回答:" in text:
                # 只添加"回答:"标记，实际内容通过流式输出显示
                self.typing_queue.put(("", "answer", True))
            elif "错误" in text or "失败" in text:
                # 错误信息同时显示在两边
                self.typing_queue.put((text + "\n", "error", False))
                self.typing_queue.put((text + "\n", "error", True))
                self.status_label.configure(text="❌ 出现错误", text_color="#FF6B6B")
            else:
                # 系统消息显示在问题区域
                self.typing_queue.put((text + "\n", "system", False))
            
            # 更新状态标签
            if "开始" in text:
                self.status_label.configure(text="🎵 正在录音...", text_color="#00B4D8")
            elif "停止" in text:
                self.status_label.configure(text="⏹ 已停止", text_color="#FF6B6B")
            
            # 保持最新的几行，但分别处理两个文本区域
            for text_area in [self.question_area, self.answer_area]:
                content = text_area.get("1.0", "end-1c").split("\n")
                if len(content) > 50:  # 保留更多行以显示完整对话
                    text_area.delete("1.0", "end")
                    text_area.insert("1.0", "\n".join(content[-50:]) + "\n")
    
    def refresh_devices(self):
        self.devices = self.monitor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            if device_type == "output":
                prefix = "🔊 输出: "
            elif device_type == "input":
                prefix = "🎤 输入: "
            else:
                prefix = "📱 应用: "
            device_names.append(f"{device_type}:{id}:{prefix}{name}")
            
        self.device_combo.configure(values=device_names)
        if device_names:
            self.device_combo.set(device_names[0])
        self.update_text("✨ 已刷新设备列表\n")
        self.status_label.configure(text="📝 已更新设备列表", text_color="#00B4D8")
        
    def start_monitoring(self):
        if not self.device_var.get():
            self.update_text("⚠️ 请先选择音频来源！\n")
            return
            
        try:
            device_type, device_id, _ = self.device_var.get().split(':', 2)
            device_id = int(device_id)
            
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.monitor.start_recording(device_type, device_id)
            self.update_text("🎵 开始监听...\n")
        except Exception as e:
            self.update_text(f"❌ 启动失败: {str(e)}\n")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
        
    def stop_monitoring(self):
        self.monitor.stop_recording()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_text("⏹ 停止监听。\n")
        
    def process_typing_queue(self):
        """处理打字机效果队列"""
        while True:
            try:
                # 获取下一个要显示的字符和相关信息
                text, tag, is_stream = self.typing_queue.get()
                self.is_typing = True
                
                # 选择目标文本区域
                target_area = self.answer_area if is_stream else self.question_area
                
                # 如果是空文本，直接跳过
                if not text:
                    self.typing_queue.task_done()
                    self.is_typing = False
                    continue
                
                # 逐字显示文本
                for char in text:
                    if char == '\n':
                        # 对于换行符，直接添加
                        target_area.insert("end", char, tag)
                    else:
                        # 对于普通字符，添加并模拟打字延迟
                        target_area.insert("end", char, tag)
                        target_area.see("end")
                        time.sleep(self.typing_speed / 1000)  # 转换为秒
                
                self.is_typing = False
                self.typing_queue.task_done()
                
            except queue.Empty:
                time.sleep(0.1)  # 避免过度消耗CPU
                continue
            except Exception as e:
                print(f"打字机效果错误: {e}")
                self.is_typing = False
                continue

    def adjust_typing_speed(self, speed):
        """调整打字速度（毫秒）"""
        self.typing_speed = max(10, min(50, speed))  # 限制在10-50毫秒范围内

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = MonitorGUI()
    gui.run() 