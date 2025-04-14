"""
音频处理模块，负责音频捕获和处理
"""

import sounddevice as sd
import numpy as np
import threading
import queue
import time
import tempfile
import soundfile as sf
import os
import wave
import requests
import json
import mimetypes
from typing import Optional, List, Dict, Callable, Any
from openai import OpenAI
import psutil
import win32gui
import win32process
from ..config.settings import AUDIO_SETTINGS, WHISPER_SETTINGS, GPT_SETTINGS, QUESTION_KEYWORDS
from ..utils.error_handler import ErrorHandler

# 用于multipart/form-data请求的boundary
BOUNDARY = '----WebKitFormBoundary' + ''.join(['1234567890', 'abcdefghijklmnopqrstuvwxyz'][:10])

# 问题关键词
QUESTION_KEYWORDS = ['吗', '?', '？', '什么', '为什么', '如何', '怎么', '哪里', '谁', '何时', '是否']

class AudioProcessor:
    def __init__(self):
        """初始化音频处理器"""
        # 初始化API客户端
        try:
            self.client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                base_url=os.getenv('OPENAI_BASE_URL')
            )
        except Exception as e:
            ErrorHandler.handle_error(e, "API客户端初始化失败")
            raise
            
        # 初始化内部状态
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.text_callback = None
        self.volume_callback = None
        
        # 从配置文件加载设置
        self.sample_rate = AUDIO_SETTINGS['SAMPLE_RATE']
        self.channels = AUDIO_SETTINGS['CHANNELS']
        self.chunk_duration = AUDIO_SETTINGS.get('CHUNK_DURATION', 0.1)
        self.buffer_duration = AUDIO_SETTINGS['BUFFER_DURATION']
        
        self.audio_buffer = []
        self.latest_audio_data = np.array([])
        self.current_device = None
        
    def get_audio_devices(self) -> List[tuple]:
        """获取所有音频设备"""
        return ErrorHandler.safe_execute(
            self._get_audio_devices,
            "获取音频设备时出错",
            default_return=[]
        )
    
    def _get_audio_devices(self) -> List[tuple]:
        """内部方法：获取所有音频设备"""
        devices = sd.query_devices()
        device_list = []
        
        # 添加输出设备
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                name = f"{device['name']}"
                if device['hostapi'] == 0:  # WASAPI
                    name += " (WASAPI)"
                    device_list.append(("output", i, name))
                elif device['hostapi'] == 1:  # DirectSound
                    name += " (DirectSound)"
                    device_list.append(("output", i, name))
                
        # 添加输入设备
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                name = f"{device['name']}"
                if device['hostapi'] == 0:  # WASAPI
                    name += " (WASAPI)"
                    device_list.append(("input", i, name))
                elif device['hostapi'] == 1:  # DirectSound
                    name += " (DirectSound)"
                    device_list.append(("input", i, name))
                
        return device_list
        
    def get_audio_applications(self) -> List[tuple]:
        """获取正在播放音频的应用程序"""
        return ErrorHandler.safe_execute(
            self._get_audio_applications,
            "获取音频应用程序时出错",
            default_return=[]
        )
    
    def _get_audio_applications(self) -> List[tuple]:
        """内部方法：获取正在播放音频的应用程序"""
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
        return list(set(apps))
        
    def get_available_devices(self) -> List[tuple]:
        """获取所有可用的音频设备和应用程序"""
        devices = self.get_audio_devices()
        for pid, app_name in self.get_audio_applications():
            devices.append(("app", pid, app_name))
        return devices
        
    def audio_callback(self, indata, frames, time, status):
        """音频回调函数，处理捕获的音频数据"""
        if status:
            print(f"音频回调状态: {status}")
        
        # 计算当前音量级别
        if np.any(indata):
            volume_level = np.abs(indata).mean()
            if self.volume_callback:
                self.volume_callback(volume_level)
        
        self.audio_queue.put(indata.copy())
        
    def start_recording(self, device_type: str, device_id: int):
        """开始录音"""
        if self.is_recording:
            # 如果已经在录音，先停止当前录音
            self.stop_recording()
            
        self.is_recording = True
        
        # 启动录音线程
        self.record_thread = threading.Thread(
            target=lambda: ErrorHandler.safe_execute(
                self._record_audio,
                "录音过程中出错",
                self.text_callback,
                device_type=device_type,
                device_id=device_id
            )
        )
        
        # 启动处理线程
        self.process_thread = threading.Thread(
            target=lambda: ErrorHandler.safe_execute(
                self.process_audio,
                "处理音频时出错",
                self.text_callback
            )
        )
        
        self.record_thread.start()
        self.process_thread.start()
            
    def _record_audio(self, device_type: str, device_id: int):
        """内部方法：实际录音实现"""
        try:
            # 获取设备信息
            devices = sd.query_devices()
            device_info = None
            selected_device_id = device_id  # 保存原始device_id
            
            if device_type == "app":
                # 查找VB-CABLE Output设备
                for i, dev in enumerate(devices):
                    if dev['max_input_channels'] > 0 and ('CABLE Output' in dev['name'] or 'VB-Audio' in dev['name']):
                        selected_device_id = i
                        device_info = dev
                        break
                
                # 如果没找到VB-CABLE，尝试使用默认输入设备
                if device_info is None:
                    default_device = sd.query_devices(kind='input')
                    selected_device_id = default_device['index']
                    device_info = default_device
            else:
                device_info = devices[selected_device_id]
            
            if device_info is None:
                raise Exception("找不到可用的音频设备")
            
            # 保存当前设备信息
            self.current_device = device_info
            
            # 设置采样率和通道数
            self.sample_rate = int(device_info['default_samplerate'])
            self.channels = min(2, device_info['max_input_channels'])
            
            # 配置音频流
            stream_config = {
                'device': selected_device_id,
                'channels': self.channels,
                'samplerate': self.sample_rate,
                'callback': self.audio_callback,
                'blocksize': int(self.sample_rate * self.chunk_duration)
            }
            
            # 使用WASAPI共享模式
            if device_type in ["output", "app"]:
                stream_config['extra_settings'] = dict(
                    wasapi_shared=True,
                    wasapi_exclusive=False
                )
            
            # 创建音频流
            with sd.InputStream(**stream_config):
                if self.text_callback:
                    self.text_callback(f"正在使用设备: {device_info['name']}\n")
                    self.text_callback(f"采样率: {self.sample_rate}Hz, 通道数: {self.channels}\n")
                    if device_type == "app":
                        self.text_callback("""
请确保：
1. VB-CABLE已正确安装并启用：
   - 在Windows声音设置中找到"CABLE Output"
   - 确保设备已启用且未被禁用
   - 在设备属性中启用"侦听此设备"
   - 选择您的耳机作为回放设备

2. 音频设置正确：
   - 检查系统音量混合器中的应用程序音量
   - 确保应用程序正在播放音频
   - 尝试调整应用程序的音频输出设备

3. 如果听不到声音：
   - 检查耳机是否设为默认播放设备
   - 确保"CABLE Output"的侦听功能已启用
   - 检查系统和应用程序音量

4. 如果仍有问题：
   - 重启应用程序
   - 检查是否有其他程序占用音频设备
   - 尝试重新插拔耳机或重启电脑
\n""")
                
                while self.is_recording:
                    sd.sleep(int(1000 * self.chunk_duration))
                    
        except Exception as e:
            if not self.is_recording:
                # 如果已经不在录音状态，说明是正常停止，不需要报错
                return
                
            error_msg = f"录音错误: {str(e)}\n"
            if device_type == "app":
                error_msg += f"""
音频设备配置错误，请检查：
1. 设备状态：
   - 当前设备: {self.current_device['name'] if self.current_device else '未知'}
   - 采样率: {self.sample_rate}Hz
   - 通道数: {self.channels}

2. 常见问题解决：
   - 确保VB-CABLE驱动已正确安装
   - 检查Windows声音设置中的设备状态
   - 验证应用程序的音频输出设置
   - 尝试重新启动应用程序和音频服务

3. 详细错误信息：
{str(e)}
"""
            if self.text_callback:
                self.text_callback(error_msg)
            self.is_recording = False
        
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            return
            
        print("正在停止录音...")
        self.is_recording = False
        
        try:
            # 等待线程结束，但设置超时时间
            if hasattr(self, 'record_thread'):
                self.record_thread.join(timeout=2.0)
            if hasattr(self, 'process_thread'):
                self.process_thread.join(timeout=2.0)
                
            # 清空队列
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
                    
            # 重置缓冲区和设备信息
            self.audio_buffer = []
            self.latest_audio_data = np.array([])
            self.current_device = None
            
        except Exception as e:
            ErrorHandler.handle_error(e, "停止录音时出错", self.text_callback)
        finally:
            print("录音已停止")
            
    def process_audio(self):
        """处理音频数据"""
        buffer_samples = int(self.sample_rate * self.buffer_duration)
        
        # 从配置文件读取参数
        silence_threshold = AUDIO_SETTINGS.get("SILENCE_THRESHOLD", 0.0015)  # 静音阈值，增加灵敏度
        min_speech_samples = int(self.sample_rate * AUDIO_SETTINGS.get("MIN_SPEECH_DURATION", 0.5))  # 最小语音片段时长
        max_speech_samples = int(self.sample_rate * AUDIO_SETTINGS.get("MAX_RECORDING_DURATION", 20.0))  # 最大语音片段时长（最多20秒）
        speech_energy_threshold = AUDIO_SETTINGS.get("SPEECH_ENERGY_THRESHOLD", 0.002)  # 语音能量阈值
        
        # 语音状态
        is_speech = False
        speech_buffer = []
        silence_counter = 0
        # 从配置文件读取最大静音时长，默认为1.5秒
        max_silence_samples = int(self.sample_rate * AUDIO_SETTINGS.get("PAUSE_TOLERANCE", 1.5))
        
        # 限制回复频率，避免重复提问
        last_response_time = 0
        # 从配置文件读取最小回复间隔，默认为2.0秒
        min_response_interval = AUDIO_SETTINGS.get("SPEECH_TIMEOUT", 2.0)
        
        while self.is_recording:
            try:
                # 使用超时来避免无限等待
                audio_data = self.audio_queue.get(timeout=0.5)
                
                # 如果是立体声，转换为单声道
                if audio_data.shape[1] == 2:
                    audio_data = np.mean(audio_data, axis=1)
                
                # 应用简单的噪声门限
                audio_data = np.where(np.abs(audio_data) < silence_threshold, 0, audio_data)
                
                # 计算当前帧的能量
                frame_energy = np.mean(np.abs(audio_data))
                
                if frame_energy > speech_energy_threshold:
                    # 检测到语音
                    if not is_speech:
                        is_speech = True
                        speech_buffer = []
                    silence_counter = 0
                    speech_buffer.extend(audio_data)
                else:
                    # 检测到静音
                    if is_speech:
                        silence_counter += len(audio_data)
                        speech_buffer.extend(audio_data)
                        
                        # 如果静音时长超过阈值或语音长度超过最大值，处理当前语音片段
                        if silence_counter >= max_silence_samples or len(speech_buffer) >= max_speech_samples:
                            if len(speech_buffer) >= min_speech_samples:
                                # 处理语音片段
                                speech_segment = np.array(speech_buffer)
                                # 标准化音频数据
                                speech_segment = speech_segment / (np.max(np.abs(speech_segment)) + 1e-6)
                                # 转写音频
                                text = self.transcribe_audio(speech_segment)
                                if text and self.text_callback:
                                    text = text.strip()
                                    if text and len(text) > 1:  # 只处理有意义的文本
                                        current_time = time.time()
                                        is_question_text = self.is_question(text)
                                        
                                        # 对于问题，检查是否需要响应
                                        if is_question_text:
                                            # 确保回复间隔大于最小间隔
                                            if current_time - last_response_time >= min_response_interval:
                                                self.text_callback(f"问题: {text}\n")
                                                answer = self.get_gpt_response(text)
                                                last_response_time = time.time()  # 更新最后响应时间
                                            else:
                                                # 响应太频繁，仅显示问题
                                                self.text_callback(f"问题: {text} (等待中...)\n")
                                        else:
                                            self.text_callback(f"文本: {text}\n")
                            # 重置状态
                            is_speech = False
                            speech_buffer = []
                            silence_counter = 0
                
            except queue.Empty:
                # 队列超时，继续循环
                continue
            except Exception as e:
                ErrorHandler.handle_error(e, "处理音频数据时出错", self.text_callback)
                    
    def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """使用OpenAI Whisper API转写音频"""
        return ErrorHandler.safe_execute(
            self._transcribe_audio,
            "转写音频时出错",
            self.text_callback,
            audio_data=audio_data
        )
    
    def _transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """内部方法：实际转写实现"""
        # 将音频数据保存为临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, self.sample_rate)
            temp_filename = temp_file.name

        try:
            # 使用OpenAI客户端进行音频转写
            with open(temp_filename, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=WHISPER_SETTINGS['model'],
                    file=audio_file,
                    language=WHISPER_SETTINGS.get('language', 'zh'),
                    prompt=WHISPER_SETTINGS.get('prompt', None),
                    response_format="json"
                )
                return transcript.text.strip()
        finally:
            # 确保临时文件被删除
            try:
                os.unlink(temp_filename)
            except Exception as e:
                print(f"删除临时文件时出错: {e}")
        
    def is_question(self, text: str) -> bool:
        """检测文本是否为问题"""
        # 添加更多的判断条件
        
        # 1. 如果直接包含问号，肯定是问题
        if "?" in text or "？" in text:
            return True
            
        # 2. 检查常见问句关键词
        question_keywords = QUESTION_KEYWORDS + [
            "请", "能否", "可以", "怎样", "多少", "几个", "是不是", 
            "有没有", "为啥", "咋", "有何", "哪些", "啥时", "干嘛"
        ]
        
        if any(keyword in text for keyword in question_keywords):
            return True
            
        # 3. 检查特定的句式模式 (以"请"开头的指令)
        if text.strip().startswith("请") and len(text) > 2:
            return True
            
        # 4. 如果文本很长(超过15个字符)但没有任何问句特征，可能是陈述句
        if len(text) > 15:
            # 长文本但没有明显问句特征，可能是陈述或描述
            return False
            
        # 5. 如果是较短的文本(<=15字符)且没有明显结束符，倾向于认为是问题
        if len(text) <= 15 and not text.endswith(("。", "！", "~", "…")):
            return True
            
        return False
        
    def get_gpt_response(self, question: str) -> str:
        """获取GPT回答，使用流式输出"""
        return ErrorHandler.safe_execute(
            self._get_gpt_response,
            "获取GPT回答时出错",
            self.text_callback,
            question=question,
            default_return="抱歉，无法获取回答。"
        )
    
    def _get_gpt_response(self, question: str) -> str:
        """内部方法：实际GPT调用实现"""
        # 先发送正在处理的提示
        if self.text_callback:
            self.text_callback("回答: ")
            self.text_callback("<stream>🤔 正在思考...")
        
        # 从GPT_SETTINGS中获取所有可用的参数
        completion_params = {
            'model': GPT_SETTINGS['model'],
            'messages': [
                {"role": "system", "content": GPT_SETTINGS['system_prompt']},
                {"role": "user", "content": question}
            ],
            'stream': True  # 启用流式输出
        }
        
        # 可选参数，如果在设置中存在则添加
        optional_params = ['temperature', 'max_tokens', 'top_p', 
                          'frequency_penalty', 'presence_penalty']
        for param in optional_params:
            if param in GPT_SETTINGS:
                completion_params[param] = GPT_SETTINGS[param]
        
        # 用于累积完整的回答
        full_response = ""
        
        # 清除"正在思考"提示
        if self.text_callback:
            self.text_callback("<stream>\r" + " " * 20 + "\r")  # 清除当前行
            time.sleep(0.1)  # 短暂停顿
        
        # 使用流式调用API
        response = self.client.chat.completions.create(**completion_params)
        
        # 逐个处理流式响应的内容
        for chunk in response:
            # 安全地检查是否有内容，避免索引错误
            try:
                if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        full_response += content
                        # 发送带有特殊标记的增量更新
                        if self.text_callback:
                            self.text_callback(f"<stream>{content}")
                        # 小延迟，避免过快刷新
                        time.sleep(0.01)
            except (IndexError, AttributeError) as e:
                print(f"处理流式响应块时出错: {e}")
                continue  # 跳过这个块，继续处理下一个
        
        return full_response 