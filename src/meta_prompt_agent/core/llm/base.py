from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional

class LLMClient(ABC):
    """大型语言模型客户端抽象基类"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本响应"""
        pass
        
    @abstractmethod
    async def generate_with_metadata(self, prompt: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """生成文本响应及元数据"""
        pass 