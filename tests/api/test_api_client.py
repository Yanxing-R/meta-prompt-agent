# tests/api/test_api_client.py
import pytest
from unittest.mock import patch, MagicMock
import requests
import json
from datetime import datetime

from meta_prompt_agent.api.client import ThinkTwiceAPIClient

@pytest.fixture
def client():
    """创建测试客户端"""
    return ThinkTwiceAPIClient(base_url="http://test-server")

@pytest.fixture
def mock_response():
    """创建模拟响应"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": "测试成功"}
    return mock_resp

@pytest.fixture
def error_response():
    """创建错误响应"""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.json.return_value = {"detail": "服务器错误"}
    return mock_resp

def test_check_health(client, mock_response):
    """测试健康检查"""
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = client.check_health()
        mock_get.assert_called_once_with("http://test-server/")
        assert result == {"message": "测试成功"}

def test_get_system_info(client, mock_response):
    """测试获取系统信息"""
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = client.get_system_info()
        mock_get.assert_called_once_with("http://test-server/system/info")
        assert result == {"message": "测试成功"}

def test_generate_simple_prompt(client, mock_response):
    """测试生成简单提示"""
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = client.generate_simple_prompt("测试请求", "测试类型")
        mock_post.assert_called_once()
        assert result == {"message": "测试成功"}

def test_explain_term(client, mock_response):
    """测试解释术语"""
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = client.explain_term("测试术语", "测试上下文")
        mock_post.assert_called_once()
        assert result == {"message": "测试成功"}

def test_error_handling(client, error_response):
    """测试错误处理"""
    with patch("requests.get", return_value=error_response) as mock_get:
        result = client.check_health()
        assert "error" in result
        assert result["status_code"] == 500
        assert result["detail"] == "服务器错误"

def test_handle_exception(client):
    """测试异常处理"""
    with patch("requests.get", side_effect=Exception("测试异常")) as mock_get:
        result = client.check_health()
        assert "error" in result
        assert result["detail"] == "请求失败: 测试异常" 