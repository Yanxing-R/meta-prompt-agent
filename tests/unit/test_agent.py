# tests/unit/test_agent.py
import pytest
import os
import json
import io 
import builtins
import requests 
import google.generativeai as genai 
import dashscope # 确保导入 dashscope 以便 mock
from dashscope.api_entities.dashscope_response import Role, GenerationResponse, GenerationOutput, Choice, Message
from http import HTTPStatus


# 导入所有需要测试的函数和依赖
from meta_prompt_agent.core.agent import (
    call_ollama_api, 
    call_gemini_api, 
    call_qwen_api, # 新增导入
    invoke_llm,      
    load_and_format_structured_prompt, 
    load_feedback, 
    save_feedback,
    generate_and_refine_prompt,
    explain_term_in_prompt 
)
from meta_prompt_agent.config import settings 
from meta_prompt_agent.prompts.templates import ( 
    CORE_META_PROMPT_TEMPLATE,
    STRUCTURED_PROMPT_TEMPLATES,
    EVALUATION_META_PROMPT_TEMPLATE, 
    REFINEMENT_META_PROMPT_TEMPLATE,
    EXPLAIN_TERM_TEMPLATE 
)


# --- 模块级别的辅助类定义 (MockResponse 已存在) ---
class MockResponse: # 用于模拟 requests.Response
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
            raise requests.exceptions.JSONDecodeError("No JSON content or invalid JSON", "doc", 0)
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            http_error = requests.exceptions.HTTPError(f"Mocked HTTP Error {self.status_code}", response=self)
            raise http_error

# --- 已有的测试用例 (保持不变，但确保其mock目标已更新为invoke_llm如果适用) ---
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

# --- Tests for call_ollama_api (这些测试直接测试call_ollama_api，保持不变) ---
def test_call_ollama_api_success(monkeypatch):
    prompt_content = "这是一个测试提示。"
    expected_response_content = "这是Ollama返回的模拟内容。"
    def mock_post_success(*args, **kwargs):
        payload_str = kwargs.get('data')
        assert payload_str is not None
        payload = json.loads(payload_str)
        assert payload.get('model') == settings.OLLAMA_MODEL
        assert payload['messages'][-1]['content'] == prompt_content
        mock_api_response = {"message": {"content": expected_response_content}}
        return MockResponse(json_data=mock_api_response, status_code=200)
    monkeypatch.setattr(requests, 'post', mock_post_success)
    result_content, error_details = call_ollama_api(prompt_content)
    assert error_details is None
    assert result_content == expected_response_content

# ... (其他 test_call_ollama_api_... 测试用例保持不变) ...
def test_call_ollama_api_connection_error(monkeypatch):
    prompt_content = "这是一个会遇到连接错误的提示。"
    def mock_post_raises_connection_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Simulated Connection Error")
    monkeypatch.setattr(requests, 'post', mock_post_raises_connection_error)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content.startswith("错误：无法连接到Ollama服务")
    assert error_details is not None and error_details.get("type") == "ConnectionError"

def test_call_ollama_api_http_error(monkeypatch):
    prompt_content = "这是一个会遇到HTTP错误的提示。"
    http_status_code = 400 
    error_response_json = {"error": "Invalid model"} 
    def mock_post_raises_http_error(*args, **kwargs):
        prepared_request = requests.Request('POST', args[0] if args else kwargs.get('url', settings.OLLAMA_API_URL)).prepare()
        return MockResponse(json_data=error_response_json, status_code=http_status_code, request_obj=prepared_request)
    monkeypatch.setattr(requests, 'post', mock_post_raises_http_error)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content.startswith(f"错误：Ollama API交互失败 (HTTP {http_status_code})")
    assert error_details is not None and error_details.get("type") == "HTTPError"

def test_call_ollama_api_timeout(monkeypatch):
    prompt_content = "这是一个会遇到超时的提示。"
    def mock_post_raises_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Simulated Request Timeout")
    monkeypatch.setattr(requests, 'post', mock_post_raises_timeout)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content.startswith("错误：请求Ollama API超时")
    assert error_details is not None and error_details.get("type") == "TimeoutError"

