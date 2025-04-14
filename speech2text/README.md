# OmniAsk 实时语音助手

一个基于OpenAI Whisper和GPT的实时语音识别和问答系统，能够监听音频输入，识别语音内容，并智能回答问题。

## 特性

- 实时语音监听和识别
- 自动检测问题并提供AI回答
- 流式输出，逐字显示响应
- 多种音频输入源支持：麦克风、系统声音和应用程序
- 优雅的用户界面，支持双栏显示问题和回答
- 音量实时可视化
- 可调节的打字速度

## 环境要求

- Python 3.8+
- VB-CABLE Virtual Audio Driver（用于捕获系统音频）
- OpenAI API密钥

## 安装

1. 克隆代码库
```bash
git clone https://github.com/yourusername/OmniAsk.git
cd OmniAsk
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境
创建.env文件，设置OpenAI API密钥：
```
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

4. 安装VB-CABLE（用于系统声音捕获）
- 访问[VB-CABLE下载页面](https://vb-audio.com/Cable/)
- 下载并安装驱动
- 在Windows声音设置中将VB-CABLE设为默认音频输出设备
- 在VB-CABLE Output属性中启用"侦听此设备"

## 使用方法

运行程序：
```bash
python -m speech2text.src
```

1. 选择音频源：
   - 麦克风输入（用于直接对话）
   - 系统声音输出（用于监听系统播放的内容）
   - 应用程序（用于监听特定应用的音频）

2. 点击"开始"按钮开始监听

3. 说话或播放音频，系统会自动识别内容
   - 普通语句会显示为"文本"
   - 问题会触发AI回答

4. 使用滑块调整打字速度

## 项目结构

```
speech2text/
├── src/                  # 源代码目录
│   ├── __main__.py       # 主入口点
│   ├── audio/            # 音频处理模块
│   │   └── audio_processor.py  # 音频处理器
│   ├── config/           # 配置文件
│   │   └── settings.py   # 设置和参数
│   ├── ui/               # 用户界面
│   │   ├── main_window.py  # 主窗口
│   │   ├── visualizer.py   # 音频可视化
│   │   └── styles.py       # UI样式
│   └── utils/            # 工具模块
│       └── error_handler.py  # 错误处理
├── .env                  # 环境变量（不提交到版本控制）
├── .gitignore            # Git忽略文件
└── README.md             # 项目说明
```

## 示例

```python
# 使用示例
from speech2text.src.ui.main_window import MainWindow

def main():
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()
```

## 常见问题

1. Q: 系统不能检测到音频输入？
   A: 确保麦克风已正确连接，并在系统设置中启用。

2. Q: 使用VB-CABLE监听系统声音时没有响应？
   A: 确保已将VB-CABLE设为默认音频输出，并在其属性中启用"侦听此设备"。

3. Q: API调用错误？
   A: 检查.env文件中的API密钥是否正确设置。

## 许可

MIT 许可证
