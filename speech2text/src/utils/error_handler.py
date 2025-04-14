"""
错误处理工具模块
提供统一的错误处理机制
"""

import logging
import traceback
from typing import Callable, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('speech2text')

class ErrorHandler:
    """错误处理类，提供统一的错误处理机制"""
    
    @staticmethod
    def handle_error(
        error: Exception, 
        context: str = "", 
        callback: Optional[Callable[[str], Any]] = None
    ) -> str:
        """
        处理异常并生成统一的错误消息
        
        参数:
            error: 捕获到的异常
            context: 错误发生的上下文说明
            callback: 可选的回调函数，用于将错误消息发送到UI
            
        返回:
            格式化的错误消息
        """
        # 生成错误消息
        error_type = type(error).__name__
        error_message = str(error)
        error_trace = traceback.format_exc()
        
        # 构建格式化的错误信息
        formatted_message = f"错误 [{error_type}]: {error_message}"
        if context:
            formatted_message = f"{context} - {formatted_message}"
        
        # 记录详细错误信息到日志
        logger.error(f"{formatted_message}\n{error_trace}")
        
        # 如果有回调函数，调用它发送错误消息
        if callback:
            callback(formatted_message)
        
        return formatted_message
    
    @staticmethod
    def safe_execute(
        func: Callable, 
        error_context: str = "", 
        callback: Optional[Callable[[str], Any]] = None,
        default_return: Any = None,
        *args, **kwargs
    ) -> Any:
        """
        安全执行函数，捕获和处理任何异常
        
        参数:
            func: 要执行的函数
            error_context: 错误发生的上下文
            callback: 错误回调函数
            default_return: 发生错误时的默认返回值
            args, kwargs: 传递给func的参数
            
        返回:
            函数执行结果或默认返回值(如果发生错误)
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_error(e, error_context, callback)
            return default_return 