def test_call_ollama_api_unexpected_response_format(monkeypatch):
    prompt_content = "这是一个会得到意外格式响应的提示。"
    mock_api_response = {"model": "test_model", "wrong_key": "some_content"} # 缺少 message.content
    def mock_post_unexpected_format(*args, **kwargs):
        return MockResponse(json_data=mock_api_response, status_code=200)
    monkeypatch.setattr(requests, 'post', mock_post_unexpected_format)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content == "错误：Ollama API响应格式不符合预期"
    assert error_details is not None and error_details.get("type") == "FormatError"

def test_call_ollama_api_unknown_error(monkeypatch):
    prompt_content = "这是一个会遇到未知错误的提示。"
    def mock_post_raises_generic_exception(*args, **kwargs):
        raise RuntimeError("Simulated generic error") 
    monkeypatch.setattr(requests, 'post', mock_post_raises_generic_exception)
    result_content, error_details = call_ollama_api(prompt_content)
    assert result_content == "错误：调用Ollama API时发生未知内部错误"
    assert error_details is not None and error_details.get("type") == "UnknownError"


# --- Tests for generate_and_refine_prompt (这些将需要改为mock invoke_llm) ---
def test_generate_and_refine_prompt_no_self_correction_success(monkeypatch):
    user_raw_request = "帮我写一个关于猫的笑话。"
    task_type = "通用/问答" 
    expected_p1_prompt = "这是一个由Ollama优化后的关于猫的笑话提示。"
    mock_invoke_llm_calls = [] 
    def mock_successful_invoke_llm(prompt_content_sent, messages_history=None):
        mock_invoke_llm_calls.append({
            "prompt_content_sent": prompt_content_sent,
            "messages_history": messages_history
        })
        return expected_p1_prompt, None 
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_successful_invoke_llm) 
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type=task_type,
        enable_self_correction=False, max_recursion_depth=0,      
        use_structured_template_name=None, structured_template_vars=None
    )
    assert results.get("error_message") is None
    assert results.get("p1_initial_optimized_prompt") == expected_p1_prompt
    assert results.get("final_prompt") == expected_p1_prompt
    assert len(mock_invoke_llm_calls) == 1 
    expected_initial_llm_prompt = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert mock_invoke_llm_calls[0]["prompt_content_sent"] == expected_initial_llm_prompt
    assert results.get("initial_core_prompt") == expected_initial_llm_prompt

# ... (其他 test_generate_and_refine_prompt_... 测试用例也需要类似修改mock目标为 invoke_llm) ...
def test_generate_and_refine_prompt_initial_api_call_fails(monkeypatch):
    user_raw_request = "一个会触发初始API失败的请求。"
    simulated_api_error_message = "错误：模拟的LLM API连接失败"
    simulated_api_error_details = {"type": "ConnectionError", "details": "连接超时"}
    def mock_failing_invoke_llm(prompt_content_sent, messages_history=None):
        return simulated_api_error_message, simulated_api_error_details
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_failing_invoke_llm)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="通用/问答",
        enable_self_correction=False, max_recursion_depth=0,
        use_structured_template_name=None, structured_template_vars=None
    )
    assert results.get("error_message") == f"生成初始优化提示失败: {simulated_api_error_message}"
    assert results.get("error_details") == simulated_api_error_details

