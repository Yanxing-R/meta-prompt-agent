# tests/unit/test_agent.py
import pytest
import os
import json
import io 
import builtins
import requests 

# 导入所有需要测试的函数和依赖
from meta_prompt_agent.core.agent import (
    call_ollama_api, 
    load_and_format_structured_prompt, 
    load_feedback, 
    save_feedback,
    generate_and_refine_prompt 
)
from meta_prompt_agent.config import settings 
from meta_prompt_agent.prompts.templates import ( 
    CORE_META_PROMPT_TEMPLATE,
    STRUCTURED_PROMPT_TEMPLATES,
    EVALUATION_META_PROMPT_TEMPLATE, # 确保这是最新的JSON输出版本
    REFINEMENT_META_PROMPT_TEMPLATE  
)


# --- 模块级别的辅助类定义 (MockResponse 已存在) ---
class MockResponse:
    def __init__(self, json_data, status_code, text_data=None, request_obj=None):
        self.json_data = json_data
        self.status_code = status_code
        if text_data is not None:
            self.text = text_data
        elif json_data is not None:
            self.text = json.dumps(json_data)
        else:
            self.text = ""
        self.request = request_obj if request_obj else requests.Request('POST', settings.OLLAMA_API_URL).prepare()

    def json(self):
        if self.json_data is None:
            # 模拟真实 requests 库在内容不是有效JSON时的行为
            raise requests.exceptions.JSONDecodeError("No JSON content or invalid JSON", "doc", 0)
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            http_error = requests.exceptions.HTTPError(f"Mocked HTTP Error {self.status_code}", response=self)
            raise http_error

# --- 已有的测试用例 (保持不变) ---
def test_load_and_format_structured_prompt_template_not_found():
    template_name = "non_existent_template"
    user_request = "一些用户请求"
    variables = {}
    result = load_and_format_structured_prompt(template_name, user_request, variables)
    assert result is None, f"当模板 '{template_name}' 不存在时，函数应返回 None，但返回了 {result}"

def test_load_and_format_structured_prompt_missing_variables():
    template_name = "ExplainConcept" 
    user_request = "解释一下黑洞"
    variables_none = None
    result_none_vars = load_and_format_structured_prompt(template_name, user_request, variables_none)
    assert result_none_vars is None, f"当模板 '{template_name}' 需要变量但 variables 为 None 时，应返回 None，但返回了 {result_none_vars}"
    variables_empty = {}
    result_empty_vars = load_and_format_structured_prompt(template_name, user_request, variables_empty)
    assert result_empty_vars is None, f"当模板 '{template_name}' 需要变量但 variables 为空字典时，应返回 None，但返回了 {result_empty_vars}"
    if template_name in STRUCTURED_PROMPT_TEMPLATES and \
       "concept_to_explain" in STRUCTURED_PROMPT_TEMPLATES[template_name].get("variables", []):
        variables_partial = {"target_audience": "初学者"} 
        result_partial_vars = load_and_format_structured_prompt(template_name, user_request, variables_partial)
        assert result_partial_vars is None, (
            f"当模板 '{template_name}' 缺少必需变量 'concept_to_explain' 时，应返回 None，"
            f"但返回了 {result_partial_vars}"
        )
    else:
        pytest.skip(f"测试场景假设模板 '{template_name}' 需要 'concept_to_explain' 变量，请核实模板定义。")

def test_load_and_format_structured_prompt_success():
    template_name = "ExplainConcept" 
    user_request = "请通俗易懂地解释一下什么是黑洞。"
    variables = {
        "concept_to_explain": "黑洞",
        "target_audience": "对天文感兴趣的初中生"
    }
    expected_substrings = [
        user_request, 
        variables["concept_to_explain"], 
        variables["target_audience"] 
    ]
    result = load_and_format_structured_prompt(template_name, user_request, variables)
    assert result is not None, (
        f"当模板 '{template_name}' 和所有必需变量都提供时，函数不应返回 None。"
    )
    assert isinstance(result, str), (
        f"当格式化成功时，函数应返回一个字符串，但返回了类型 {type(result)}。"
    )
    for substring in expected_substrings:
        assert substring in result, (
            f"格式化后的提示词中应包含子字符串 '{substring}'，但实际内容为:\n'{result}'"
        )

def test_load_feedback_file_not_exists(monkeypatch):
    def mock_exists(path):
        return False
    monkeypatch.setattr(os.path, 'exists', mock_exists)
    result = load_feedback()
    assert result == [], f"当反馈文件不存在时，load_feedback 应返回空列表，但返回了 {result}"

