# tests/api/test_main_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch 

# 导入你的FastAPI应用实例和Pydantic模型
from meta_prompt_agent.api.main import app as fastapi_app
from meta_prompt_agent.api.main import ExplainTermRequest, ExplanationResponse, UserRequest, P1Response, ErrorResponse # 确保所有模型都被导入
from meta_prompt_agent.config import settings # 如果测试中直接或间接用到
from meta_prompt_agent.prompts.templates import EXPLAIN_TERM_TEMPLATE # 如果mock中用到


client = TestClient(fastapi_app)

def test_explain_term_endpoint_success(monkeypatch):
    """
    测试 /explain-term 端点在成功解释术语时的行为。
    """
    # 1. 准备 (Arrange)
    term_to_explain_input = "角色扮演" 
    context_prompt_input = "请使用角色扮演的方式，扮演一个海盗船长，然后告诉我一个宝藏的故事。"
    expected_explanation_text = "角色扮演是指让AI模仿特定的身份或性格来进行回应，以增强对话的沉浸感和趣味性。"
    
    request_payload = ExplainTermRequest(
        term_to_explain=term_to_explain_input,
        context_prompt=context_prompt_input
    )

    mock_explain_calls = []
    def mock_successful_explain_term(term_to_explain: str, context_prompt: str):
        mock_explain_calls.append({"term_to_explain": term_to_explain, "context_prompt": context_prompt})
        assert term_to_explain == term_to_explain_input 
        assert context_prompt == context_prompt_input
        return expected_explanation_text, None 
    
    monkeypatch.setattr('meta_prompt_agent.api.main.explain_term_in_prompt', mock_successful_explain_term)

    # 2. 执行 (Act)
    response = client.post("/explain-term", json=request_payload.model_dump()) 

    # 3. 断言 (Assert)
    assert response.status_code == 200, \
        f"请求应成功返回200状态码，但返回了 {response.status_code}。响应内容: {response.text}"
    
    response_data = response.json() 
    
    assert response_data.get("explanation") == expected_explanation_text, "返回的解释文本与预期不符"
    assert response_data.get("term") == term_to_explain_input, "返回的术语与预期不符" 
    assert response_data.get("message") == "术语已成功解释。", "返回的成功消息不符合预期"
    
    assert len(mock_explain_calls) == 1, "explain_term_in_prompt 应只被调用1次"
    assert mock_explain_calls[0]["term_to_explain"] == term_to_explain_input
    assert mock_explain_calls[0]["context_prompt"] == context_prompt_input


def test_explain_term_endpoint_input_validation_empty_term():
    """
    测试当请求中 term_to_explain 为空字符串时，API是否返回422错误。
    (Pydantic的min_length=1应该捕获这个)
    """
    request_payload_dict = {
        "term_to_explain": "", 
        "context_prompt": "这是一个有效的上下文提示。"
    }
    response = client.post("/explain-term", json=request_payload_dict)
    assert response.status_code == 422, \
        f"请求term_to_explain为空时应返回422状态码，但返回了 {response.status_code}。响应: {response.text}"
    response_data = response.json()
    assert "detail" in response_data
    found_term_error = False
    if isinstance(response_data["detail"], list): 
        for error_item in response_data["detail"]:
            if isinstance(error_item, dict) and "loc" in error_item and "term_to_explain" in error_item["loc"]:
                found_term_error = True
                break
    elif isinstance(response_data["detail"], str): 
        if "term_to_explain" in response_data["detail"].lower():
             found_term_error = True
    assert found_term_error, f"422错误的详情中未明确指出 'term_to_explain' 的问题。详情: {response_data['detail']}"

# --- 修正后的测试用例 ---
def test_explain_term_endpoint_input_validation_empty_context(monkeypatch):
    """
    测试当请求中 context_prompt 为仅包含空白的字符串时，
    API是否由于自定义验证返回400错误。
    """
    # 1. 准备 (Arrange)
    request_payload_dict = {
        "term_to_explain": "一个有效的术语",
        "context_prompt": "   " # 仅包含空白
    }

    # 我们不需要mock explain_term_in_prompt，因为我们期望它被调用并执行其内部验证
    # 但是，为了确保测试的隔离性，并且如果 explain_term_in_prompt 内部
    # 在验证失败后还尝试做其他事情（比如调用 call_ollama_api），mocking 仍然有意义。
    # 在这种情况下，explain_term_in_prompt 应该在验证失败后直接返回。
    # 所以，我们不需要mock其内部的 call_ollama_api。

    # 2. 执行 (Act)
    response = client.post("/explain-term", json=request_payload_dict)

    # 3. 断言 (Assert)
    assert response.status_code == 400, \
        f"请求context_prompt为空白时应返回400状态码，但返回了 {response.status_code}。响应: {response.text}"
    
    response_data = response.json()
    assert "detail" in response_data, "错误响应中应包含 'detail' 字段"
    # 验证返回的detail是否是我们的自定义错误消息
    assert response_data["detail"] == "错误：需要提供术语所在的上下文提示。", \
        f"400错误的详情不符合预期。实际: {response_data['detail']}"

# 新增测试用例：测试 agent.explain_term_in_prompt 调用失败的情况
def test_explain_term_endpoint_agent_call_fails(monkeypatch):
    """
    测试当后端的 explain_term_in_prompt 函数返回错误时，
    /explain-term API端点是否正确处理并返回500错误。
    """
    # 1. 准备 (Arrange)
    term_to_explain_input = "一个会导致agent失败的术语"
    context_prompt_input = "一些上下文"
    
    request_payload = ExplainTermRequest(
        term_to_explain=term_to_explain_input,
        context_prompt=context_prompt_input
    )

    simulated_agent_error_message = "错误：模拟的Ollama API在解释时连接失败"
    simulated_agent_error_details = {"type": "ConnectionError", "details": "模拟连接失败"}

    # 模拟 core.agent.explain_term_in_prompt 函数，使其返回一个错误
    def mock_failing_explain_term(term_to_explain: str, context_prompt: str):
        assert term_to_explain == term_to_explain_input
        assert context_prompt == context_prompt_input
        return simulated_agent_error_message, simulated_agent_error_details
    
    monkeypatch.setattr('meta_prompt_agent.api.main.explain_term_in_prompt', mock_failing_explain_term)

    # 2. 执行 (Act)
    response = client.post("/explain-term", json=request_payload.model_dump())

    # 3. 断言 (Assert)
    assert response.status_code == 500, \
        f"当agent调用失败时应返回500状态码，但返回了 {response.status_code}。响应内容: {response.text}"
    
    response_data = response.json()
    assert "detail" in response_data, "错误响应中应包含 'detail' 字段"
    # API 端点会将 agent 返回的错误消息作为 detail 返回
    assert response_data["detail"] == simulated_agent_error_message, \
        f"500错误的详情与agent返回的错误消息不符。预期: '{simulated_agent_error_message}', 实际: '{response_data['detail']}'"