def test_generate_and_refine_prompt_structured_template_success_no_correction(monkeypatch):
    user_raw_request = "用Python写一个斐波那契函数。" 
    template_name = "BasicCodeSnippet" 
    template_vars = {"programming_language": "Python"}
    formatted_structured_prompt = "这是由BasicCodeSnippet模板和Python变量格式化后的核心指令。"
    expected_api_response = "def fibonacci(n): # 这是LLM对结构化提示的响应"
    
    mock_load_format_calls = []
    def mock_successful_load_format(tn, ur, tv):
        mock_load_format_calls.append(True)
        return formatted_structured_prompt
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', mock_successful_load_format)
    
    mock_invoke_llm_calls = []
    def mock_successful_invoke_llm(prompt_content_sent, messages_history=None):
        mock_invoke_llm_calls.append({"prompt_content_sent": prompt_content_sent})
        assert prompt_content_sent == formatted_structured_prompt 
        return expected_api_response, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_successful_invoke_llm)
    
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="代码生成",
        enable_self_correction=False, max_recursion_depth=0,
        use_structured_template_name=template_name, structured_template_vars=template_vars
    )
    assert results.get("error_message") is None
    assert len(mock_load_format_calls) == 1
    assert len(mock_invoke_llm_calls) == 1
    assert results.get("initial_core_prompt") == formatted_structured_prompt
    assert results.get("p1_initial_optimized_prompt") == expected_api_response

def test_generate_and_refine_prompt_with_self_correction_one_iteration_success(monkeypatch):
    user_raw_request = "写一个关于太空旅行的短故事。"
    expected_p1 = "初步优化的太空故事提示 (P1)"
    expected_e1_json_str = json.dumps({"evaluation_summary": {"main_weaknesses": "主角不明确"}})
    expected_e1_dict = json.loads(expected_e1_json_str)
    expected_p2 = "精炼后的太空故事提示，包含主角 (P2)"
    mock_invoke_llm_log = []
    def mock_invoke_llm_multi_call(prompt_content_sent, messages_history=None):
        call_order = len(mock_invoke_llm_log)
        mock_invoke_llm_log.append(prompt_content_sent)
        if call_order == 0: return expected_p1, None
        elif call_order == 1: return expected_e1_json_str, None
        elif call_order == 2: return expected_p2, None
        pytest.fail("invoke_llm被意外调用过多")
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_multi_call)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="通用/问答",
        enable_self_correction=True, max_recursion_depth=1,
        use_structured_template_name=None, structured_template_vars=None
    )
    assert results.get("error_message") is None
    assert len(mock_invoke_llm_log) == 3
    assert results.get("p1_initial_optimized_prompt") == expected_p1
    assert results.get("evaluation_reports")[0] == expected_e1_dict
    assert results.get("refined_prompts")[0] == expected_p2
    assert results.get("final_prompt") == expected_p2

def test_generate_and_refine_prompt_self_correction_stops_if_no_change(monkeypatch):
    user_raw_request = "一个不需要改变的完美请求。"
    expected_p1 = "完美的初始提示 (P1)"
    expected_e1_json_str = json.dumps({"evaluation_summary": {"main_strengths": "完美"}})
    expected_e1_dict = json.loads(expected_e1_json_str)
    mock_invoke_llm_log = []
    def mock_invoke_llm_stops_on_no_change(prompt_content_sent, messages_history=None):
        call_order = len(mock_invoke_llm_log)
        mock_invoke_llm_log.append(True)
        if call_order == 0: return expected_p1, None
        elif call_order == 1: return expected_e1_json_str, None
        elif call_order == 2: return expected_p1, None # P2与P1相同
        pytest.fail("invoke_llm不应在无变化后继续调用")
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_stops_on_no_change)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="通用/问答",
        enable_self_correction=True, max_recursion_depth=2,
        use_structured_template_name=None, structured_template_vars=None
    )
    assert results.get("error_message") is None
    assert len(mock_invoke_llm_log) == 3
    assert results.get("final_prompt") == expected_p1

def test_generate_and_refine_prompt_evaluation_call_fails(monkeypatch):
    user_raw_request = "一个在评估阶段会失败的请求。"
    expected_p1 = "成功的初始提示 (P1)"
    simulated_eval_error_msg = "错误：评估API失败"
    simulated_eval_error_details = {"type": "APIError"}
    mock_invoke_llm_log = []
    def mock_invoke_llm_eval_fails(prompt_content_sent, messages_history=None):
        call_order = len(mock_invoke_llm_log)
        mock_invoke_llm_log.append(True)
        if call_order == 0: return expected_p1, None
        elif call_order == 1: return simulated_eval_error_msg, simulated_eval_error_details
        pytest.fail("invoke_llm不应在评估失败后继续调用")
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_eval_fails)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="通用/问答",
        enable_self_correction=True, max_recursion_depth=1,
        use_structured_template_name=None, structured_template_vars=None
    )
    assert results.get("error_message") is None # 内部错误，不设顶层错误
    assert len(mock_invoke_llm_log) == 2
    assert results.get("final_prompt") == expected_p1