def test_load_feedback_empty_file(monkeypatch, tmp_path):
    temp_feedback_file = tmp_path / "test_feedback.json"
    temp_feedback_file.write_text("") 
    monkeypatch.setattr(settings, 'FEEDBACK_FILE', str(temp_feedback_file))
    monkeypatch.setattr(os.path, 'exists', lambda path: path == str(temp_feedback_file))
    result = load_feedback()
    assert result == [], f"当反馈文件为空时，load_feedback 应返回空列表，但返回了 {result}"

def test_load_feedback_valid_json(monkeypatch, tmp_path):
    expected_data = [
        {"id": 1, "feedback": "good"},
        {"id": 2, "feedback": "excellent"}
    ]
    temp_feedback_file = tmp_path / "test_feedback_valid.json"
    temp_feedback_file.write_text(json.dumps(expected_data), encoding='utf-8')
    monkeypatch.setattr(settings, 'FEEDBACK_FILE', str(temp_feedback_file))
    monkeypatch.setattr(os.path, 'exists', lambda path: path == str(temp_feedback_file))
    result = load_feedback()
    assert result == expected_data, (
        f"当反馈文件包含有效JSON时，load_feedback 返回的数据与预期不符。\n"
        f"预期: {expected_data}\n"
        f"实际: {result}"
    )

def test_load_feedback_invalid_json(monkeypatch, tmp_path):
    invalid_json_content = "这不是一个有效的JSON{, "
    temp_feedback_file = tmp_path / "test_feedback_invalid.json"
    temp_feedback_file.write_text(invalid_json_content, encoding='utf-8')
    monkeypatch.setattr(settings, 'FEEDBACK_FILE', str(temp_feedback_file))
    monkeypatch.setattr(os.path, 'exists', lambda path: path == str(temp_feedback_file))
    result = load_feedback()
    assert result == [], (
        f"当反馈文件包含无效JSON时，load_feedback 应返回空列表，但返回了 {result}"
    )

def test_load_feedback_io_error(monkeypatch, tmp_path):
    temp_feedback_file = tmp_path / "test_feedback_io_error.json"
    temp_feedback_file.write_text("irrelevant content")
    monkeypatch.setattr(settings, 'FEEDBACK_FILE', str(temp_feedback_file))
    monkeypatch.setattr(os.path, 'exists', lambda path: path == str(temp_feedback_file))
    def mock_open_raises_io_error(*args, **kwargs):
        raise IOError("Simulated IOError during file open/read")
    monkeypatch.setattr(builtins, 'open', mock_open_raises_io_error)
    result = load_feedback()
    assert result == [], (
        f"当读取反馈文件时发生IOError，load_feedback 应返回空列表，但返回了 {result}"
    )

def test_save_feedback_success_new_file(monkeypatch, tmp_path):
    feedback_data_to_save = [
        {"request": "req1", "rating": 5, "comment": "great"},
        {"request": "req2", "rating": 4, "comment": "good"}
    ]
    temp_feedback_file = tmp_path / "test_save_feedback.json"
    monkeypatch.setattr(settings, 'FEEDBACK_FILE', str(temp_feedback_file))
    save_result = save_feedback(feedback_data_to_save)
    assert save_result is True, "save_feedback 在成功时应返回 True"
    assert temp_feedback_file.exists(), "反馈文件应该被创建"
    try:
        with open(temp_feedback_file, 'r', encoding='utf-8') as f:
            saved_data_from_file = json.load(f)
        assert saved_data_from_file == feedback_data_to_save
    except FileNotFoundError:
        pytest.fail("save_feedback 声称成功，但反馈文件未找到。")
    except json.JSONDecodeError:
        pytest.fail(f"save_feedback 写入的文件不是有效的JSON。文件内容: {temp_feedback_file.read_text(encoding='utf-8')}")

