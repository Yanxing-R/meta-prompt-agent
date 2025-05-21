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
            "gemini-2.0-flash": "gemini-2.0-flash",
            "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20"
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
            # 如果模型在映射中，使用映射后的名称
            model_name = self.model_mapping.get(model_override, model_override)
            print(f"使用模型覆盖: {model_override} -> {model_name}")
            # 更新客户端的模型名称
            self.model_name = model_name
        
        # 添加调试日志
        print(f"Gemini调用参数: 模型={model_name}, 温度={temperature}, 最大令牌数={max_tokens}")
        
        try:
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
            
            return response_text, {"model": model_name}
        except Exception as e:
            print(f"Gemini API调用失败: {str(e)}")
            raise 