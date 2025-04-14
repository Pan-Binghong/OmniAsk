"""
UI样式工具模块
提供统一的UI样式定义
"""

class UIColors:
    """UI颜色定义"""
    # 主要颜色
    PRIMARY = "#3b82f6"       # 主色调-蓝色
    PRIMARY_DARK = "#2563eb"  # 主色调-深蓝
    PRIMARY_LIGHT = "#60a5fa" # 主色调-浅蓝
    
    # 背景颜色
    BG_DARK = "#1e293b"       # 主背景-深色
    BG_MEDIUM = "#2d3748"     # 次背景-中深
    BG_LIGHT = "#3f4d64"      # 轻背景-中浅
    
    # 文本颜色
    TEXT_PRIMARY = "#e2e8f0"  # 主文本-浅色
    TEXT_SECONDARY = "#94a3b8"# 次文本-灰色
    TEXT_MUTED = "#64748b"    # 弱文本-深灰
    
    # 功能颜色
    SUCCESS = "#22c55e"       # 成功-绿色
    SUCCESS_DARK = "#16a34a"  # 深绿色
    WARNING = "#f59e0b"       # 警告-橙色
    ERROR = "#ef4444"         # 错误-红色
    ERROR_DARK = "#dc2626"    # 深红色
    
    # 输出类型颜色
    QUESTION = "#60a5fa"      # 问题-蓝色
    ANSWER = "#a7f3d0"        # 回答-绿色
    SYSTEM = "#94a3b8"        # 系统-灰色
    TRANSCRIPTION = "#e2e8f0" # 转写-白色
    ERROR_TEXT = "#f87171"    # 错误-红色

class UIStyles:
    """UI样式定义"""
    
    # 字体设置
    FONT_FAMILY = "微软雅黑"
    FONT_NORMAL = ("微软雅黑", 11)
    FONT_BOLD = ("微软雅黑", 11, "bold")
    FONT_SMALL = ("微软雅黑", 10)
    FONT_TITLE = ("微软雅黑", 12, "bold")
    
    # 圆角半径
    CORNER_RADIUS_LARGE = 8
    CORNER_RADIUS_MEDIUM = 6
    CORNER_RADIUS_SMALL = 3
    
    # 内边距
    PADDING_LARGE = 10
    PADDING_MEDIUM = 5
    PADDING_SMALL = 2
    
    # 按钮样式
    BUTTON_WIDTH = 70
    BUTTON_HEIGHT = 32
    
    # 图标
    ICONS = {
        "app": "📱",
        "question": "📝",
        "answer": "🤖",
        "mic": "🎤",
        "speaker": "🔊",
        "refresh": "🔄",
        "start": "▶️",
        "stop": "⏹",
        "error": "❌",
        "recording": "🎵",
        "waiting": "🤔",
        "success": "✅",
        "speed": "⚡",
        "audio_source": "🎧",
        "other": "📌",
        "welcome": "👋"
    }
    
    @classmethod
    def get_frame_style(cls, style_type="normal"):
        """获取框架样式"""
        styles = {
            "normal": {
                "fg_color": UIColors.BG_DARK,
                "corner_radius": cls.CORNER_RADIUS_LARGE
            },
            "header": {
                "fg_color": UIColors.BG_MEDIUM,
                "corner_radius": cls.CORNER_RADIUS_LARGE,
                "height": 35
            },
            "control": {
                "fg_color": UIColors.BG_MEDIUM,
                "corner_radius": cls.CORNER_RADIUS_MEDIUM
            }
        }
        return styles.get(style_type, styles["normal"])
    
    @classmethod
    def get_button_style(cls, style_type="primary"):
        """获取按钮样式"""
        styles = {
            "primary": {
                "fg_color": UIColors.PRIMARY,
                "hover_color": UIColors.PRIMARY_DARK,
                "text_color": UIColors.TEXT_PRIMARY,
                "corner_radius": cls.CORNER_RADIUS_MEDIUM,
                "font": cls.FONT_BOLD,
                "width": cls.BUTTON_WIDTH,
                "height": cls.BUTTON_HEIGHT
            },
            "success": {
                "fg_color": UIColors.SUCCESS,
                "hover_color": UIColors.SUCCESS_DARK,
                "text_color": UIColors.TEXT_PRIMARY,
                "corner_radius": cls.CORNER_RADIUS_MEDIUM,
                "font": cls.FONT_BOLD,
                "width": cls.BUTTON_WIDTH,
                "height": cls.BUTTON_HEIGHT
            },
            "danger": {
                "fg_color": UIColors.ERROR,
                "hover_color": UIColors.ERROR_DARK,
                "text_color": UIColors.TEXT_PRIMARY,
                "corner_radius": cls.CORNER_RADIUS_MEDIUM,
                "font": cls.FONT_BOLD,
                "width": cls.BUTTON_WIDTH,
                "height": cls.BUTTON_HEIGHT
            }
        }
        return styles.get(style_type, styles["primary"])
    
    @classmethod
    def get_text_style(cls, style_type="normal"):
        """获取文本样式"""
        styles = {
            "normal": {
                "font": cls.FONT_NORMAL,
                "text_color": UIColors.TEXT_PRIMARY
            },
            "title": {
                "font": cls.FONT_TITLE,
                "text_color": UIColors.PRIMARY_LIGHT
            },
            "small": {
                "font": cls.FONT_SMALL,
                "text_color": UIColors.TEXT_SECONDARY
            },
            "success": {
                "font": cls.FONT_BOLD,
                "text_color": UIColors.SUCCESS
            },
            "error": {
                "font": cls.FONT_BOLD,
                "text_color": UIColors.ERROR_TEXT
            }
        }
        return styles.get(style_type, styles["normal"])
    
    @classmethod
    def get_text_area_style(cls):
        """获取文本区域样式"""
        return {
            "bg": UIColors.BG_DARK,
            "fg": UIColors.TEXT_PRIMARY,
            "bd": 0,
            "padx": cls.PADDING_LARGE,
            "pady": cls.PADDING_LARGE,
            "insertbackground": UIColors.TEXT_PRIMARY,
            "font": cls.FONT_NORMAL
        }
    
    @classmethod
    def get_tag_styles(cls):
        """获取文本标签样式"""
        return {
            "question": {"foreground": UIColors.QUESTION, "font": cls.FONT_BOLD},
            "answer": {"foreground": UIColors.ANSWER, "font": cls.FONT_NORMAL},
            "transcription": {"foreground": UIColors.TRANSCRIPTION, "font": cls.FONT_NORMAL},
            "system": {"foreground": UIColors.SYSTEM, "font": cls.FONT_SMALL},
            "error": {"foreground": UIColors.ERROR_TEXT, "font": ("微软雅黑", 10, "bold")}
        } 