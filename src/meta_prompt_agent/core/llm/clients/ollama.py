import httpx
import os
from typing import Dict, Any, Tuple, Optional
from ..base import LLMClient
from ....config.settings import get_settings

class OllamaClient(LLMClient):
    """Ollama API客户端实现"""
    
    def __init__(self, model_name: str = None):
        """
        初始化Ollama客户端
        
        Args:
            model_name: 指定使用的模型名称，如果为None则使用配置中的默认值
        """
        self.settings = get_settings()
        self.model_name = model_name or self.settings["OLLAMA_MODEL"]
        self.api_base_url = self.settings["OLLAMA_API_URL"].rstrip("/")
        print(f"初始化Ollama客户端，模型: {self.model_name}, API URL: {self.api_base_url}")
        
    async def check_service_status(self) -> tuple[bool, str]:
        """
        检查Ollama服务状态
        
        Returns:
            tuple[bool, str]: (是否可用, 状态消息)
        """
        try:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{self.api_base_url}/api/version", timeout=5.0)
                    if response.status_code == 200:
                        version_info = response.json()
                        return True, f"Ollama服务正常，版本: {version_info.get('version', '未知')}"
                    else:
                        return False, f"Ollama服务响应异常，状态码: {response.status_code}"
                except httpx.HTTPError as e:
                    return False, f"连接到Ollama服务失败: {str(e)}"
        except Exception as e:
            return False, f"检查Ollama服务时出错: {str(e)}"
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用Ollama API生成响应"""
        response, _ = await self.generate_with_metadata(prompt, **kwargs)
        return response
        
    async def generate_with_metadata(self, prompt: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """调用Ollama API生成响应及元数据"""
        temperature = kwargs.get("temperature", 0.7)
        
        # 处理模型覆盖，如果指定了model_override，使用指定的模型
        model_override = kwargs.get("model_override")
        model_name = model_override if model_override else self.model_name
        
        # 更新客户端的模型名称，确保系统信息显示正确
        if model_override:
            self.model_name = model_override
        
        # 构建请求数据
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        # 添加其他可选参数
        for key, value in kwargs.items():
            if key not in ["temperature", "model_override"]:
                request_data[key] = value
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            # 确保使用正确的API端点
            api_endpoint = f"{self.api_base_url}/api/generate"
            
            print(f"调用Ollama API: {api_endpoint}, 模型: {model_name}")
            
            try:
                # 增加超时时间到120秒
                response = await client.post(
                    api_endpoint,
                    json=request_data,
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    error_msg = f"Ollama API错误 ({response.status_code}): {response.text}"
                    print(error_msg)
                    # 添加更详细的错误信息
                    if response.status_code == 502:
                        error_msg += " - 可能是网关超时或服务器内部错误，请检查Ollama服务是否正常运行，或模型是否加载完成"
                    elif response.status_code == 404:
                        error_msg += f" - 模型 '{model_name}' 可能不存在或未加载"
                    raise Exception(error_msg)
                    
                result = response.json()
                response_text = result.get("response", "")
                
                # 提取元数据
                metadata = {
                    "model": model_name,
                    "provider": "ollama",
                    "total_duration": result.get("total_duration", 0),
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0)
                }
                
                return response_text, metadata
            except httpx.HTTPError as e:
                error_msg = f"Ollama API连接错误: {str(e)} (URL: {api_endpoint})"
                if isinstance(e, httpx.TimeoutException):
                    error_msg = f"Ollama API请求超时: {str(e)} (URL: {api_endpoint}, 模型: {model_name}) - 请检查模型大小和资源使用情况"
                print(error_msg)
                raise Exception(error_msg) 