def test_save_feedback_overwrite_existing_file(monkeypatch, tmp_path):
    initial_data = [{"request": "initial_req", "rating": 1, "comment": "initial"}]
    data_to_overwrite_with = [
        {"request": "new_req1", "rating": 5, "comment": "overwritten_great"},
        {"request": "new_req2", "rating": 4, "comment": "overwritten_good"}
    ]
    temp_feedback_file = tmp_path / "test_feedback_overwrite.json"
    with open(temp_feedback_file, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=4)
    monkeypatch.setattr(settings, 'FEEDBACK_FILE', str(temp_feedback_file))
    save_result = save_feedback(data_to_overwrite_with)
    assert save_result is True, "save_feedback 在成功覆盖时应返回 True"
    assert temp_feedback_file.exists(), "反馈文件在覆盖后应仍然存在"
    try:
        with open(temp_feedback_file, 'r', encoding='utf-8') as f:
            saved_data_from_file = json.load(f)
        assert saved_data_from_file == data_to_overwrite_with
    except FileNotFoundError:
        pytest.fail("save_feedback 声称成功，但反馈文件未找到（不应发生）。")
    except json.JSONDecodeError:
        pytest.fail(f"save_feedback 覆盖后写入的文件不是有效的JSON。文件内容: {temp_feedback_file.read_text(encoding='utf-8')}")

def test_save_feedback_io_error_on_write(monkeypatch, tmp_path):
    feedback_data_to_save = [{"request": "req_io_error", "rating": 1, "comment": "io_error_test"}]
    temp_feedback_file = tmp_path / "test_feedback_write_io_error.json"
    monkeypatch.setattr(settings, 'FEEDBACK_FILE', str(temp_feedback_file))
    def mock_open_raises_io_error_on_write(file, mode='r', *args, **kwargs):
        if 'w' in mode.lower():
            raise IOError("Simulated IOError during file write operation")
        return builtins.open(file,mode,*args,**kwargs) 
    monkeypatch.setattr(builtins, 'open', mock_open_raises_io_error_on_write)
    save_result = save_feedback(feedback_data_to_save)
    assert save_result is False, (
        "当写入反馈文件时发生IOError，save_feedback 应返回 False，但返回了 True"
    )

def test_call_ollama_api_success(monkeypatch):
    prompt_content = "这是一个测试提示。"
    expected_response_content = "这是Ollama返回的模拟内容。"
    def mock_post_success(*args, **kwargs):
        payload_str = kwargs.get('data')
        assert payload_str is not None, "requests.post 的 'data' 参数不应为 None"
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            pytest.fail(f"传递给 requests.post 的 'data' 参数不是有效的JSON字符串: {payload_str}")
        assert payload.get('model') == settings.OLLAMA_MODEL
        assert 'messages' in payload
        assert len(payload.get('messages', [])) > 0
        last_message = payload['messages'][-1]
        assert last_message.get('role') == 'user'
        assert last_message.get('content') == prompt_content
        mock_api_response = {
            "model": settings.OLLAMA_MODEL,
            "created_at": "2023-10-26T12:00:00Z", 
            "message": {"role": "assistant", "content": expected_response_content},
            "done": True
        }
        return MockResponse(json_data=mock_api_response, status_code=200)
    monkeypatch.setattr(requests, 'post', mock_post_success)
    result_content, error_details = call_ollama_api(prompt_content)
    assert error_details is None, f"成功调用时不应返回错误详情，但返回了: {error_details}"
    assert result_content == expected_response_content

def test_call_ollama_api_connection_error(monkeypatch):
    prompt_content = "这是一个会遇到连接错误的提示。"
    def mock_post_raises_connection_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Simulated Connection Error")
    monkeypatch.setattr(requests, 'post', mock_post_raises_connection_error)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content.startswith("错误：无法连接到Ollama服务"), \
        f"错误消息开头不符合预期。实际: '{result_content}'"
    assert error_details is not None
    assert error_details.get("type") == "ConnectionError"
    assert error_details.get("url") == settings.OLLAMA_API_URL
    assert "Simulated Connection Error" in error_details.get("details", "")


def test_call_ollama_api_http_error(monkeypatch):
    prompt_content = "这是一个会遇到HTTP错误的提示。"
    http_status_code = 400 
    error_response_json = {"error": "Invalid request parameter: model not found"} 
    def mock_post_raises_http_error(*args, **kwargs):
        url_for_request = args[0] if args else kwargs.get('url', settings.OLLAMA_API_URL)
        prepared_request = requests.Request('POST', url_for_request).prepare()
        return MockResponse(json_data=error_response_json, status_code=http_status_code, request_obj=prepared_request)
    monkeypatch.setattr(requests, 'post', mock_post_raises_http_error)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content.startswith(f"错误：Ollama API交互失败 (HTTP {http_status_code})"), \
        f"错误消息开头不符合预期。实际: '{result_content}'"
    if "error" in error_response_json:
         assert error_response_json["error"] in result_content, \
             f"返回的错误消息中未包含Ollama的具体错误 '{error_response_json['error']}'. 实际: '{result_content}'"
    assert error_details is not None
    assert error_details.get("type") == "HTTPError"
    assert error_details.get("status_code") == http_status_code
    assert error_details.get("raw_response") == json.dumps(error_response_json)
    if "error" in error_response_json:
        assert error_details.get("ollama_error") == error_response_json["error"]

