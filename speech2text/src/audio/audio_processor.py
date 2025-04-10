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
from typing import Optional, List, Dict
from openai import OpenAI
import psutil
import win32gui
import win32process
from ..config.settings import AUDIO_SETTINGS, WHISPER_SETTINGS, GPT_SETTINGS, QUESTION_KEYWORDS

# 用于multipart/form-data请求的boundary
BOUNDARY = '----WebKitFormBoundary' + ''.join(['1234567890', 'abcdefghijklmnopqrstuvwxyz'][:10])

# 问题关键词
QUESTION_KEYWORDS = ['吗', '?', '？', '什么', '为什么', '如何', '怎么', '哪里', '谁', '何时', '是否']

class AudioProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL')
        )
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.text_callback = None
        
        # 从配置文件加载设置
        self.sample_rate = AUDIO_SETTINGS['sample_rate']
        self.channels = AUDIO_SETTINGS['channels']
        self.chunk_duration = AUDIO_SETTINGS['chunk_duration']
        self.buffer_duration = AUDIO_SETTINGS['buffer_duration']
        
        self.audio_buffer = []
        self.latest_audio_data = np.array([])
        self.current_device = None
        
    def get_audio_devices(self):
        """获取所有音频设备"""
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
        
    def get_audio_applications(self):
        """获取正在播放音频的应用程序"""
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
        
    def get_available_devices(self):
        """获取所有可用的音频设备和应用程序"""
        devices = self.get_audio_devices()
        for pid, app_name in self.get_audio_applications():
            devices.append(("app", pid, app_name))
        return devices
        
    def start_recording(self, device_type, device_id):
        """开始录音"""
        self.is_recording = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"音频回调状态: {status}")
            self.audio_queue.put(indata.copy())
            
        def record_audio():
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
                    'callback': audio_callback,
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
                print(error_msg)
                if self.text_callback:
                    self.text_callback(error_msg)
                self.is_recording = False
                
        self.record_thread = threading.Thread(target=record_audio)
        self.process_thread = threading.Thread(target=self.process_audio)
        
        self.record_thread.start()
        self.process_thread.start()
        
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
            print(f"停止录音时出错: {e}")
        finally:
            print("录音已停止")
            
    def process_audio(self):
        """处理音频数据"""
        buffer_samples = int(self.sample_rate * self.buffer_duration)
        silence_threshold = 0.001  # 静音阈值
        
        while self.is_recording:
            try:
                # 使用超时来避免无限等待
                audio_data = self.audio_queue.get(timeout=0.5)
                
                # 如果是立体声，转换为单声道
                if audio_data.shape[1] == 2:
                    audio_data = np.mean(audio_data, axis=1)
                
                self.latest_audio_data = audio_data
                self.audio_buffer.extend(audio_data)
                
                # 当缓冲区达到指定大小时处理音频
                if len(self.audio_buffer) >= buffer_samples:
                    audio_segment = np.array(self.audio_buffer[:buffer_samples])
                    self.audio_buffer = self.audio_buffer[buffer_samples:]
                    
                    # 计算音量级别
                    volume_level = np.abs(audio_segment).mean()
                    
                    # 只处理非静音的音频
                    if volume_level > silence_threshold:
                        # 标准化音频数据
                        audio_segment = audio_segment / np.max(np.abs(audio_segment))
                        
                        # 转写音频
                        text = self.transcribe_audio(audio_segment)
                        if text and self.text_callback:
                            if self.is_question(text):
                                answer = self.get_gpt_response(text)
                                self.text_callback(f"问题: {text}\n回答: {answer}\n")
                            else:
                                self.text_callback(f"文本: {text}\n")
                                
            except queue.Empty:
                # 队列超时，继续循环
                continue
            except Exception as e:
                print(f"处理错误: {e}")
                if self.text_callback:
                    self.text_callback(f"错误: {str(e)}\n")
                # 不要因为处理错误就退出循环
                    
    def transcribe_audio(self, audio_data):
        """
        使用 OpenAI Whisper API 将音频转写为文本
        
        Args:
            audio_data: 音频数据
            
        Returns:
            str: 转写的文本，如果失败则返回 None
        """
        try:
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

        except Exception as e:
            print(f"转写过程中出错: {str(e)}")
            return None
        
    def is_question(self, text):
        """检测文本是否为问题"""
        return any(keyword in text for keyword in QUESTION_KEYWORDS)
        
    def get_gpt_response(self, question):
        """获取GPT回答"""
        try:
            # 从GPT_SETTINGS中获取所有可用的参数
            completion_params = {
                'model': GPT_SETTINGS['model'],
                'messages': [
                    {"role": "system", "content": GPT_SETTINGS['system_prompt']},
                    {"role": "user", "content": question}
                ]
            }
            
            # 可选参数，如果在设置中存在则添加
            optional_params = ['temperature', 'max_tokens', 'top_p', 
                             'frequency_penalty', 'presence_penalty']
            for param in optional_params:
                if param in GPT_SETTINGS:
                    completion_params[param] = GPT_SETTINGS[param]

            # 调用API
            response = self.client.chat.completions.create(**completion_params)
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT API 错误: {e}")
            return "抱歉，获取答案时出现错误。" 