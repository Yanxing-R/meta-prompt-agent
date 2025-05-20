# tests/unit/test_llm_clients.py
import pytest
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock, patch

from meta_prompt_agent.core.llm import LLMClientFactory, LLMClient
from meta_prompt_agent.core.llm.clients import OllamaClient, GeminiClient, QwenClient

# ---- 测试LLM工厂 ----
@pytest.mark.asyncio
@patch('meta_prompt_agent.config.settings.get_settings')
async def test_llm_factory_create(mock_get_settings):
    """测试LLM工厂创建不同类型的客户端"""
    # 配置模拟
    mock_settings = {
        "ACTIVE_LLM_PROVIDER": "ollama"  # 默认设为ollama
    }
    mock_get_settings.return_value = mock_settings
    
    # 测试创建Ollama客户端
    client = LLMClientFactory.create()
    assert isinstance(client, OllamaClient)
    
    # 测试创建Gemini客户端
    mock_settings["ACTIVE_LLM_PROVIDER"] = "gemini"
    client = LLMClientFactory.create()
    assert isinstance(client, GeminiClient)
    
    # 测试创建Qwen客户端
    mock_settings["ACTIVE_LLM_PROVIDER"] = "qwen"
    client = LLMClientFactory.create()
    assert isinstance(client, QwenClient)
    
    # 测试使用显式指定的提供商
    mock_settings["ACTIVE_LLM_PROVIDER"] = "ollama"  # 设置默认为ollama
    client = LLMClientFactory.create("gemini")  # 但创建gemini
    assert isinstance(client, GeminiClient)
    
    # 测试未知的提供商
    mock_settings["ACTIVE_LLM_PROVIDER"] = "unknown"
    with pytest.raises(ValueError, match="不支持的LLM提供商"):
        LLMClientFactory.create()

# ---- 测试Ollama客户端 ----
@pytest.mark.asyncio
@patch('meta_prompt_agent.core.llm.clients.ollama.get_settings')
@patch('meta_prompt_agent.core.llm.clients.ollama.httpx.AsyncClient')
async def test_ollama_client_generate(mock_async_client, mock_get_settings):
    """测试Ollama客户端的generate方法"""
    # 配置模拟
    mock_settings = {
        "OLLAMA_MODEL": "test-model",
        "OLLAMA_API_URL": "http://test-url"
    }
    mock_get_settings.return_value = mock_settings
    
    # 模拟httpx客户端
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    
    # 模拟响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "test-model",
        "response": "这是测试响应",
        "total_duration": 100,
        "eval_count": 10,
        "eval_duration": 50
    }
    mock_client_instance.post.return_value = mock_response
    
    # 创建客户端并调用
    client = OllamaClient()
    response = await client.generate("测试提示")
    
    # 验证结果
    assert response == "这是测试响应"
    
    # 验证模拟调用
    mock_client_instance.post.assert_called_once()
    call_args = mock_client_instance.post.call_args[1]
    assert call_args["json"]["model"] == "test-model"
    assert call_args["json"]["prompt"] == "测试提示"
    assert call_args["json"]["stream"] == False

# ---- 测试Gemini客户端 ----
@pytest.mark.asyncio
@patch('meta_prompt_agent.core.llm.clients.gemini.get_settings')
@patch('meta_prompt_agent.core.llm.clients.gemini.genai')
async def test_gemini_client_generate_with_metadata(mock_genai, mock_get_settings):
    """测试Gemini客户端的generate_with_metadata方法"""
    # 配置模拟
    mock_settings = {
        "GEMINI_API_KEY": "test-api-key",
        "GEMINI_MODEL_NAME": "gemini-test-model"
    }
    mock_get_settings.return_value = mock_settings
    
    # 模拟Gemini模型
    mock_model = AsyncMock()  # 使用AsyncMock而不是MagicMock
    mock_genai.GenerativeModel.return_value = mock_model
    
    # 模拟generate_content_async的结果
    mock_response = MagicMock()
    mock_response.text = "这是Gemini的测试响应"
    mock_model.generate_content_async.return_value = mock_response
    
    # 创建客户端并调用
    client = GeminiClient()
    response, metadata = await client.generate_with_metadata("测试提示", temperature=0.5)
    
    # 验证结果
    assert response == "这是Gemini的测试响应"
    assert "model" in metadata
    assert metadata["model"] == "gemini-test-model"
    
    # 验证模拟调用
    mock_genai.configure.assert_called_once_with(api_key="test-api-key")
    mock_genai.GenerativeModel.assert_called_once()
    mock_model.generate_content_async.assert_called_once_with("测试提示")

# ---- 测试Qwen客户端 ----
@pytest.mark.asyncio
@patch('meta_prompt_agent.core.llm.clients.qwen.get_settings')
@patch('meta_prompt_agent.core.llm.clients.qwen.httpx.AsyncClient')
async def test_qwen_client_generate(mock_async_client, mock_get_settings):
    """测试通义千问客户端的generate方法"""
    # 配置模拟
    mock_settings = {
        "DASHSCOPE_API_KEY": "test-api-key",
        "QWEN_API_KEY": None,
        "QWEN_MODEL_NAME": "qwen-test-model"
    }
    mock_get_settings.return_value = mock_settings
    
    # 模拟httpx客户端
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    
    # 模拟响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": {
            "text": "这是通义千问的测试响应",
            "finish_reason": "normal"
        },
        "request_id": "test-request-id",
        "usage": {"total_tokens": 50}
    }
    mock_client_instance.post.return_value = mock_response
    
    # 创建客户端并调用
    client = QwenClient()
    response = await client.generate("测试提示")
    
    # 验证结果
    assert response == "这是通义千问的测试响应"
    
    # 验证模拟调用
    mock_client_instance.post.assert_called_once()
    call_args = mock_client_instance.post.call_args[1]
    assert call_args["json"]["model"] == "qwen-test-model"
    assert call_args["json"]["input"]["prompt"] == "测试提示"
    assert call_args["headers"]["Authorization"] == "Bearer test-api-key"

# ---- 集成测试：agent.py中的invoke_llm函数 ----
@pytest.mark.asyncio
@patch('meta_prompt_agent.core.agent.LLMClientFactory')
async def test_invoke_llm_integration(mock_factory):
    """测试agent.py中的invoke_llm函数与LLM抽象层的集成"""
    from meta_prompt_agent.core.agent import invoke_llm
    
    # 模拟工厂和客户端
    mock_client = AsyncMock()
    mock_factory.create.return_value = mock_client
    mock_client.model_name = "test-model"
    
    # 模拟client.generate_with_metadata的返回值
    mock_client.generate_with_metadata.return_value = ("这是测试响应", {"test_metadata": "value"})
    
    # 调用invoke_llm
    response, error = await invoke_llm("测试提示", [{"role": "user", "content": "历史消息"}])
    
    # 验证结果
    assert response == "这是测试响应"
    assert error is None
    
    # 验证mock调用
    mock_factory.create.assert_called_once()
    mock_client.generate_with_metadata.assert_called_once_with(
        "测试提示", 
        messages_history=[{"role": "user", "content": "历史消息"}]
    ) 