def test_call_ollama_api_timeout(monkeypatch):
    prompt_content = "这是一个会遇到超时的提示。"
    def mock_post_raises_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Simulated Request Timeout")
    monkeypatch.setattr(requests, 'post', mock_post_raises_timeout)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content.startswith("错误：请求Ollama API超时"), \
        f"错误消息开头不符合预期。实际: '{result_content}'"
    assert error_details is not None
    assert error_details.get("type") == "TimeoutError"
    assert error_details.get("url") == settings.OLLAMA_API_URL
    assert "Simulated Request Timeout" in error_details.get("details", "")

def test_call_ollama_api_unexpected_response_format(monkeypatch):
    prompt_content = "这是一个会得到意外格式响应的提示。"
    unexpected_format_1 = {
        "model": settings.OLLAMA_MODEL, "created_at": "2023-10-27T10:00:00Z",
        "response_text": "一些其他内容，但没有message字段", "done": True
    }
    unexpected_format_2 = {
        "model": settings.OLLAMA_MODEL, "created_at": "2023-10-27T11:00:00Z",
        "message": {"role": "assistant", "summary": "这是一个摘要"}, "done": True
    }
    test_cases = [
        ("missing_message_key", unexpected_format_1),
        ("missing_content_in_message", unexpected_format_2)
    ]
    for test_name, mock_api_response in test_cases:
        def mock_post_unexpected_format(*args, **kwargs):
            return MockResponse(json_data=mock_api_response, status_code=200)
        monkeypatch.setattr(requests, 'post', mock_post_unexpected_format)
        result_content, error_details = call_ollama_api(prompt_content)
        assert result_content == "错误：Ollama API响应格式不符合预期", \
            f"对于场景 '{test_name}'，错误消息不符合预期。实际: '{result_content}'"
        assert error_details is not None, f"对于场景 '{test_name}'，error_details 不应为 None"
        assert error_details.get("type") == "FormatError", \
            f"对于场景 '{test_name}'，错误类型不为 'FormatError'。实际: '{error_details.get('type')}'"
        assert error_details.get("details") == mock_api_response, \
            f"对于场景 '{test_name}'，错误详情中的响应数据不符合预期。"

def test_call_ollama_api_unknown_error(monkeypatch):
    prompt_content = "这是一个会遇到未知错误的提示。"
    simulated_error_message = "Simulated generic runtime error"
    def mock_post_raises_generic_exception(*args, **kwargs):
        raise RuntimeError(simulated_error_message) 
    monkeypatch.setattr(requests, 'post', mock_post_raises_generic_exception)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content == "错误：调用Ollama API时发生未知内部错误", \
        f"错误消息不符合预期。实际: '{result_content}'"
    assert error_details is not None, "发生未知错误时，error_details 不应为 None"
    assert error_details.get("type") == "UnknownError", \
        f"错误类型不为 'UnknownError'。实际: '{error_details.get('type')}'"
    assert error_details.get("exception_type") == "RuntimeError", \
        f"错误详情中的异常类型不符合预期。实际: '{error_details.get('exception_type')}'"
    assert error_details.get("details") == "详情请查看应用日志", \
        f"错误详情中的details文本不符合预期。实际: '{error_details.get('details')}'"

# --- Tests for generate_and_refine_prompt ---

def test_generate_and_refine_prompt_no_self_correction_success(monkeypatch):
    user_raw_request = "帮我写一个关于猫的笑话。"
    task_type = "通用/问答" 
    expected_p1_prompt = "这是一个由Ollama优化后的关于猫的笑话提示。"
    mock_call_ollama_api_calls = [] 
    def mock_successful_ollama_call(prompt_content_sent, messages_history=None):
        mock_call_ollama_api_calls.append({
            "prompt_content_sent": prompt_content_sent,
            "messages_history": messages_history
        })
        return expected_p1_prompt, None 
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_successful_ollama_call)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False, 
        max_recursion_depth=0,      
        use_structured_template_name=None, 
        structured_template_vars=None
    )
    assert results is not None, "结果不应为 None"
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    assert results.get("p1_initial_optimized_prompt") == expected_p1_prompt, \
        "p1_initial_optimized_prompt 与预期不符"
    assert results.get("final_prompt") == expected_p1_prompt, \
        "final_prompt 在禁用自我校正时应等于 p1_initial_optimized_prompt"
    assert len(results.get("evaluation_reports", [])) == 0, "不应有评估报告"
    assert len(results.get("refined_prompts", [])) == 0, "不应有精炼提示"
    assert len(mock_call_ollama_api_calls) == 1, \
        f"call_ollama_api 应只被调用1次，实际调用了 {len(mock_call_ollama_api_calls)} 次"
    expected_initial_llm_prompt = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert mock_call_ollama_api_calls[0]["prompt_content_sent"] == expected_initial_llm_prompt, \
        "发送给 call_ollama_api 的初始提示内容不符合预期"
    assert results.get("initial_core_prompt") == expected_initial_llm_prompt, \
        "results中的initial_core_prompt不符合预期"

