"""
音频可视化模块
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from ..config.settings import VISUALIZER_SETTINGS
import matplotlib.font_manager as fm
import matplotlib

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 使用微软雅黑
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class AudioVisualizer:
    def __init__(self, frame, audio_processor):
        """
        初始化音频可视化器
        
        Args:
            frame: tkinter框架
            audio_processor: 音频处理器实例
        """
        self.frame = frame
        self.audio_processor = audio_processor
        self.setup_plot()
        
    def setup_plot(self):
        """设置matplotlib图表"""
        # 创建图形
        self.fig = Figure(
            figsize=VISUALIZER_SETTINGS['figure_size'],
            dpi=VISUALIZER_SETTINGS['dpi']
        )
        
        # 设置样式
        self.fig.patch.set_facecolor('#2b2b2b')  # 深色背景
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')  # 深色背景
        
        # 设置轴范围和标签
        self.ax.set_ylim(-1, 1)
        self.ax.set_xlim(0, VISUALIZER_SETTINGS['data_points'])
        self.ax.set_title('音频波形', color='white', fontsize=12)
        
        # 设置网格
        self.ax.grid(True, color='#404040', linestyle='--', alpha=0.5)
        
        # 设置轴标签颜色
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        
        # 创建波形线
        self.line, = self.ax.plot([], [], lw=2, color='#00ff00')  # 绿色波形
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # 初始化数据
        self.data = np.zeros(VISUALIZER_SETTINGS['data_points'])
        
        # 创建动画
        self.animation = animation.FuncAnimation(
            self.fig,
            self.update_plot,
            interval=VISUALIZER_SETTINGS['update_interval'],
            blit=True,
            save_count=100  # 限制缓存帧数
        )
            
    def update_plot(self, frame):
        """更新图表数据"""
        if hasattr(self.audio_processor, 'latest_audio_data'):
            new_data = self.audio_processor.latest_audio_data
            if len(new_data) > 0:
                # 重采样数据以匹配显示点数
                target_size = VISUALIZER_SETTINGS['data_points']
                step = max(1, len(new_data) // target_size)
                resampled_data = new_data[::step][:target_size]
                
                if len(resampled_data) < target_size:
                    resampled_data = np.pad(
                        resampled_data,
                        (0, target_size - len(resampled_data)),
                        'constant'
                    )
                
                # 更新数据
                self.data = resampled_data
                
                # 应用平滑处理
                self.data = np.convolve(
                    self.data,
                    np.ones(5)/5,  # 5点移动平均
                    mode='same'
                )
        
        self.line.set_data(
            np.arange(len(self.data)),
            self.data
        )
        return self.line, 