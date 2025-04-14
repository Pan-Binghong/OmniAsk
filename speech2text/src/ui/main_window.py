"""
主窗口模块
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from .visualizer import AudioVisualizer
from ..audio.audio_processor import AudioProcessor
from ..config.settings import UI_SETTINGS
import threading
import queue
import time
import re

class MainWindow:
    def __init__(self):
        """初始化主窗口"""
        # 创建应用程序窗口
        self.root = ctk.CTk()
        self.root.title(UI_SETTINGS['window_title'])
        self.root.geometry(UI_SETTINGS['window_size'])
        ctk.set_appearance_mode(UI_SETTINGS['theme_mode'])
        
        # 配置行列权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#121212")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置主框架行列权重
        self.main_frame.grid_rowconfigure(0, weight=0)  # 控制区域
        self.main_frame.grid_rowconfigure(1, weight=1)  # 内容区域
        self.main_frame.grid_rowconfigure(2, weight=0)  # 状态栏
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # 创建音频处理器
        self.audio_processor = AudioProcessor()
        
        # 打字机效果相关
        self.typing_queue = queue.Queue()
        self.typing_speed = 20  # 每字符毫秒数（越小越快）
        self.is_typing = False
        
        # 创建线程处理打字机效果
        self.typing_thread = threading.Thread(target=self.process_typing_queue, daemon=True)
        self.typing_thread.start()
        
        # 创建控制区域
        self.control_frame = ctk.CTkFrame(self.main_frame, fg_color="#1a1a1a", height=60)
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.control_frame.grid_propagate(False)
        
        # 创建内容区域
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="#121212")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # 配置内容区域行列权重
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        
        # 创建左右分栏
        self.left_frame = ctk.CTkFrame(self.content_frame, fg_color="#121212")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="#121212")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # 配置左右分栏行列权重
        self.left_frame.grid_rowconfigure(0, weight=0)  # 音频可视化
        self.left_frame.grid_rowconfigure(1, weight=0)  # 可视化控制
        self.left_frame.grid_rowconfigure(2, weight=0)  # 文本标题
        self.left_frame.grid_rowconfigure(3, weight=1)  # 文本区域
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        self.right_frame.grid_rowconfigure(0, weight=0)  # 标题
        self.right_frame.grid_rowconfigure(1, weight=1)  # 回答区域
        self.right_frame.grid_columnconfigure(0, weight=1)
        
        # 创建状态栏
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="#1a1a1a", height=30)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.status_frame.grid_propagate(False)
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="✅ 就绪",
            font=("微软雅黑", 10),
            text_color="#e2e8f0"
        )
        self.status_label.pack(side="left", padx=10)
        
        # 创建各个区域的组件
        self.create_device_selector()
        self.create_control_buttons()
        self.create_volume_indicator()
        self.create_widgets()
        
        # 设置自定义样式
        self.apply_custom_styles()
        
    def setup_window(self):
        """设置窗口基本属性"""
        self.root = ctk.CTk()
        self.root.title(UI_SETTINGS['window_title'])
        self.root.geometry(UI_SETTINGS['window_size'])
        
        # 设置主题
        ctk.set_appearance_mode(UI_SETTINGS['theme_mode'])
        ctk.set_default_color_theme(UI_SETTINGS['color_theme'])
        
        # 创建音频处理器
        self.audio_processor = AudioProcessor()
        
    def setup_styles(self):
        """设置自定义样式"""
        style = ttk.Style()
        
        # 设置Combobox样式
        style.configure(
            "Custom.TCombobox",
            background="#2b2b2b",
            fieldbackground="#2b2b2b",
            foreground="white",
            arrowcolor="white"
        )
        
    def apply_custom_styles(self):
        """应用自定义样式"""
        style = ttk.Style()
        
        # 设置Combobox样式
        style.configure(
            "Custom.TCombobox",
            background="#2b2b2b",
            fieldbackground="#2b2b2b",
            foreground="white",
            arrowcolor="white"
        )
        
    def create_widgets(self):
        """创建界面组件"""
        # 设置两列布局
        self.root.grid_columnconfigure(0, weight=4)  # 左侧占40%
        self.root.grid_columnconfigure(1, weight=6)  # 右侧占60%
        
        # 左侧面板 - 控制区域和问题显示
        self.left_frame = ctk.CTkFrame(self.root)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        self.left_frame.grid_rowconfigure(3, weight=1)  # 文本区域占满剩余空间
        
        # 右侧面板 - 回答显示
        self.right_frame = ctk.CTkFrame(self.root)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)
        self.right_frame.grid_rowconfigure(1, weight=1)  # 文本区域占满剩余空间
        
        # 控制面板容器 - 设置渐变背景
        self.control_frame = ctk.CTkFrame(self.left_frame, fg_color="#1e293b", corner_radius=8)
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # 创建设备选择器
        self.create_device_selector()
        
        # 创建控制按钮
        self.create_control_buttons()
        
        # 状态指示器区域
        self.status_frame = ctk.CTkFrame(self.left_frame, fg_color="#2d3748", corner_radius=8)
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # 状态文本
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="就绪",
            height=25,
            font=("微软雅黑", 11, "bold")
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # 音量指示器 - 使用简化的指示器
        self.create_volume_indicator()
        
        # 左侧文本区域标题
        self.question_title_frame = ctk.CTkFrame(self.left_frame, fg_color="#2d3748", corner_radius=8, height=35)
        self.question_title_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(5,0))
        
        self.question_label = ctk.CTkLabel(
            self.question_title_frame,
            text="📝 识别文本",
            font=("微软雅黑", 12, "bold"),
            text_color="#60a5fa"
        )
        self.question_label.pack(side="left", padx=10, pady=5)
        
        # 左侧文本区域
        self.question_frame = ctk.CTkFrame(self.left_frame, fg_color="#1e293b", corner_radius=8)
        self.question_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        
        # 使用原生tk.Text代替CTkTextbox
        self.question_area = tk.Text(
            self.question_frame,
            wrap="word",
            font=("微软雅黑", 11),
            bg="#1e293b",
            fg="#e2e8f0",
            bd=0,
            padx=10,
            pady=10,
            insertbackground="#ffffff"  # 光标颜色
        )
        self.question_area.pack(fill="both", expand=True, padx=3, pady=3)
        
        # 右侧标题
        self.answer_title_frame = ctk.CTkFrame(self.right_frame, fg_color="#2d3748", corner_radius=8, height=35)
        self.answer_title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.answer_label = ctk.CTkLabel(
            self.answer_title_frame,
            text="🤖 AI 回复",
            font=("微软雅黑", 12, "bold"),
            text_color="#a7f3d0"
        )
        self.answer_label.pack(side="left", padx=10, pady=5)
        
        # 右侧文本区域
        self.answer_frame = ctk.CTkFrame(self.right_frame, fg_color="#1e293b", corner_radius=8)
        self.answer_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # 使用原生tk.Text代替CTkTextbox
        self.answer_area = tk.Text(
            self.answer_frame,
            wrap="word",
            font=("微软雅黑", 11),
            bg="#1e293b",
            fg="#e2e8f0",
            bd=0,
            padx=10,
            pady=10,
            insertbackground="#ffffff"  # 光标颜色
        )
        self.answer_area.pack(fill="both", expand=True, padx=3, pady=3)
        
        # 添加打字速度控制滑块
        self.speed_frame = ctk.CTkFrame(self.control_frame, fg_color="#2d3748", corner_radius=6)
        self.speed_frame.pack(side="right", padx=10, pady=5)
        
        self.speed_label = ctk.CTkLabel(
            self.speed_frame,
            text="⚡ 打字速度",
            font=("微软雅黑", 10, "bold"),
            text_color="#e2e8f0"
        )
        self.speed_label.pack(side="left", padx=5)
        
        self.speed_slider = ctk.CTkSlider(
            self.speed_frame,
            from_=10,
            to=50,
            number_of_steps=40,
            width=80,
            fg_color="#3f4d64",
            button_color="#60a5fa",
            button_hover_color="#93c5fd",
            command=self.adjust_typing_speed
        )
        self.speed_slider.set(self.typing_speed)
        self.speed_slider.pack(side="left", padx=5)
        
        # 设置文本标签样式 - 现在可以使用tag_configure了
        self.question_area.tag_configure("question", foreground="#60a5fa", font=("微软雅黑", 11, "bold"))
        self.question_area.tag_configure("transcription", foreground="#e2e8f0", font=("微软雅黑", 11))
        self.question_area.tag_configure("system", foreground="#94a3b8", font=("微软雅黑", 10))
        self.question_area.tag_configure("error", foreground="#f87171", font=("微软雅黑", 10, "bold"))
        
        self.answer_area.tag_configure("answer", foreground="#a7f3d0", font=("微软雅黑", 11))
        self.answer_area.tag_configure("answer_bold", foreground="#a7f3d0", font=("微软雅黑", 12, "bold"))
        self.answer_area.tag_configure("list_item", foreground="#a7f3d0", font=("微软雅黑", 11), lmargin1=20, lmargin2=30)
        self.answer_area.tag_configure("error", foreground="#f87171", font=("微软雅黑", 10, "bold"))
        
        # 显示欢迎消息
        self.question_area.insert("end", "👋 欢迎使用实时语音助手！\n请选择音频设备并点击开始按钮。\n\n", "system")
        self.answer_area.insert("end", "🤖 我是您的AI助手，我会回答您的问题。\n\n", "answer")
        
        # 设置回调
        self.audio_processor.text_callback = self.update_text
        self.audio_processor.volume_callback = self.update_volume
        
    def create_volume_indicator(self):
        """创建简单的音量指示器"""
        self.volume_indicator_frame = ctk.CTkFrame(self.status_frame, fg_color="#1e293b", corner_radius=6, height=25)
        self.volume_indicator_frame.pack(side="right", padx=10, pady=5, fill="x", expand=True)
        
        # 创建音量指示灯
        self.indicators = []
        self.indicator_colors = ["#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8", "#1e40af"]
        
        self.indicator_container = ctk.CTkFrame(self.volume_indicator_frame, fg_color="#1e293b")
        self.indicator_container.pack(fill="both", expand=True)
        
        for i in range(10):
            color = self.indicator_colors[min(i//2, len(self.indicator_colors)-1)]
            indicator = ctk.CTkFrame(
                self.indicator_container, 
                width=6, 
                height=16, 
                fg_color="#2d3748",
                corner_radius=3
            )
            indicator.pack(side="left", padx=1, pady=0)
            self.indicators.append(indicator)
            
    def update_volume(self, volume):
        """更新音量指示器"""
        # 将音量值转换为0-10的范围
        level = min(10, int(volume * 300))
        
        # 更新指示灯状态
        for i, indicator in enumerate(self.indicators):
            if i < level:
                color = self.indicator_colors[min(i//2, len(self.indicator_colors)-1)]
                indicator.configure(fg_color=color)
            else:
                indicator.configure(fg_color="#333333")
        
    def create_device_selector(self):
        """创建设备选择器"""
        # 获取设备列表
        self.devices = self.audio_processor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            prefix = {
                "output": "🔊 输出",
                "input": "🎤 输入",
                "app": "📱 应用"
            }.get(device_type, "📌 其他")
            device_names.append(f"{device_type}:{id}:{prefix}: {name}")
        
        # 设备选择器标签
        self.device_label = ctk.CTkLabel(
            self.control_frame,
            text="🎧 音频源:",
            font=("微软雅黑", 11, "bold"),
            text_color="#e2e8f0"
        )
        self.device_label.pack(side="left", padx=(10, 5))
        
        # 创建下拉框
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.device_var,
            values=device_names,
            width=30,
            style="Custom.TCombobox"
        )
        if device_names:
            self.device_combo.set(device_names[0])
        self.device_combo.pack(side="left", padx=5)
        
    def create_control_buttons(self):
        """创建控制按钮"""
        # 刷新按钮
        self.refresh_button = ctk.CTkButton(
            self.control_frame,
            text="刷新",
            width=70,
            height=32,
            command=self.refresh_devices,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            text_color="#ffffff",
            corner_radius=6,
            font=("微软雅黑", 11, "bold")
        )
        self.refresh_button.pack(side="left", padx=5)
        
        # 开始按钮
        self.start_button = ctk.CTkButton(
            self.control_frame,
            text="开始",
            width=70,
            height=32,
            command=self.start_monitoring,
            fg_color="#22c55e",
            hover_color="#16a34a",
            text_color="#ffffff",
            corner_radius=6,
            font=("微软雅黑", 11, "bold")
        )
        self.start_button.pack(side="left", padx=5)
        
        # 停止按钮
        self.stop_button = ctk.CTkButton(
            self.control_frame,
            text="停止",
            width=70,
            height=32,
            command=self.stop_monitoring,
            state="disabled",
            fg_color="#ef4444",
            hover_color="#dc2626",
            text_color="#ffffff",
            corner_radius=6,
            font=("微软雅黑", 11, "bold")
        )
        self.stop_button.pack(side="left", padx=5)
        
    def update_text(self, text):
        """更新文本显示，处理流式输出和普通文本"""
        if "当前音量级别" not in text:
            # 处理流式输出
            if text.startswith("<stream>"):
                content = text[8:]  # 移除<stream>标记
                # 处理特殊的回车符清除指令
                if content.startswith("\r"):
                    # 获取最后一行
                    end_index = self.answer_area.index("end-1c")
                    last_line_start = self.answer_area.index(f"{end_index} linestart")
                    # 删除最后一行
                    self.answer_area.delete(last_line_start, end_index)
                    # 移除回车符后再处理剩余内容
                    content = content.lstrip("\r").lstrip(" ").lstrip("\r")
                    if not content:  # 如果没有剩余内容，直接返回
                        return
                
                # 将流式内容添加到打字队列
                self.typing_queue.put((content, "answer", True, True))  # 最后参数表示是否需要markdown渲染
                return
            
            # 根据内容类型将文本添加到相应的区域
            if "问题:" in text:
                # 记录当前问题ID，保证答案对应到正确的问题
                question_text = text.replace("问题:", "").strip()
                
                # 添加分隔线使问题更明显
                self.typing_queue.put(("\n" + "─"*40 + "\n", "system", False, False))
                
                # 添加带编号的问题
                formatted_question = f"问题: {question_text}\n"
                self.typing_queue.put((formatted_question, "question", False, False))
                
                # 同时在右侧添加问题提示
                self.typing_queue.put((f"针对问题: {question_text}\n", "system", True, False))
                
            elif "文本:" in text:
                self.typing_queue.put((text + "\n", "transcription", False, False))
            elif "回答:" in text:
                # 只添加"回答:"标记，实际内容通过流式输出显示
                self.typing_queue.put(("", "answer", True, False))
            elif "错误" in text or "失败" in text:
                # 错误信息同时显示在两边
                self.typing_queue.put(("\n❌ " + text + "\n", "error", False, False))
                self.typing_queue.put(("\n❌ " + text + "\n", "error", True, False))
                self.status_label.configure(text="❌ 出现错误", text_color="#f87171")
            else:
                # 系统消息显示在问题区域
                self.typing_queue.put((text + "\n", "system", False, False))
            
            # 更新状态标签
            if "开始" in text:
                self.status_label.configure(text="🎵 正在录音...", text_color="#60a5fa")
            elif "停止" in text:
                self.status_label.configure(text="⏹ 已停止", text_color="#f87171")
    
    def parse_markdown(self, text):
        """简单的Markdown解析函数"""
        # 替换粗体 **text** -> 添加bold标签
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # 替换代码块
        if '```' in text:
            text = text.replace('```', '')
        
        # 处理列表前的数字和点
        text = re.sub(r'^\d+\.\s', '', text)
        
        return text
    
    def process_typing_queue(self):
        """处理打字机效果队列"""
        while True:
            try:
                # 获取下一个要显示的字符和相关信息
                text, tag, is_stream, is_markdown = self.typing_queue.get(timeout=0.1)
                self.is_typing = True
                
                # 选择目标文本区域
                target_area = self.answer_area if is_stream else self.question_area
                
                # 如果是空文本，直接跳过
                if not text:
                    self.typing_queue.task_done()
                    self.is_typing = False
                    continue
                
                # 确保样式标签已创建
                if not hasattr(self, 'markdown_tags_created'):
                    target_area.tag_configure("bold", font=("微软雅黑", 11, "bold"), foreground="#a7f3d0")
                    target_area.tag_configure("code", font=("Consolas", 10), background="#2d3748", foreground="#a7f3d0")
                    target_area.tag_configure("list", lmargin1=20, lmargin2=30, foreground="#a7f3d0")
                    target_area.tag_configure("answer_bold", font=("微软雅黑", 12, "bold"), foreground="#a7f3d0")
                    self.markdown_tags_created = True
                
                # 检测并处理markdown格式
                if is_markdown and is_stream:
                    # 简化处理流程，不再尝试预处理所有markdown格式
                    # 直接按行逐字符输出，在过程中处理特殊格式
                    
                    # 按行处理文本
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        # 检查是否是列表项
                        list_match = re.match(r'^(\d+\.\s)(.*?)$', line)
                        if list_match:
                            # 列表项处理为点标记
                            target_area.insert("end", "• ", "list_item")
                            # 显示列表内容
                            content = list_match.group(2)
                            for char in content:
                                target_area.insert("end", char, "list_item")
                                target_area.see("end")
                                time.sleep(self.typing_speed / 1000)
                        else:
                            # 普通文本行，可能包含粗体
                            # 拆分成普通文本和粗体文本段
                            parts = []
                            # 按粗体格式拆分
                            segments = re.split(r'(\*\*.*?\*\*)', line)
                            for segment in segments:
                                bold_match = re.match(r'\*\*(.*?)\*\*', segment)
                                if bold_match:
                                    # 粗体文本
                                    parts.append(("bold", bold_match.group(1)))
                                else:
                                    # 普通文本
                                    if segment:  # 确保不是空字符串
                                        parts.append(("normal", segment))
                            
                            # 显示处理后的各个部分
                            for part_type, part_text in parts:
                                if part_type == "bold":
                                    # 粗体文本
                                    for char in part_text:
                                        target_area.insert("end", char, "answer_bold")
                                        target_area.see("end")
                                        time.sleep(self.typing_speed / 1000)
                                else:
                                    # 普通文本
                                    for char in part_text:
                                        target_area.insert("end", char, tag)
                                        target_area.see("end")
                                        time.sleep(self.typing_speed / 1000)
                        
                        # 除了最后一行外，所有行末尾添加换行符
                        if i < len(lines) - 1:
                            target_area.insert("end", "\n", tag)
                else:
                    # 非markdown内容，逐字显示文本
                    for char in text:
                        target_area.insert("end", char, tag)
                        target_area.see("end")
                        time.sleep(self.typing_speed / 1000)
                
                # 确保文本区域滚动到最新内容
                target_area.see("end")
                
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
    
    def refresh_devices(self):
        """刷新设备列表"""
        self.devices = self.audio_processor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            prefix = {
                "output": "🔊 输出",
                "input": "🎤 输入",
                "app": "📱 应用"
            }.get(device_type, "📌 其他")
            device_names.append(f"{device_type}:{id}:{prefix}: {name}")
            
        self.device_combo.configure(values=device_names)
        if device_names:
            self.device_combo.set(device_names[0])
        self.update_text("已刷新设备列表\n")
        self.status_label.configure(text="📝 已更新设备列表", text_color="#00B4D8")
        
    def start_monitoring(self):
        """开始监听"""
        if not self.device_var.get():
            self.update_text("请先选择音频来源！\n")
            return
            
        try:
            device_type, device_id, _ = self.device_var.get().split(':', 2)
            device_id = int(device_id)
            
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.audio_processor.start_recording(device_type, device_id)
            self.update_text("开始监听...\n")
        except Exception as e:
            self.update_text(f"启动失败: {str(e)}\n")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            
    def stop_monitoring(self):
        """停止监听"""
        self.audio_processor.stop_recording()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_text("停止监听。\n")
        
    def run(self):
        """运行主程序"""
        self.root.mainloop() 