def test_generate_and_refine_prompt_initial_api_call_fails(monkeypatch):
    user_raw_request = "一个会触发初始API失败的请求。"
    task_type = "通用/问答"
    simulated_api_error_message = "错误：模拟的Ollama API连接失败"
    simulated_api_error_details = {"type": "ConnectionError", "details": "连接超时"}
    def mock_failing_ollama_call(prompt_content_sent, messages_history=None):
        return simulated_api_error_message, simulated_api_error_details
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_failing_ollama_call)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False, 
        max_recursion_depth=0,
        use_structured_template_name=None,
        structured_template_vars=None
    )
    assert results is not None, "结果不应为 None"
    assert results.get("error_message") is not None, "应包含错误消息"
    assert results.get("error_message") == f"生成初始优化提示失败: {simulated_api_error_message}", \
        "返回的 error_message 与预期不符"
    assert results.get("error_details") == simulated_api_error_details, \
        "返回的 error_details 与预期不符"
    assert results.get("p1_initial_optimized_prompt") == "", "p1_initial_optimized_prompt 应为空字符串或未设置"
    assert results.get("final_prompt") == "", "final_prompt 应为空字符串或未设置"

def test_generate_and_refine_prompt_structured_template_success_no_correction(monkeypatch):
    user_raw_request = "用Python写一个斐波那契函数。" 
    task_type = "代码生成" 
    template_name = "BasicCodeSnippet" 
    template_vars = {"programming_language": "Python"}
    formatted_structured_prompt = "这是由BasicCodeSnippet模板和Python变量格式化后的核心指令。"
    expected_api_response = "def fibonacci(n): # 这是Ollama对结构化提示的响应"
    mock_load_format_calls = []
    def mock_successful_load_format(tn, ur, tv):
        mock_load_format_calls.append({"template_name": tn, "user_request": ur, "variables": tv})
        assert tn == template_name
        assert ur == user_raw_request 
        assert tv == template_vars
        return formatted_structured_prompt
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', mock_successful_load_format)
    mock_call_ollama_api_calls = []
    def mock_successful_ollama_call_for_structured(prompt_content_sent, messages_history=None):
        mock_call_ollama_api_calls.append({"prompt_content_sent": prompt_content_sent})
        assert prompt_content_sent == formatted_structured_prompt 
        return expected_api_response, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_successful_ollama_call_for_structured)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False,
        max_recursion_depth=0,
        use_structured_template_name=template_name, 
        structured_template_vars=template_vars
    )
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    assert len(mock_load_format_calls) == 1, "load_and_format_structured_prompt 应被调用1次"
    assert len(mock_call_ollama_api_calls) == 1, "call_ollama_api 应被调用1次"
    assert results.get("initial_core_prompt") == formatted_structured_prompt, \
        "initial_core_prompt 应为格式化后的结构化提示"
    assert results.get("p1_initial_optimized_prompt") == expected_api_response, \
        "p1_initial_optimized_prompt 与预期API响应不符"
    assert results.get("final_prompt") == expected_api_response, \
        "final_prompt 在此场景下应等于 p1_initial_optimized_prompt"