def test_generate_and_refine_prompt_refinement_call_fails(monkeypatch):
    user_raw_request = "一个在精炼阶段会失败的请求。"
    expected_p1 = "成功的初始提示 (P1)"
    expected_e1_json_str = json.dumps({"evaluation_summary": {"main_strengths": "OK"}})
    expected_e1_dict = json.loads(expected_e1_json_str)
    simulated_refine_error_msg = "错误：精炼API失败"
    simulated_refine_error_details = {"type": "APIError"}
    mock_invoke_llm_log = []
    def mock_invoke_llm_refine_fails(prompt_content_sent, messages_history=None):
        call_order = len(mock_invoke_llm_log)
        mock_invoke_llm_log.append(True)
        if call_order == 0: return expected_p1, None
        elif call_order == 1: return expected_e1_json_str, None
        elif call_order == 2: return simulated_refine_error_msg, simulated_refine_error_details
        pytest.fail("invoke_llm不应在精炼失败后继续调用")
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_refine_fails)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="通用/问答",
        enable_self_correction=True, max_recursion_depth=1,
        use_structured_template_name=None, structured_template_vars=None
    )
    assert results.get("error_message") is None
    assert len(mock_invoke_llm_log) == 3
    assert results.get("evaluation_reports")[0] == expected_e1_dict
    assert results.get("final_prompt") == expected_p1

def test_generate_and_refine_prompt_structured_template_load_fails(monkeypatch):
    user_raw_request = "一个请求，但其选择的结构化模板会加载失败。"
    expected_p1_from_core = "这是基于CORE_META_PROMPT的回退优化提示。"
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', lambda *args: None) # Mock加载失败
    
    mock_invoke_llm_calls = []
    def mock_invoke_llm_receives_core(prompt_content_sent, messages_history=None):
        mock_invoke_llm_calls.append(prompt_content_sent)
        assert CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request) in prompt_content_sent
        return expected_p1_from_core, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_receives_core)
    
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="代码生成",
        enable_self_correction=False, max_recursion_depth=0,
        use_structured_template_name="DetailedCodeFunction", structured_template_vars={}
    )
    assert results.get("error_message") is None
    assert results.get("initial_core_prompt") == CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert results.get("p1_initial_optimized_prompt") == expected_p1_from_core

def test_generate_and_refine_prompt_task_type_image_gen_fallback(monkeypatch):
    user_raw_request = "一只在月球上戴着宇航员头盔的猫，数字艺术风格。"
    expected_p1_from_basic_image_gen = "这是由BasicImageGen优化后的图像提示。"
    expected_initial_llm_prompt = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(user_raw_request=user_raw_request)
    
    mock_invoke_llm_calls = []
    def mock_invoke_llm_receives_image_gen(prompt_content_sent, messages_history=None):
        mock_invoke_llm_calls.append(prompt_content_sent)
        assert prompt_content_sent == expected_initial_llm_prompt
        return expected_p1_from_basic_image_gen, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_receives_image_gen)
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', lambda *args: pytest.fail("不应调用"))

    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request, task_type="图像生成",
        enable_self_correction=False, max_recursion_depth=0,
        use_structured_template_name=None, structured_template_vars=None
    )
    assert results.get("error_message") is None
    assert results.get("initial_core_prompt") == expected_initial_llm_prompt
    assert results.get("p1_initial_optimized_prompt") == expected_p1_from_basic_image_gen


