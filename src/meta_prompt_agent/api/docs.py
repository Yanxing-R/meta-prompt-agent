# src/meta_prompt_agent/api/docs.py
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any, Callable, Optional

def custom_openapi_schema(app) -> Callable[[], Dict[str, Any]]:
    """
    创建自定义OpenAPI文档生成函数
    
    Args:
        app: FastAPI应用实例
        
    Returns:
        用于生成OpenAPI模式的函数
    """
    
    def custom_openapi() -> Dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # 自定义OpenAPI文档样式
        openapi_schema["info"]["x-logo"] = {
            "url": "https://example.com/logo.png",  # 替换为实际的logo URL
            "altText": "Think Twice Logo" 
        }
        
        # 添加API使用示例
        openapi_schema["info"]["description"] = f"""
        {app.description}
        
        ## API使用示例
        
        ### 生成优化的提示词
        
        ```python
        import requests
        import json
        
        url = "http://localhost:8000/generate-simple-p1"
        payload = {
            "raw_request": "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战",
            "task_type": "深度研究"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        ```
        
        ### 解释提示词中的术语
        
        ```python
        import requests
        import json
        
        url = "http://localhost:8000/explain-term"
        payload = {
            "term_to_explain": "S2S",
            "context_prompt": "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        ```
        
        ## 认证方法
        
        目前API不需要认证。后续版本可能会添加API密钥认证机制。
        """
        
        # 更新标签描述
        openapi_schema["tags"] = [
            {
                "name": "General",
                "description": "通用API端点"
            },
            {
                "name": "System",
                "description": "系统信息相关端点"
            },
            {
                "name": "Prompt Generation",
                "description": "提示词生成相关端点"
            },
            {
                "name": "AI Utilities",
                "description": "AI辅助工具端点"
            },
            {
                "name": "Feedback",
                "description": "用户反馈相关端点"
            }
        ]
        
        # 修改响应模式
        for path in openapi_schema["paths"].values():
            for method in path.values():
                if "responses" in method:
                    for status_code, response in method["responses"].items():
                        if status_code == "422":
                            response["description"] = "请求验证失败，请检查输入参数"
                        elif status_code == "500":
                            response["description"] = "服务器内部错误，请稍后重试或联系管理员"
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    return custom_openapi 