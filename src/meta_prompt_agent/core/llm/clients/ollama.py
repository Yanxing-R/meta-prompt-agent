import httpx
from typing import Dict, Any, Tuple, Optional
from ..base import LLMClient
from ....config.settings import get_settings

class OllamaClient(LLMClient):
    """Ollama API客户端实现"""
    
    def __init__(self, model_name: str = None):
        self.settings = get_settings()
        self.model_name = model_name or self.settings["OLLAMA_MODEL"]
        self.api_url = self.settings["OLLAMA_API_URL"]
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用Ollama API生成响应"""
        response, _ = await self.generate_with_metadata(prompt, **kwargs)
        return response
        
    async def generate_with_metadata(self, prompt: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """调用Ollama API生成响应及元数据"""
        temperature = kwargs.get("temperature", 0.7)
        
        # 构建请求数据
        request_data = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        # 添加其他可选参数
        for key, value in kwargs.items():
            if key not in ["temperature"]:
                request_data[key] = value
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/generate",
                json=request_data,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API错误: {response.text}")
                
            result = response.json()
            response_text = result.get("response", "")
            
            # 提取元数据
            metadata = {
                "model": result.get("model", ""),
                "total_duration": result.get("total_duration", 0),
                "eval_count": result.get("eval_count", 0),
                "eval_duration": result.get("eval_duration", 0)
            }
            
            return response_text, metadata 