# --- Tests for explain_term_in_prompt (已更新mock目标为invoke_llm) ---
def test_explain_term_in_prompt_success(monkeypatch):
    term_to_explain = "角色扮演"
    context_prompt = "请使用角色扮演的方式，扮演一个海盗船长，然后告诉我一个宝藏的故事。"
    expected_explanation = "角色扮演是指让AI模仿特定的身份或性格来进行回应..."
    mock_invoke_calls = [] 
    def mock_successful_invoke_llm_for_explain(prompt_content_sent, messages_history=None):
        mock_invoke_calls.append(prompt_content_sent)
        expected_explain_request = EXPLAIN_TERM_TEMPLATE.format(
            term_to_explain=term_to_explain,
            context_prompt=context_prompt
        )
        assert prompt_content_sent == expected_explain_request
        return expected_explanation, None 
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_successful_invoke_llm_for_explain)
    explanation, error_details = explain_term_in_prompt(term_to_explain, context_prompt)
    assert error_details is None
    assert explanation == expected_explanation.strip()
    assert len(mock_invoke_calls) == 1

def test_explain_term_in_prompt_empty_term(monkeypatch):
    term_to_explain = ""
    context_prompt = "一些上下文。"
    mock_invoke_llm_calls = []
    def mock_invoke_llm_should_not_be_called(*args, **kwargs):
        mock_invoke_llm_calls.append(True)
        pytest.fail("invoke_llm 不应在输入验证失败时被调用")
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_should_not_be_called)
    explanation, error_details = explain_term_in_prompt(term_to_explain, context_prompt)
    assert explanation.startswith("错误：需要提供要解释的术语。")
    assert error_details is not None and error_details.get("type") == "InputValidationError"
    assert len(mock_invoke_llm_calls) == 0

def test_explain_term_in_prompt_empty_context(monkeypatch):
    term_to_explain = "某个术语"
    context_prompt = "   " 
    mock_invoke_llm_calls = []
    def mock_invoke_llm_should_not_be_called(*args, **kwargs):
        mock_invoke_llm_calls.append(True)
        pytest.fail("invoke_llm 不应在输入验证失败时被调用")
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_invoke_llm_should_not_be_called)
    explanation, error_details = explain_term_in_prompt(term_to_explain, context_prompt)
    assert explanation.startswith("错误：需要提供术语所在的上下文提示。")
    assert error_details is not None and error_details.get("type") == "InputValidationError"
    assert len(mock_invoke_llm_calls) == 0

def test_explain_term_in_prompt_api_call_fails(monkeypatch):
    term_to_explain = "复杂术语"
    context_prompt = "包含这个复杂术语的提示。"
    simulated_api_error_message = "错误：LLM连接失败" 
    simulated_api_error_details = {"type": "ConnectionError", "details": "模拟连接失败"}
    def mock_failing_invoke_llm(prompt_content_sent, messages_history=None):
        return simulated_api_error_message, simulated_api_error_details
    monkeypatch.setattr('meta_prompt_agent.core.agent.invoke_llm', mock_failing_invoke_llm)
    explanation, error_details = explain_term_in_prompt(term_to_explain, context_prompt)
    assert explanation == simulated_api_error_message
    assert error_details == simulated_api_error_details

# --- 新增 invoke_llm 的测试用例 ---
def test_invoke_llm_calls_ollama_when_provider_is_ollama(monkeypatch):
    monkeypatch.setattr(settings, 'ACTIVE_LLM_PROVIDER', 'ollama')
    mock_ollama_calls = []
    def mock_call_ollama(*args, **kwargs):
        mock_ollama_calls.append(True)
        return "ollama_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_call_ollama)
    mock_gemini_calls = [] # 确保其他API没被调用
    def mock_call_gemini(*args, **kwargs): mock_gemini_calls.append(True); return "gemini_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_gemini_api', mock_call_gemini)
    mock_qwen_calls = []
    def mock_call_qwen(*args, **kwargs): mock_qwen_calls.append(True); return "qwen_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_qwen_api', mock_call_qwen)
    result, error = invoke_llm("test prompt")
    assert result == "ollama_response" and error is None
    assert len(mock_ollama_calls) == 1 and len(mock_gemini_calls) == 0 and len(mock_qwen_calls) == 0

