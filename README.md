# OmniAsk

OmniAsk 是一个实时音频监控和问答系统，可以捕获 Windows 应用程序的音频输出并使用 GPT 进行智能问答。

## 特性

- 实时音频捕获：支持捕获指定 Windows 应用程序的音频输出
- 智能语音识别：使用 OpenAI Whisper 进行准确的语音转文字
- GPT 问答：自动检测问题并使用 GPT 模型生成回答
- 多设备支持：支持 WASAPI 和 DirectSound 音频设备
- 灵活配置：可自定义音频设置、模型参数等

## 安装要求

- Python 3.8 或更高版本
- Windows 10/11 操作系统
- VB-CABLE Virtual Audio Device（用于应用程序音频捕获）

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/OmniAsk.git
cd OmniAsk
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 安装 VB-CABLE：
- 从 [VB-CABLE 官网](https://vb-audio.com/Cable/) 下载并安装
- 重启电脑以确保驱动正确加载

5. 配置环境变量：
- 创建 `.env` 文件并设置以下变量：
```
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=your_api_base_url
```

## 使用方法

1. 启动程序：
```bash
python -m speech2text.src
```

2. 配置音频设备：
- 在 Windows 声音设置中启用 "CABLE Output"
- 在设备属性中启用 "侦听此设备"
- 选择您的耳机作为回放设备

3. 使用程序：
- 选择要监听的应用程序或音频设备
- 开始录音后，系统会自动识别语音并转换为文字
- 当检测到问题时，会自动使用 GPT 生成回答

## 配置说明

配置文件位于 `speech2text/src/config/settings.py`：

- `AUDIO_SETTINGS`：音频采集参数
- `WHISPER_SETTINGS`：Whisper API 设置
- `GPT_SETTINGS`：GPT 模型参数
- `QUESTION_KEYWORDS`：问题检测关键词

## 故障排除

1. 听不到声音：
- 确保耳机设为默认播放设备
- 检查 "CABLE Output" 的侦听功能是否启用
- 验证系统和应用程序音量

2. 无法捕获音频：
- 确保 VB-CABLE 正确安装
- 检查应用程序的音频输出设置
- 尝试重启应用程序或电脑

3. API 错误：
- 验证环境变量是否正确设置
- 检查网络连接
- 确认 API 密钥是否有效

## 贡献指南

欢迎提交 Pull Requests！对于重大更改，请先开 Issue 讨论您想要更改的内容。

## 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件
