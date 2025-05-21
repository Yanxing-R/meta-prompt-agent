from typing import Dict, Type
import logging
from .base import LLMClient
from .clients.ollama import OllamaClient
from .clients.gemini import GeminiClient
from .clients.qwen import QwenClient

# 获取日志记录器
logger = logging.getLogger(__name__)

class LLMClientFactory:
    """LLM客户端工厂类"""
    
    # 注册可用的LLM客户端实现
    _clients: Dict[str, Type[LLMClient]] = {
        "ollama": OllamaClient,
        "gemini": GeminiClient,
        "qwen": QwenClient
    }
    
    @classmethod
    def create(cls, provider: str = None, model_override: str = None, **kwargs) -> LLMClient:
        """
        创建LLM客户端实例
        
        Args:
            provider: 提供商名称，如果为None则使用配置中的活跃提供商
            model_override: 要使用的模型名称，将传递给客户端构造函数
            **kwargs: 其他传递给客户端构造函数的参数
        """
        # 如果没有指定提供商，使用配置中的活跃提供商
        from ...config.settings import get_settings
        settings = get_settings()
        
        active_provider = provider or settings["ACTIVE_LLM_PROVIDER"]
        
        # 添加日志记录
        logger.info(f"创建LLM客户端: 提供商={active_provider}, 模型覆盖={model_override or '无'}")
        
        # 检查提供商是否支持
        if active_provider not in cls._clients:
            logger.error(f"不支持的LLM提供商: {active_provider}, 可用提供商: {list(cls._clients.keys())}")
            raise ValueError(f"不支持的LLM提供商: {active_provider}")
            
        # 如果提供了model_override，添加到kwargs中
        if model_override:
            kwargs["model_name"] = model_override
            logger.info(f"使用指定模型: {model_override}")
            
        # 实例化客户端
        client_class = cls._clients[active_provider]
        logger.debug(f"使用客户端类: {client_class.__name__}")
        
        try:
            client = client_class(**kwargs)
            logger.info(f"成功创建客户端: {client_class.__name__}, 模型={client.model_name}")
            return client
        except Exception as e:
            logger.exception(f"创建客户端失败: {e}")
            raise 