def test_invoke_llm_calls_gemini_when_provider_is_gemini(monkeypatch):
    monkeypatch.setattr(settings, 'ACTIVE_LLM_PROVIDER', 'gemini')
    mock_gemini_calls = []
    def mock_call_gemini(*args, **kwargs): mock_gemini_calls.append(True); return "gemini_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_gemini_api', mock_call_gemini)
    mock_ollama_calls = [] 
    def mock_call_ollama(*args, **kwargs): mock_ollama_calls.append(True); return "ollama_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_call_ollama)
    mock_qwen_calls = []
    def mock_call_qwen(*args, **kwargs): mock_qwen_calls.append(True); return "qwen_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_qwen_api', mock_call_qwen)
    result, error = invoke_llm("test prompt")
    assert result == "gemini_response" and error is None
    assert len(mock_gemini_calls) == 1 and len(mock_ollama_calls) == 0 and len(mock_qwen_calls) == 0

def test_invoke_llm_calls_qwen_when_provider_is_qwen(monkeypatch): # 新增Qwen的测试
    """测试当 ACTIVE_LLM_PROVIDER 为 'qwen' 时，invoke_llm 调用 call_qwen_api"""
    monkeypatch.setattr(settings, 'ACTIVE_LLM_PROVIDER', 'qwen')
    mock_qwen_calls = []
    def mock_call_qwen(*args, **kwargs): mock_qwen_calls.append(True); return "qwen_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_qwen_api', mock_call_qwen)
    mock_ollama_calls = [] 
    def mock_call_ollama(*args, **kwargs): mock_ollama_calls.append(True); return "ollama_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_call_ollama)
    mock_gemini_calls = []
    def mock_call_gemini(*args, **kwargs): mock_gemini_calls.append(True); return "gemini_response", None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_gemini_api', mock_call_gemini)
    result, error = invoke_llm("test prompt")
    assert result == "qwen_response" and error is None
    assert len(mock_qwen_calls) == 1 and len(mock_ollama_calls) == 0 and len(mock_gemini_calls) == 0


def test_invoke_llm_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, 'ACTIVE_LLM_PROVIDER', 'unknown_provider')
    result, error = invoke_llm("test prompt")
    assert result.startswith("错误：未知的LLM服务提供者配置")
    assert error is not None and error.get("type") == "ConfigurationError"


# --- 新增 call_gemini_api 的测试用例 (已存在部分) ---
class MockGeminiContentPart:
    def __init__(self, text): self.text = text
class MockGeminiContent:
    def __init__(self, parts_text_list): self.parts = [MockGeminiContentPart(text) for text in parts_text_list]
class MockGeminiCandidate:
    def __init__(self, content_parts_text_list):
        self.content = MockGeminiContent(content_parts_text_list)
        self.finish_reason = None 
        self.safety_ratings = []
class MockGeminiResponseSDK: # 重命名以避免与我们的MockResponse冲突
    def __init__(self, candidates_data_list, prompt_feedback=None):
        self.candidates = [MockGeminiCandidate(data) for data in candidates_data_list]
        self.prompt_feedback = prompt_feedback
class MockGenerativeModel:
    def __init__(self, model_name):
        self.model_name = model_name
        self.generate_content_calls = [] 
        self.mock_response_data = None 
        self.mock_exception = None 
    def generate_content(self, contents, *args, **kwargs):
        self.generate_content_calls.append({"contents": contents, "args": args, "kwargs": kwargs})
        if self.mock_exception: raise self.mock_exception
        if self.mock_response_data: return self.mock_response_data
        return MockGeminiResponseSDK(candidates_data_list=[[""]]) 
    def set_next_response(self, response_data): self.mock_response_data = response_data
    def set_next_exception(self, exception): self.mock_exception = exception

