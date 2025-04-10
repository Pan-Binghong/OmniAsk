"""
程序入口
"""

from dotenv import load_dotenv
from .ui.main_window import MainWindow

def main():
    # 加载环境变量
    load_dotenv()
    
    # 创建并运行主窗口
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main() 