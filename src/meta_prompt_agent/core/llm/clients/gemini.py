import google.generativeai as genai
from typing import Dict, Any, Tuple, Optional
from ..base import LLMClient
from ....config.settings import get_settings

class GeminiClient(LLMClient):
    """Google Gemini API客户端实现"""
    
    def __init__(self, model_name: str = None):
        self.settings = get_settings()
        self.api_key = self.settings["GEMINI_API_KEY"]
        if not self.api_key:
            raise ValueError("未设置Gemini API密钥")
            
        self.model_name = model_name or self.settings["GEMINI_MODEL_NAME"]
        
        # 模型映射，将前端友好名称映射到实际API模型名称
        self.model_mapping = {
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
            "gemini-1.0-pro": "gemini-1.0-pro"
        }
        
        # 配置Gemini
        genai.configure(api_key=self.api_key)
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用Gemini API生成响应"""
        response, _ = await self.generate_with_metadata(prompt, **kwargs)
        return response
        
    async def generate_with_metadata(self, prompt: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """调用Gemini API生成响应及元数据"""
        # 提取参数
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1024)
        
        # 处理模型覆盖
        model_override = kwargs.get("model_override")
        model_name = self.model_name
        
        if model_override:
            # 直接使用model_override作为模型名称
            model_name = model_override
            # 更新客户端的模型名称，确保系统信息显示正确
            self.model_name = model_override
        
        # 获取模型
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": kwargs.get("top_p", 0.95),
                "top_k": kwargs.get("top_k", 0)
            }
        )
        
        # 生成响应
        response = await model.generate_content_async(prompt)
        
        # 提取响应文本
        response_text = response.text
        
        # 提取元数据
        metadata = {
            "model": model_name,
            "prompt_feedback": getattr(response, "prompt_feedback", {}),
            "candidates": [
                getattr(candidate, "finish_reason", None)
                for candidate in getattr(response, "candidates", [])
            ]
        }
        
        return response_text, metadata 