def test_call_gemini_api_success(monkeypatch):
    prompt_content = "你好 Gemini"
    expected_gemini_text = "你好，我是 Gemini！"
    mock_model_instance = MockGenerativeModel(settings.GEMINI_MODEL_NAME)
    mock_model_instance.set_next_response(
        MockGeminiResponseSDK(candidates_data_list=[[expected_gemini_text]])
    )
    monkeypatch.setattr(genai, 'GenerativeModel', lambda *args, **kwargs: mock_model_instance)
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'test_api_key') 
    result, error = call_gemini_api(prompt_content)
    assert error is None and result == expected_gemini_text
    assert len(mock_model_instance.generate_content_calls) == 1

def test_call_gemini_api_no_api_key(monkeypatch):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', None) 
    result, error = call_gemini_api("test prompt")
    assert result.startswith("错误：Gemini API 密钥未配置。")
    assert error is not None and error.get("type") == "ConfigurationError"

def test_call_gemini_api_sdk_error(monkeypatch):
    prompt_content = "一个会导致SDK出错的提示"
    simulated_sdk_error = RuntimeError("Simulated SDK internal error")
    mock_model_instance = MockGenerativeModel(settings.GEMINI_MODEL_NAME)
    mock_model_instance.set_next_exception(simulated_sdk_error)
    monkeypatch.setattr(genai, 'GenerativeModel', lambda *args, **kwargs: mock_model_instance)
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'test_api_key')
    result, error = call_gemini_api(prompt_content)
    assert result.startswith(f"错误：调用 Gemini API ({settings.GEMINI_MODEL_NAME}) 时发生错误: RuntimeError - {simulated_sdk_error}")
    assert error is not None and error.get("type") == "GeminiAPIError"

def test_call_gemini_api_content_blocked(monkeypatch):
    prompt_content = "一个可能触发安全过滤的提示"
    mock_model_instance = MockGenerativeModel(settings.GEMINI_MODEL_NAME)
    class MockBlockedPromptFeedback:
        def __init__(self, reason): self.block_reason = reason; self.safety_ratings = []
    mock_response_blocked = MockGeminiResponseSDK(
        candidates_data_list=[[]], 
        prompt_feedback=MockBlockedPromptFeedback("SAFETY")
    )
    mock_model_instance.set_next_response(mock_response_blocked)
    monkeypatch.setattr(genai, 'GenerativeModel', lambda *args, **kwargs: mock_model_instance)
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'test_api_key')
    result, error = call_gemini_api(prompt_content)
    assert result.startswith("错误：Gemini API 未返回有效内容。可能原因: 内容被安全过滤器阻止")
    assert error is not None and error.get("type") == "GeminiContentError"

# --- 新增 call_qwen_api 的测试用例 ---
# 辅助类，用于模拟 dashscope.Generation.call 的响应对象
class MockQwenSDKResponse:
    def __init__(self, status_code, output_choices_content=None, request_id="test_req_id", code=None, message=None):
        self.status_code = status_code
        self.request_id = request_id
        self.code = code
        self.message = message # API层面错误时，SDK的message字段可能包含错误信息
        if status_code == HTTPStatus.OK and output_choices_content:
            # 构造一个符合成功响应结构的 output 和 choices
            choice_message = Message(role=Role.ASSISTANT, content=output_choices_content)
            choice = Choice(message=choice_message, finish_reason="stop")
            self.output = GenerationOutput(choices=[choice], text=None, finish_reason=None) # text和finish_reason在顶层output中可能为None
        else:
            self.output = None # 错误时或无内容时output可能为None或不包含有效choices

    def __str__(self): # 用于错误详情中的raw_response
        return f"MockQwenSDKResponse(status_code={self.status_code}, message='{self.message}', output={self.output})"


