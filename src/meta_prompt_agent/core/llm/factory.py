from typing import Dict, Type
from .base import LLMClient
from .clients.ollama import OllamaClient
from .clients.gemini import GeminiClient
from .clients.qwen import QwenClient

class LLMClientFactory:
    """LLM客户端工厂类"""
    
    # 注册可用的LLM客户端实现
    _clients: Dict[str, Type[LLMClient]] = {
        "ollama": OllamaClient,
        "gemini": GeminiClient,
        "qwen": QwenClient
    }
    
    @classmethod
    def create(cls, provider: str = None, **kwargs) -> LLMClient:
        """创建LLM客户端实例"""
        # 如果没有指定提供商，使用配置中的活跃提供商
        from ...config.settings import get_settings
        settings = get_settings()
        
        active_provider = provider or settings["ACTIVE_LLM_PROVIDER"]
        
        # 检查提供商是否支持
        if active_provider not in cls._clients:
            raise ValueError(f"不支持的LLM提供商: {active_provider}")
            
        # 实例化客户端
        client_class = cls._clients[active_provider]
        return client_class(**kwargs) 