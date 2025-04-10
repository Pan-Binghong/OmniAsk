"""
配置文件，包含所有全局设置
"""

# 音频设置
AUDIO_SETTINGS = {
    'sample_rate': 16000,
    'channels': 2,
    'chunk_duration': 0.1,
    'buffer_duration': 2.0,
}

# 界面设置
UI_SETTINGS = {
    'window_title': '实时音频监控系统',
    'window_size': '800x600',
    'theme_mode': 'dark',
    'color_theme': 'blue',
    'text_area_height': 150,
    'visualizer_height': 200,
}

# 音频可视化设置
VISUALIZER_SETTINGS = {
    'figure_size': (10, 3),
    'dpi': 100,
    'update_interval': 30,
    'data_points': 200,
}

# Whisper设置
WHISPER_SETTINGS = {
    'model': 'whisper-1',
    'response_format': 'text',
    'prompt': '这是一段中文音频，可能包含问题',
}

# GPT设置
GPT_SETTINGS = {
    'model': 'gpt-4o-mini',
    'max_tokens': 1024,
    'system_prompt': '你是一个专业的助手，请简洁地回答问题。',
}

# 问题检测关键词
QUESTION_KEYWORDS = ['什么', '如何', '为什么', '怎么', '哪些', '?', '？','请你'] 