def test_call_qwen_api_success(monkeypatch):
    """测试 call_qwen_api 成功获取响应"""
    prompt_content = "你好通义千问"
    expected_qwen_text = "你好，我是通义千问！很高兴为您服务。"
    
    mock_dashscope_calls = []
    def mock_dashscope_generation_call(model, messages, result_format, **kwargs):
        mock_dashscope_calls.append({"model": model, "messages": messages})
        assert model == settings.QWEN_MODEL_NAME
        assert messages[-1]["role"] == Role.USER
        assert messages[-1]["content"] == prompt_content
        assert result_format == 'message'
        return MockQwenSDKResponse(status_code=HTTPStatus.OK, output_choices_content=expected_qwen_text)

    monkeypatch.setattr(dashscope.Generation, 'call', mock_dashscope_generation_call)
    monkeypatch.setattr(settings, 'QWEN_API_KEY', 'test_qwen_api_key') # 确保API Key存在

    result, error = call_qwen_api(prompt_content)

    assert error is None, f"成功时不应有错误: {error}"
    assert result == expected_qwen_text, f"预期 '{expected_qwen_text}', 得到 '{result}'"
    assert len(mock_dashscope_calls) == 1, "dashscope.Generation.call 应被调用一次"

def test_call_qwen_api_no_api_key(monkeypatch):
    """测试当 Qwen API Key 未配置时，call_qwen_api 返回错误"""
    monkeypatch.setattr(settings, 'QWEN_API_KEY', None)
    
    result, error = call_qwen_api("test prompt")
    
    assert result.startswith("错误：通义千问 API 密钥未配置。")
    assert error is not None
    assert error.get("type") == "ConfigurationError"

def test_call_qwen_api_sdk_call_fails_http_error(monkeypatch):
    """测试当 dashscope.Generation.call 返回非OK状态码时"""
    prompt_content = "一个会导致API失败的提示"
    error_status_code = HTTPStatus.BAD_REQUEST # 400
    error_api_message = "Invalid parameter"
    error_api_code = "InvalidParameter"

    def mock_dashscope_generation_call_fails(*args, **kwargs):
        return MockQwenSDKResponse(
            status_code=error_status_code, 
            message=error_api_message,
            code=error_api_code
        )
    monkeypatch.setattr(dashscope.Generation, 'call', mock_dashscope_generation_call_fails)
    monkeypatch.setattr(settings, 'QWEN_API_KEY', 'test_qwen_api_key')

    result, error = call_qwen_api(prompt_content)

    assert result.startswith(f"错误：通义千问 API 调用失败。状态码: {error_status_code}。"), result
    assert error is not None
    assert error.get("type") == "QwenAPIError"
    assert error.get("status_code") == error_status_code
    assert error.get("error_message_from_api") == error_api_message
    assert error.get("error_code") == error_api_code

def test_call_qwen_api_sdk_call_raises_exception(monkeypatch):
    """测试当 dashscope.Generation.call 抛出SDK内部异常时"""
    prompt_content = "一个会导致SDK异常的提示"
    simulated_sdk_exception = ValueError("Simulated Dashscope SDK error")

    def mock_dashscope_generation_call_raises_exception(*args, **kwargs):
        raise simulated_sdk_exception
    monkeypatch.setattr(dashscope.Generation, 'call', mock_dashscope_generation_call_raises_exception)
    monkeypatch.setattr(settings, 'QWEN_API_KEY', 'test_qwen_api_key')

    result, error = call_qwen_api(prompt_content)
    
    assert result.startswith(f"错误：调用通义千问 API ({settings.QWEN_MODEL_NAME}) 时发生SDK或未知错误: ValueError - {simulated_sdk_exception}")
    assert error is not None
    assert error.get("type") == "QwenSDKError"
    assert error.get("exception_type") == "ValueError"

def test_call_qwen_api_unexpected_response_format(monkeypatch):
    """测试当Qwen API响应成功但格式不符合预期（例如缺少output或choices）"""
    prompt_content = "提示"
    
    def mock_dashscope_bad_format(*args, **kwargs):
        # 模拟一个 status_code=OK 但 output 为 None 的情况
        return MockQwenSDKResponse(status_code=HTTPStatus.OK, output_choices_content=None) 
    monkeypatch.setattr(dashscope.Generation, 'call', mock_dashscope_bad_format)
    monkeypatch.setattr(settings, 'QWEN_API_KEY', 'test_qwen_api_key')

    result, error = call_qwen_api(prompt_content)

    assert result.startswith("错误：通义千问 API响应格式不符合预期")
    assert error is not None
    assert error.get("type") == "QwenFormatError"

