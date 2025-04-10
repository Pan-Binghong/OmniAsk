"""
主窗口模块
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from .visualizer import AudioVisualizer
from ..audio.audio_processor import AudioProcessor
from ..config.settings import UI_SETTINGS

class MainWindow:
    def __init__(self):
        """初始化主窗口"""
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        
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
        
    def create_widgets(self):
        """创建界面组件"""
        # 顶部控制区域
        self.create_control_panel()
        
        # 中间的音频可视化区域
        self.create_visualizer()
        
        # 底部的文本显示区域
        self.create_text_area()
        
    def create_control_panel(self):
        """创建控制面板"""
        # 控制面板容器
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(fill="x", padx=10, pady=5)
        
        # 设备选择下拉框
        self.create_device_selector()
        
        # 控制按钮
        self.create_control_buttons()
        
    def create_device_selector(self):
        """创建设备选择器"""
        # 获取设备列表
        self.devices = self.audio_processor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            prefix = {
                "output": "输出",
                "input": "输入",
                "app": "应用"
            }.get(device_type, "其他")
            device_names.append(f"{device_type}:{id}:{prefix}: {name}")
        
        # 创建下拉框
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.device_var,
            values=device_names,
            width=50,
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
            width=80,
            command=self.refresh_devices,
            fg_color="#404040",
            hover_color="#505050"
        )
        self.refresh_button.pack(side="left", padx=5)
        
        # 开始按钮
        self.start_button = ctk.CTkButton(
            self.control_frame,
            text="开始",
            width=80,
            command=self.start_monitoring,
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.start_button.pack(side="left", padx=5)
        
        # 停止按钮
        self.stop_button = ctk.CTkButton(
            self.control_frame,
            text="停止",
            width=80,
            command=self.stop_monitoring,
            state="disabled",
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.stop_button.pack(side="left", padx=5)
        
    def create_visualizer(self):
        """创建音频可视化区域"""
        self.viz_frame = ctk.CTkFrame(self.root)
        self.viz_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.visualizer = AudioVisualizer(self.viz_frame, self.audio_processor)
        
    def create_text_area(self):
        """创建文本显示区域"""
        self.text_area = ctk.CTkTextbox(
            self.root,
            wrap="word",
            height=UI_SETTINGS['text_area_height'],
            font=("微软雅黑", 12)
        )
        self.text_area.pack(fill="x", padx=10, pady=5)
        
        # 设置文本区域的样式
        self.text_area.configure(
            text_color="white",
            fg_color="#1e1e1e",
            border_color="#404040",
            border_width=1
        )
        
        # 设置回调
        self.audio_processor.text_callback = self.update_text
        
    def update_text(self, text):
        """更新文本显示"""
        if "当前音量级别" not in text:
            self.text_area.insert("end", text)
            self.text_area.see("end")
            
            # 保持最新的几行
            content = self.text_area.get("1.0", "end-1c").split("\n")
            if len(content) > 10:
                self.text_area.delete("1.0", "end")
                self.text_area.insert("1.0", "\n".join(content[-10:]) + "\n")
                
    def refresh_devices(self):
        """刷新设备列表"""
        self.devices = self.audio_processor.get_available_devices()
        device_names = []
        for device_type, id, name in self.devices:
            prefix = {
                "output": "输出",
                "input": "输入",
                "app": "应用"
            }.get(device_type, "其他")
            device_names.append(f"{device_type}:{id}:{prefix}: {name}")
            
        self.device_combo.configure(values=device_names)
        if device_names:
            self.device_combo.set(device_names[0])
        self.update_text("已刷新设备列表\n")
        
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