# 修改后的测试用例，以适应JSON评估报告
def test_generate_and_refine_prompt_with_self_correction_one_iteration_success(monkeypatch):
    """
    测试启用自我校正 (max_recursion_depth=1) 时，函数是否按预期
    调用 call_ollama_api 三次 (P1, E1, P2) 并返回正确结果，
    其中 E1 是JSON格式的评估报告。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "写一个关于太空旅行的短故事。"
    task_type = "通用/问答" 

    expected_p1 = "初步优化的太空故事提示 (P1)"
    # 模拟的JSON评估报告 (作为字符串，因为API会返回字符串)
    expected_e1_json_str = json.dumps({
        "evaluation_summary": {
            "overall_score": 4,
            "main_strengths": "P1主题明确。",
            "main_weaknesses": "P1可以更具体描述主角。"
        },
        "dimension_scores": {
            "clarity": {"score": 5, "justification": "清晰"},
            "completeness": {"score": 3, "justification": "缺少主角细节"},
            "specificity_actionability": {"score": 4, "justification": "基本可操作"},
            "faithfulness_consistency": {"score": 5, "justification": "忠于原意"}
        },
        "potential_risks": {"level": "Low", "description": "无明显风险"},
        "suggestions_for_improvement": ["建议添加主角的姓名和目标。"]
    })
    # 解析后的期望E1字典
    expected_e1_dict = json.loads(expected_e1_json_str)
    
    expected_p2 = "精炼后的太空故事提示，包含主角姓名和目标 (P2)"

    mock_ollama_call_log = []
    def mock_ollama_multi_call_with_json_eval(prompt_content_sent, messages_history=None):
        call_number = len(mock_ollama_call_log)
        mock_ollama_call_log.append({
            "call_order": call_number,
            "prompt_content_sent": prompt_content_sent,
            "messages_history_length": len(messages_history) if messages_history else 0
        })
        
        if call_number == 0: 
            assert CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request) in prompt_content_sent
            return expected_p1, None
        elif call_number == 1: 
            # 确保发送的是新的评估模板
            assert EVALUATION_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request, prompt_to_evaluate=expected_p1) in prompt_content_sent
            return expected_e1_json_str, None # 返回JSON字符串
        elif call_number == 2: 
            # 确保精炼模板接收到的是原始的E1字符串 (或根据agent.py的实现调整)
            # 当前 agent.py 实现是传递 evaluation_report_str
            assert REFINEMENT_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request, previous_prompt=expected_p1, evaluation_report=expected_e1_json_str) in prompt_content_sent
            return expected_p2, None
        else:
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}

    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_multi_call_with_json_eval)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True, 
        max_recursion_depth=1,       
        use_structured_template_name=None,
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    
    assert len(mock_ollama_call_log) == 3, \
        f"call_ollama_api 应被调用3次，实际调用了 {len(mock_ollama_call_log)} 次"

    assert results.get("p1_initial_optimized_prompt") == expected_p1, "P1 与预期不符"
    
    assert len(results.get("evaluation_reports", [])) == 1, "应有1份评估报告"
    # 验证存储的是解析后的字典
    assert results.get("evaluation_reports")[0] == expected_e1_dict, "解析后的E1与预期不符" 
    
    assert len(results.get("refined_prompts", [])) == 1, "应有1份精炼提示 (P2)"
    assert results.get("refined_prompts")[0] == expected_p2, "P2 与预期不符"
    
    assert results.get("final_prompt") == expected_p2, "最终提示应为P2"

    expected_initial_core = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert results.get("initial_core_prompt") == expected_initial_core, "initial_core_prompt 与预期不符"
    
    assert mock_ollama_call_log[0]["messages_history_length"] == 0 
    assert mock_ollama_call_log[1]["messages_history_length"] == 0, "E1调用的messages_history长度应为0"
    assert mock_ollama_call_log[2]["messages_history_length"] == 4, "P2调用的messages_history长度应为4"


def test_generate_and_refine_prompt_self_correction_stops_if_no_change(monkeypatch):
    user_raw_request = "一个不需要改变的完美请求。"
    task_type = "通用/问答"
    expected_p1 = "完美的初始提示 (P1)" 
    # 模拟的JSON评估报告
    expected_e1_json_str = json.dumps({
        "evaluation_summary": {"overall_score": 5, "main_strengths": "完美", "main_weaknesses": "无"},
        "dimension_scores": {
            "clarity": {"score": 5, "justification": "非常清晰"},
            "completeness": {"score": 5, "justification": "信息完整"},
            "specificity_actionability": {"score": 5, "justification": "可直接执行"},
            "faithfulness_consistency": {"score": 5, "justification": "完全忠实"}
        },
        "potential_risks": {"level": "Low", "description": "无风险"},
        "suggestions_for_improvement": ["无需改进"]
    })
    expected_e1_dict = json.loads(expected_e1_json_str)

    mock_ollama_call_log = []
    def mock_ollama_stops_on_no_change(prompt_content_sent, messages_history=None):
        call_number = len(mock_ollama_call_log)
        mock_ollama_call_log.append({
            "call_order": call_number,
            "prompt_content_sent": prompt_content_sent
        })
        if call_number == 0: 
            return expected_p1, None
        elif call_number == 1: 
            return expected_e1_json_str, None # 返回JSON字符串
        elif call_number == 2: 
            return expected_p1, None # P2 与 P1 相同
        else:
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次（P2与P1相同后不应再调用）")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_stops_on_no_change)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True,
        max_recursion_depth=2, 
        use_structured_template_name=None,
        structured_template_vars=None
    )
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    assert len(mock_ollama_call_log) == 3, \
        f"call_ollama_api 应被调用3次（P1, E1, P2），实际调用了 {len(mock_ollama_call_log)} 次"
    assert results.get("p1_initial_optimized_prompt") == expected_p1
    assert results.get("evaluation_reports")[0] == expected_e1_dict # 验证解析后的字典
    assert len(results.get("refined_prompts", [])) == 1, "refined_prompts 列表应包含一个元素 (P2)"
    assert results.get("refined_prompts")[0] == expected_p1, "refined_prompts[0] (P2) 应等于 P1"
    assert results.get("final_prompt") == expected_p1, "最终提示应为 P1 (因为 P2 与 P1 相同)"

def test_generate_and_refine_prompt_evaluation_call_fails(monkeypatch):
    user_raw_request = "一个在评估阶段会失败的请求。"
    task_type = "通用/问答"
    expected_p1 = "成功的初始提示 (P1)"
    simulated_eval_error_message = "错误：模拟的评估API调用失败"
    simulated_eval_error_details = {"type": "TimeoutError", "details": "评估超时"}
    mock_ollama_call_log = []
    def mock_ollama_eval_fails(prompt_content_sent, messages_history=None):
        call_number = len(mock_ollama_call_log)
        mock_ollama_call_log.append({
            "call_order": call_number,
            "prompt_content_sent": prompt_content_sent
        })
        if call_number == 0: 
            return expected_p1, None
        elif call_number == 1: 
            return simulated_eval_error_message, simulated_eval_error_details
        else:
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次（评估失败后不应再调用）")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_eval_fails)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True,
        max_recursion_depth=1, 
        use_structured_template_name=None,
        structured_template_vars=None
    )
    assert results.get("error_message") is None, \
        f"顶层不应有错误消息（内部警告会被记录），但得到: {results.get('error_message')}"
    assert len(mock_ollama_call_log) == 2, \
        f"call_ollama_api 应被调用2次（P1, E1尝试），实际调用了 {len(mock_ollama_call_log)} 次"
    assert results.get("p1_initial_optimized_prompt") == expected_p1
    assert len(results.get("evaluation_reports", [])) == 0, "evaluation_reports 列表应为空"
    assert len(results.get("refined_prompts", [])) == 0, "refined_prompts 列表应为空"
    assert results.get("final_prompt") == expected_p1, "最终提示应为 P1 (因为评估失败)"

def test_generate_and_refine_prompt_refinement_call_fails(monkeypatch):
    user_raw_request = "一个在精炼阶段会失败的请求。"
    task_type = "通用/问答"
    expected_p1 = "成功的初始提示 (P1)"
    # 模拟的JSON评估报告
    expected_e1_json_str = json.dumps({
        "evaluation_summary": {"overall_score": 3, "main_strengths": "...", "main_weaknesses": "..."},
        "dimension_scores": {"clarity": {"score": 3, "justification": "..."}},
        "potential_risks": {"level": "Low", "description": "..."},
        "suggestions_for_improvement": ["..."]
    })
    expected_e1_dict = json.loads(expected_e1_json_str)
    simulated_refinement_error_message = "错误：模拟的精炼API调用失败"
    simulated_refinement_error_details = {"type": "HTTPError", "status_code": 500, "details": "精炼服务内部错误"}
    mock_ollama_call_log = []
    def mock_ollama_refinement_fails(prompt_content_sent, messages_history=None):
        call_number = len(mock_ollama_call_log)
        mock_ollama_call_log.append({
            "call_order": call_number,
            "prompt_content_sent": prompt_content_sent
        })
        if call_number == 0: 
            return expected_p1, None
        elif call_number == 1: 
            return expected_e1_json_str, None # 返回JSON字符串
        elif call_number == 2: 
            return simulated_refinement_error_message, simulated_refinement_error_details
        else:
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次（精炼失败后不应再调用）")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_refinement_fails)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True,
        max_recursion_depth=1, 
        use_structured_template_name=None,
        structured_template_vars=None
    )
    assert results.get("error_message") is None, \
        f"顶层不应有错误消息（内部警告会被记录），但得到: {results.get('error_message')}"
    assert len(mock_ollama_call_log) == 3, \
        f"call_ollama_api 应被调用3次（P1, E1, P2尝试），实际调用了 {len(mock_ollama_call_log)} 次"
    assert results.get("p1_initial_optimized_prompt") == expected_p1
    assert len(results.get("evaluation_reports", [])) == 1, "应有1份评估报告 (E1)"
    assert results.get("evaluation_reports")[0] == expected_e1_dict # 验证解析后的字典
    assert len(results.get("refined_prompts", [])) == 0, "refined_prompts 列表应为空"
    assert results.get("final_prompt") == expected_p1, "最终提示应为 P1 (因为精炼失败)"

def test_generate_and_refine_prompt_structured_template_load_fails(monkeypatch):
    user_raw_request = "一个请求，但其选择的结构化模板会加载失败。"
    task_type = "代码生成" 
    template_name_to_fail = "DetailedCodeFunction" 
    template_vars = {"programming_language": "Python", "function_name": "my_func"} 
    expected_p1_from_core = "这是基于CORE_META_PROMPT的回退优化提示。"
    mock_load_format_calls = []
    def mock_failing_load_format(tn, ur, tv):
        mock_load_format_calls.append({"template_name": tn, "user_request": ur, "variables": tv})
        assert tn == template_name_to_fail 
        return None 
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', mock_failing_load_format)
    mock_ollama_calls = []
    def mock_ollama_receives_core_template(prompt_content_sent, messages_history=None):
        mock_ollama_calls.append({"prompt_content_sent": prompt_content_sent})
        expected_fallback_prompt = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
        assert prompt_content_sent == expected_fallback_prompt
        return expected_p1_from_core, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_receives_core_template)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False, 
        max_recursion_depth=0,
        use_structured_template_name=template_name_to_fail, 
        structured_template_vars=template_vars
    )
    assert results.get("error_message") is None, \
        f"不应有错误消息（内部模板加载失败会被处理），但得到: {results.get('error_message')}"
    assert len(mock_load_format_calls) == 1, "load_and_format_structured_prompt 应被调用1次"
    assert mock_load_format_calls[0]["template_name"] == template_name_to_fail
    assert len(mock_ollama_calls) == 1, "call_ollama_api 应被调用1次"
    expected_initial_core_fallback = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert results.get("initial_core_prompt") == expected_initial_core_fallback, \
        "initial_core_prompt 应为回退后的 CORE_META_PROMPT_TEMPLATE"
    assert results.get("p1_initial_optimized_prompt") == expected_p1_from_core
    assert results.get("final_prompt") == expected_p1_from_core

def test_generate_and_refine_prompt_task_type_image_gen_fallback(monkeypatch):
    user_raw_request = "一只在月球上戴着宇航员头盔的猫，数字艺术风格。"
    task_type = "图像生成"
    expected_p1_from_basic_image_gen = "这是由BasicImageGen优化后的图像提示。"
    assert "BasicImageGen" in STRUCTURED_PROMPT_TEMPLATES
    assert "core_template_override" in STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]
    expected_initial_llm_prompt = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(
        user_raw_request=user_raw_request
    )
    mock_ollama_calls = []
    def mock_ollama_receives_basic_image_gen(prompt_content_sent, messages_history=None):
        mock_ollama_calls.append({"prompt_content_sent": prompt_content_sent})
        assert prompt_content_sent == expected_initial_llm_prompt
        return expected_p1_from_basic_image_gen, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_receives_basic_image_gen)
    mock_load_format_calls = []
    def mock_load_format_should_not_be_called(*args, **kwargs):
        mock_load_format_calls.append(True)
        pytest.fail("load_and_format_structured_prompt 不应在此场景下被调用")
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', mock_load_format_should_not_be_called)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False,
        max_recursion_depth=0,
        use_structured_template_name=None, 
        structured_template_vars=None
    )
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    assert len(mock_load_format_calls) == 0, "load_and_format_structured_prompt 不应被调用"
    assert len(mock_ollama_calls) == 1, "call_ollama_api 应被调用1次"
    assert results.get("initial_core_prompt") == expected_initial_llm_prompt, \
        "initial_core_prompt 应为 BasicImageGen 的核心模板内容"
    assert results.get("p1_initial_optimized_prompt") == expected_p1_from_basic_image_gen
    assert results.get("final_prompt") == expected_p1_from_basic_image_gen

