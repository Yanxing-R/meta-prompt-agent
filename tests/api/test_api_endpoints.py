# tests/api/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock

# 导入API应用实例
from meta_prompt_agent.api.main import app

# 创建测试客户端
client = TestClient(app)

@pytest.fixture
def mock_generate_function():
    """模拟generate_and_refine_prompt函数"""
    with patch("meta_prompt_agent.api.main.generate_and_refine_prompt") as mock_func:
        # 设置模拟的返回值
        mock_func.return_value = {
            "initial_core_prompt": "测试初始核心提示",
            "p1_initial_optimized_prompt": "这是一个优化后的测试提示",
            "evaluation_reports": [],
            "refined_prompts": [],
            "final_prompt": "这是一个优化后的测试提示",
            "error_message": None,
            "error_details": None,
        }
        yield mock_func

@pytest.fixture
def mock_explain_function():
    """模拟explain_term_in_prompt函数"""
    with patch("meta_prompt_agent.api.main.explain_term_in_prompt") as mock_func:
        # 设置模拟的返回值
        mock_func.return_value = ("这是术语的解释", None)
        yield mock_func

@pytest.fixture
def mock_feedback_functions():
    """模拟反馈相关函数"""
    with patch("meta_prompt_agent.api.main.load_feedback") as mock_load, \
         patch("meta_prompt_agent.api.main.save_feedback") as mock_save:
        
        mock_load.return_value = [
            {
                "prompt_id": "test-123",
                "original_request": "测试请求",
                "generated_prompt": "测试提示",
                "rating": 5,
                "comment": "很好",
                "timestamp": "2023-05-01T12:00:00"
            }
        ]
        mock_save.return_value = True
        
        yield (mock_load, mock_save)

@pytest.fixture
def mock_llm_factory():
    """模拟LLM工厂"""
    with patch("meta_prompt_agent.core.llm.factory.LLMClientFactory.create") as mock_factory:
        mock_client = MagicMock()
        mock_client.model_name = "test-model"
        mock_factory.return_value = mock_client
        yield mock_factory

def test_read_root():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "欢迎使用 Meta-Prompt Agent API!"}

def test_system_info(mock_llm_factory):
    """测试系统信息端点"""
    with patch("meta_prompt_agent.api.main.get_api_settings") as mock_settings, \
         patch("meta_prompt_agent.prompts.templates.STRUCTURED_PROMPT_TEMPLATES", {"TestTemplate": {}}):
        
        mock_settings.return_value = {"ACTIVE_LLM_PROVIDER": "test-provider"}
        
        response = client.get("/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "active_llm_provider" in data
        assert "model_name" in data
        assert "available_providers" in data
        assert "structured_templates" in data

def test_generate_simple_p1(mock_generate_function):
    """测试生成简单P1提示端点"""
    test_request = {
        "raw_request": "我想了解中短期天气预报",
        "task_type": "深度研究"
    }
    
    response = client.post("/generate-simple-p1", json=test_request)
    assert response.status_code == 200
    data = response.json()
    assert "p1_prompt" in data
    assert data["p1_prompt"] == "这是一个优化后的测试提示"
    assert "original_request" in data
    
    # 验证模拟函数被正确调用
    mock_generate_function.assert_called_once()
    args, kwargs = mock_generate_function.call_args
    assert kwargs["user_raw_request"] == "我想了解中短期天气预报"
    assert kwargs["task_type"] == "深度研究"
    assert kwargs["enable_self_correction"] is False
    assert kwargs["max_recursion_depth"] == 0

def test_generate_advanced_prompt(mock_generate_function):
    """测试生成高级提示端点"""
    test_request = {
        "raw_request": "我想了解中短期天气预报",
        "task_type": "深度研究",
        "enable_self_correction": True,
        "max_recursion_depth": 2,
        "template_name": None,
        "template_variables": None
    }
    
    response = client.post("/generate-advanced-prompt", json=test_request)
    assert response.status_code == 200
    data = response.json()
    assert "final_prompt" in data
    assert "initial_prompt" in data
    assert "refined_prompts" in data
    
    # 验证模拟函数被正确调用
    mock_generate_function.assert_called_once()
    args, kwargs = mock_generate_function.call_args
    assert kwargs["user_raw_request"] == "我想了解中短期天气预报"
    assert kwargs["task_type"] == "深度研究"
    assert kwargs["enable_self_correction"] is True
    assert kwargs["max_recursion_depth"] == 2

def test_explain_term(mock_explain_function):
    """测试解释术语端点"""
    test_request = {
        "term_to_explain": "S2S",
        "context_prompt": "我想了解中短期天气、S2S及年际预报的模式初始化理论"
    }
    
    response = client.post("/explain-term", json=test_request)
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert data["explanation"] == "这是术语的解释"
    assert "term" in data
    
    # 验证模拟函数被正确调用
    mock_explain_function.assert_called_once()
    args, kwargs = mock_explain_function.call_args
    assert kwargs["term_to_explain"] == "S2S"
    assert kwargs["context_prompt"] == "我想了解中短期天气、S2S及年际预报的模式初始化理论"

def test_submit_feedback(mock_feedback_functions):
    """测试提交反馈端点"""
    mock_load, mock_save = mock_feedback_functions
    
    test_feedback = {
        "prompt_id": "test-456",
        "original_request": "测试原始请求",
        "generated_prompt": "测试生成提示",
        "rating": 4,
        "comment": "还不错"
    }
    
    response = client.post("/feedback/submit", json=test_feedback)
    assert response.status_code == 201
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "feedback_id" in data
    
    # 验证模拟函数被正确调用
    mock_load.assert_called_once()
    mock_save.assert_called_once()

def test_list_feedback(mock_feedback_functions):
    """测试获取反馈列表端点"""
    mock_load, _ = mock_feedback_functions
    
    response = client.get("/feedback/list?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "feedback_items" in data
    assert "total_count" in data
    assert len(data["feedback_items"]) == 1
    assert data["total_count"] == 1
    
    # 验证模拟函数被正确调用
    mock_load.assert_called_once()
    
def test_error_handling():
    """测试错误处理"""
    # 测试无效的请求体
    invalid_request = {
        "raw_request": ""  # 空字符串，应该验证失败
    }
    
    response = client.post("/generate-simple-p1", json=invalid_request)
    assert response.status_code == 422  # 验证错误

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 