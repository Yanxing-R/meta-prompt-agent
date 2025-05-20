# src/meta_prompt_agent/api/client.py
import requests
import json
from typing import Dict, Any, List, Optional, Union, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ThinkTwiceAPIClient:
    """
    Think Twice API客户端
    
    提供对Meta-Prompt Agent API的便捷访问。
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化API客户端
        
        Args:
            base_url: API服务的基础URL，默认为http://localhost:8000
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理API响应"""
        try:
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            else:
                error_data = response.json()
                logger.error(f"API请求失败: {error_data.get('detail', f'HTTP错误 {response.status_code}')}")
                return {
                    "error": True, 
                    "status_code": response.status_code,
                    "detail": error_data.get("detail", f"HTTP错误 {response.status_code}")
                }
        except Exception as e:
            logger.exception(f"处理API响应时发生错误: {e}")
            return {
                "error": True,
                "status_code": response.status_code,
                "detail": f"处理响应失败: {str(e)}"
            }
            
    def check_health(self) -> Dict[str, Any]:
        """检查API服务健康状态"""
        try:
            response = requests.get(f"{self.base_url}/")
            return self._handle_response(response)
        except Exception as e:
            logger.exception(f"健康检查请求失败: {e}")
            return {"error": True, "detail": f"请求失败: {str(e)}"}
            
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            response = requests.get(f"{self.base_url}/system/info")
            return self._handle_response(response)
        except Exception as e:
            logger.exception(f"获取系统信息失败: {e}")
            return {"error": True, "detail": f"请求失败: {str(e)}"}
            
    def generate_simple_prompt(self, raw_request: str, task_type: str = "通用/问答") -> Dict[str, Any]:
        """
        生成简单的优化提示 (P1)
        
        Args:
            raw_request: 用户的原始请求文本
            task_type: 任务类型，默认为"通用/问答"
            
        Returns:
            包含生成的提示和其他信息的字典
        """
        try:
            payload = {
                "raw_request": raw_request,
                "task_type": task_type
            }
            
            response = requests.post(
                f"{self.base_url}/generate-simple-p1",
                headers=self.headers,
                json=payload
            )
            
            return self._handle_response(response)
        except Exception as e:
            logger.exception(f"生成简单提示请求失败: {e}")
            return {"error": True, "detail": f"请求失败: {str(e)}"}
            
    def generate_advanced_prompt(
        self, raw_request: str, task_type: str = "通用/问答",
        enable_self_correction: bool = True, max_recursion_depth: int = 2,
        template_name: Optional[str] = None, template_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成高级优化提示，支持自我校正和模板
        
        Args:
            raw_request: 用户的原始请求文本
            task_type: 任务类型，默认为"通用/问答"
            enable_self_correction: 是否启用自我校正
            max_recursion_depth: 最大递归深度
            template_name: 结构化模板名称
            template_variables: 模板变量
            
        Returns:
            包含生成的提示和其他信息的字典
        """
        try:
            payload = {
                "raw_request": raw_request,
                "task_type": task_type,
                "enable_self_correction": enable_self_correction,
                "max_recursion_depth": max_recursion_depth
            }
            
            if template_name:
                payload["template_name"] = template_name
                
            if template_variables:
                payload["template_variables"] = template_variables
                
            response = requests.post(
                f"{self.base_url}/generate-advanced-prompt",
                headers=self.headers,
                json=payload
            )
            
            return self._handle_response(response)
        except Exception as e:
            logger.exception(f"生成高级提示请求失败: {e}")
            return {"error": True, "detail": f"请求失败: {str(e)}"}
            
    def explain_term(self, term: str, context: str) -> Dict[str, Any]:
        """
        解释提示词中的特定术语
        
        Args:
            term: 要解释的术语
            context: 术语所在的上下文提示
            
        Returns:
            包含术语解释的字典
        """
        try:
            payload = {
                "term_to_explain": term,
                "context_prompt": context
            }
            
            response = requests.post(
                f"{self.base_url}/explain-term",
                headers=self.headers,
                json=payload
            )
            
            return self._handle_response(response)
        except Exception as e:
            logger.exception(f"解释术语请求失败: {e}")
            return {"error": True, "detail": f"请求失败: {str(e)}"}
            
    def submit_feedback(
        self, prompt_id: str, original_request: str, generated_prompt: str,
        rating: int, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交用户反馈
        
        Args:
            prompt_id: 提示的唯一标识符
            original_request: 原始用户请求
            generated_prompt: 生成的优化提示
            rating: 用户评分(1-5)
            comment: 用户反馈评论
            
        Returns:
            包含反馈提交状态的字典
        """
        try:
            payload = {
                "prompt_id": prompt_id,
                "original_request": original_request,
                "generated_prompt": generated_prompt,
                "rating": rating,
                "timestamp": datetime.now().isoformat()
            }
            
            if comment:
                payload["comment"] = comment
                
            response = requests.post(
                f"{self.base_url}/feedback/submit",
                headers=self.headers,
                json=payload
            )
            
            return self._handle_response(response)
        except Exception as e:
            logger.exception(f"提交反馈请求失败: {e}")
            return {"error": True, "detail": f"请求失败: {str(e)}"}
            
    def get_feedback_list(
        self, limit: int = 20, offset: int = 0, min_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取反馈列表
        
        Args:
            limit: 要返回的反馈项数量
            offset: 分页起始位置
            min_rating: 最低评分过滤
            
        Returns:
            包含反馈列表的字典
        """
        try:
            params = {"limit": limit, "offset": offset}
            
            if min_rating is not None:
                params["min_rating"] = min_rating
                
            response = requests.get(
                f"{self.base_url}/feedback/list",
                headers=self.headers,
                params=params
            )
            
            return self._handle_response(response)
        except Exception as e:
            logger.exception(f"获取反馈列表请求失败: {e}")
            return {"error": True, "detail": f"请求失败: {str(e)}"}


# 使用示例
if __name__ == "__main__":
    # 配置基本日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建客户端实例
    client = ThinkTwiceAPIClient()
    
    # 检查API健康状态
    health = client.check_health()
    print(f"API健康检查结果: {json.dumps(health, ensure_ascii=False, indent=2)}")
    
    # 获取系统信息
    system_info = client.get_system_info()
    print(f"系统信息: {json.dumps(system_info, ensure_ascii=False, indent=2)}")
    
    # 生成简单提示示例
    sample_request = "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战"
    result = client.generate_simple_prompt(sample_request, task_type="深度研究")
    
    if not result.get("error"):
        print(f"生成的提示: {result.get('p1_prompt')}")
    else:
        print(f"生成提示失败: {result.get('detail')}") 