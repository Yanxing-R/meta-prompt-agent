import httpx
import json
from typing import Dict, Any, Tuple, Optional
from ..base import LLMClient
from ....config.settings import get_settings

class QwenClient(LLMClient):
    """通义千问API客户端实现"""
    
    def __init__(self, model_name: str = None):
        self.settings = get_settings()
        # 优先使用DASHSCOPE_API_KEY，如果没有则使用QWEN_API_KEY
        self.api_key = self.settings["DASHSCOPE_API_KEY"] or self.settings["QWEN_API_KEY"]
        if not self.api_key:
            raise ValueError("未设置通义千问API密钥")
            
        self.model_name = model_name or self.settings["QWEN_MODEL_NAME"]
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用通义千问API生成响应"""
        response, _ = await self.generate_with_metadata(prompt, **kwargs)
        return response
        
    async def generate_with_metadata(self, prompt: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """调用通义千问API生成响应及元数据"""
        # 提取参数
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1024)
        
        # 处理模型覆盖
        model_override = kwargs.get("model_override")
        model_name = model_override if model_override else self.model_name
        
        # 更新客户端的模型名称，确保系统信息显示正确
        if model_override:
            self.model_name = model_override
            
        # 构建请求数据
        request_data = {
            "model": model_name,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": kwargs.get("top_p", 0.8),
                "result_format": "text",
                "enable_thinking": False  # 对非流式调用必须设置为false
            }
        }
        
        # 发送请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json=request_data,
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"通义千问API错误: {response.text}")
                
            result = response.json()
            
            # 从响应中提取文本
            output = result.get("output", {})
            response_text = output.get("text", "")
            
            # 提取元数据
            metadata = {
                "model": self.model_name,
                "request_id": result.get("request_id", ""),
                "usage": result.get("usage", {}),
                "finish_reason": output.get("finish_reason", "")
            }
            
            return response_text, metadata 