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
    generate_and_refine_prompt # 新增导入
)
from meta_prompt_agent.config import settings 
from meta_prompt_agent.prompts.templates import ( # 确保导入这些模板变量
    CORE_META_PROMPT_TEMPLATE,
    STRUCTURED_PROMPT_TEMPLATES,
    EVALUATION_META_PROMPT_TEMPLATE, # 虽然这个测试不用，但 generate_and_refine_prompt 可能会引用
    REFINEMENT_META_PROMPT_TEMPLATE  # 同上
)


# --- 模块级别的辅助类定义 ---
class MockResponse:
    """
    一个通用的模拟 requests.Response 对象的类，用于测试。
    """
    def __init__(self, json_data, status_code, text_data=None, request_obj=None):
        self.json_data = json_data
        self.status_code = status_code
        # 如果 text_data 未提供，尝试从 json_data 生成，否则为空字符串
        if text_data is not None:
            self.text = text_data
        elif json_data is not None:
            self.text = json.dumps(json_data)
        else:
            self.text = ""
        
        # request 属性对于 HTTPError 是必需的
        self.request = request_obj if request_obj else requests.Request('POST', settings.OLLAMA_API_URL).prepare()


    def json(self):
        if self.json_data is None:
            # 模拟真实 requests 库在内容不是有效JSON时的行为
            raise requests.exceptions.JSONDecodeError("No JSON content or invalid JSON", "doc", 0)
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            # HTTPError 需要 response 参数，我们将自身 (self) 作为 response 传递
            http_error = requests.exceptions.HTTPError(f"Mocked HTTP Error {self.status_code}", response=self)
            # HTTPError 对象也需要 request 属性，我们在 __init__ 中确保它存在
            # http_error.request = self.request # request 应该在创建 HTTPError 时通过 response 参数间接设置
            raise http_error

# --- Tests for load_and_format_structured_prompt (已存在) ---
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

# --- Tests for load_feedback (已存在) ---
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

# --- Tests for save_feedback (已存在) ---
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
        # Fallback for other modes, though not strictly needed for this specific test's current scope
        return builtins.open(file,mode,*args,**kwargs) # Or a more sophisticated mock if needed
    monkeypatch.setattr(builtins, 'open', mock_open_raises_io_error_on_write)
    save_result = save_feedback(feedback_data_to_save)
    assert save_result is False, (
        "当写入反馈文件时发生IOError，save_feedback 应返回 False，但返回了 True"
    )

# --- Tests for call_ollama_api ---

def test_call_ollama_api_success(monkeypatch):
    """
    测试 call_ollama_api 在成功调用 Ollama API 并获得有效响应时的行为。
    """
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
        # 使用模块级的 MockResponse
        return MockResponse(json_data=mock_api_response, status_code=200)

    monkeypatch.setattr(requests, 'post', mock_post_success)
    result_content, error_details = call_ollama_api(prompt_content)
    assert error_details is None, f"成功调用时不应返回错误详情，但返回了: {error_details}"
    assert result_content == expected_response_content

def test_call_ollama_api_connection_error(monkeypatch):
    """
    测试当 requests.post 抛出 ConnectionError 时，call_ollama_api 的行为。
    """
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

def test_call_ollama_api_http_error(monkeypatch):
    """
    测试当 requests.post 返回 HTTP 错误状态码 (如 400, 500) 时，call_ollama_api 的行为。
    """
    prompt_content = "这是一个会遇到HTTP错误的提示。"
    http_status_code = 400 
    error_response_json = {"error": "Invalid request parameter: model not found"} 

    def mock_post_raises_http_error(*args, **kwargs):
        # 准备一个模拟的 request 对象，它可能被 HTTPError 使用
        # args[0] 通常是 URL
        url_for_request = args[0] if args else kwargs.get('url', settings.OLLAMA_API_URL)
        prepared_request = requests.Request('POST', url_for_request).prepare()
        # 使用模块级的 MockResponse
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

# 测试发生 Timeout 的情况
def test_call_ollama_api_timeout(monkeypatch):
    """
    测试当 requests.post 抛出 Timeout 时，call_ollama_api 的行为。
    """
    # 1. 准备 (Arrange)
    prompt_content = "这是一个会遇到超时的提示。"
    
    # 定义当 requests.post 被调用时，我们希望它抛出 Timeout 异常
    def mock_post_raises_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Simulated Request Timeout")

    # 使用 monkeypatch 将 requests.post 替换为我们的模拟函数
    monkeypatch.setattr(requests, 'post', mock_post_raises_timeout)

    # 2. 执行 (Act)
    result_content, error_details = call_ollama_api(prompt_content)

    # 3. 断言 (Assert)
    assert result_content.startswith("错误：请求Ollama API超时"), \
        f"错误消息开头不符合预期。实际: '{result_content}'"
    
    assert error_details is not None, "发生超时错误时，error_details 不应为 None"
    assert error_details.get("type") == "TimeoutError", \
        f"错误类型不为 'TimeoutError'。实际: '{error_details.get('type')}'"
    assert error_details.get("url") == settings.OLLAMA_API_URL, \
        f"错误详情中的URL不符合预期。实际: '{error_details.get('url')}'"
    assert "Simulated Request Timeout" in error_details.get("details", ""), \
        "错误详情中未包含原始超时错误信息"

# 测试API响应格式不符合预期的情况
def test_call_ollama_api_unexpected_response_format(monkeypatch):
    """
    测试当 Ollama API 返回成功状态码但JSON格式不符合预期时，call_ollama_api 的行为。
    例如，缺少 "message" 键或 "message.content" 键。
    """
    # 1. 准备 (Arrange)
    prompt_content = "这是一个会得到意外格式响应的提示。"
    
    # 场景1: 响应中缺少 "message" 键
    unexpected_format_1 = {
        "model": settings.OLLAMA_MODEL,
        "created_at": "2023-10-27T10:00:00Z",
        "response_text": "一些其他内容，但没有message字段", # 假设这是API返回的
        "done": True
    }
    # 场景2: 响应中有 "message" 键，但 "message" 字典中缺少 "content" 键
    unexpected_format_2 = {
        "model": settings.OLLAMA_MODEL,
        "created_at": "2023-10-27T11:00:00Z",
        "message": {
            "role": "assistant",
            # "content": "应该在这里的内容" # content 键缺失
            "summary": "这是一个摘要"
        },
        "done": True
    }

    test_cases = [
        ("missing_message_key", unexpected_format_1),
        ("missing_content_in_message", unexpected_format_2)
    ]

    for test_name, mock_api_response in test_cases:
        # print(f"Running sub-test: {test_name}") # For debugging
        def mock_post_unexpected_format(*args, **kwargs):
            return MockResponse(json_data=mock_api_response, status_code=200)

        monkeypatch.setattr(requests, 'post', mock_post_unexpected_format)

        # 2. 执行 (Act)
        result_content, error_details = call_ollama_api(prompt_content)

        # 3. 断言 (Assert)
        assert result_content == "错误：Ollama API响应格式不符合预期", \
            f"对于场景 '{test_name}'，错误消息不符合预期。实际: '{result_content}'"
        
        assert error_details is not None, f"对于场景 '{test_name}'，error_details 不应为 None"
        assert error_details.get("type") == "FormatError", \
            f"对于场景 '{test_name}'，错误类型不为 'FormatError'。实际: '{error_details.get('type')}'"
        
        # 检查原始响应是否被包含在 details 中
        assert error_details.get("details") == mock_api_response, \
            f"对于场景 '{test_name}'，错误详情中的响应数据不符合预期。"
        
# 测试发生未知错误 (generic Exception) 的情况
def test_call_ollama_api_unknown_error(monkeypatch):
    """
    测试当 requests.post 或其后续处理中抛出任何未被特定捕获的 Exception 时，
    call_ollama_api 的行为。
    """
    # 1. 准备 (Arrange)
    prompt_content = "这是一个会遇到未知错误的提示。"
    simulated_error_message = "Simulated generic runtime error"
    
    # 定义当 requests.post 被调用时，我们希望它抛出通用的 Exception
    def mock_post_raises_generic_exception(*args, **kwargs):
        raise RuntimeError(simulated_error_message) # 使用 RuntimeError 或其他通用异常

    # 使用 monkeypatch 将 requests.post 替换为我们的模拟函数
    monkeypatch.setattr(requests, 'post', mock_post_raises_generic_exception)

    # 2. 执行 (Act)
    result_content, error_details = call_ollama_api(prompt_content)

    # 3. 断言 (Assert)
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
    """
    测试 generate_and_refine_prompt 在禁用自我校正时，
    成功调用一次 call_ollama_api 并返回结果的场景。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "帮我写一个关于猫的笑话。"
    task_type = "通用/问答" # 或者任何一个不强制使用特定结构化模板的类型
    expected_p1_prompt = "这是一个由Ollama优化后的关于猫的笑话提示。"

    # 模拟 call_ollama_api 函数
    # 它应该被调用一次，并返回预期的 p1_initial_optimized_prompt
    mock_call_ollama_api_calls = [] # 用于记录调用次数和参数 (可选)
    def mock_successful_ollama_call(prompt_content_sent, messages_history=None):
        mock_call_ollama_api_calls.append({
            "prompt_content_sent": prompt_content_sent,
            "messages_history": messages_history
        })
        # 第一次调用（也是唯一一次，因为禁用了自我校正）返回成功的优化提示
        return expected_p1_prompt, None 
    
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_successful_ollama_call)

    # （可选）如果 generate_and_refine_prompt 内部会调用 load_and_format_structured_prompt，
    # 并且我们想控制其行为或确保它不被意外调用（对于这个简单场景），也可以mock它。
    # 在这个测试中，我们选择 task_type="通用/问答" 和 use_structured_template_name=None，
    # 期望它可能使用 CORE_META_PROMPT_TEMPLATE，而不调用 load_and_format_structured_prompt。
    # 如果它确实调用了，我们需要确保mock的行为或提供一个有效的模板。
    # 为了简单起见，我们先不mock load_and_format_structured_prompt，
    # 而是依赖 generate_and_refine_prompt 内部的逻辑来处理这种情况。
    # 如果测试因此失败，说明我们的假设（它不调用或能正确处理）是错误的，需要调整。

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False, # 关键：禁用自我校正
        max_recursion_depth=0,      # 深度为0也表示不进行递归
        use_structured_template_name=None, # 不使用特定的结构化模板
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results is not None, "结果不应为 None"
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    
    assert results.get("p1_initial_optimized_prompt") == expected_p1_prompt, \
        "p1_initial_optimized_prompt 与预期不符"
    assert results.get("final_prompt") == expected_p1_prompt, \
        "final_prompt 在禁用自我校正时应等于 p1_initial_optimized_prompt"
    
    assert len(results.get("evaluation_reports", [])) == 0, "不应有评估报告"
    assert len(results.get("refined_prompts", [])) == 0, "不应有精炼提示"

    # 验证 call_ollama_api 是否只被调用了一次
    assert len(mock_call_ollama_api_calls) == 1, \
        f"call_ollama_api 应只被调用1次，实际调用了 {len(mock_call_ollama_api_calls)} 次"
    
    # （可选）验证传递给 call_ollama_api 的参数
    # 我们期望第一次调用时，发送的是基于 CORE_META_PROMPT_TEMPLATE 和 user_raw_request 格式化后的内容
    expected_initial_llm_prompt = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert mock_call_ollama_api_calls[0]["prompt_content_sent"] == expected_initial_llm_prompt, \
        "发送给 call_ollama_api 的初始提示内容不符合预期"
    assert results.get("initial_core_prompt") == expected_initial_llm_prompt, \
        "results中的initial_core_prompt不符合预期"

# 测试初始API调用失败的情况
def test_generate_and_refine_prompt_initial_api_call_fails(monkeypatch):
    """
    测试当第一次调用 call_ollama_api (获取P1) 失败时，
    generate_and_refine_prompt 是否正确处理并返回错误。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "一个会触发初始API失败的请求。"
    task_type = "通用/问答"
    simulated_api_error_message = "错误：模拟的Ollama API连接失败"
    simulated_api_error_details = {"type": "ConnectionError", "details": "连接超时"}

    # 模拟 call_ollama_api 函数，使其在第一次调用时返回错误
    def mock_failing_ollama_call(prompt_content_sent, messages_history=None):
        # 第一次调用（也是唯一一次，因为应该在出错后停止）
        return simulated_api_error_message, simulated_api_error_details
    
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_failing_ollama_call)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False, # 对这个测试场景不重要，因为第一次就失败了
        max_recursion_depth=0,
        use_structured_template_name=None,
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results is not None, "结果不应为 None"
    assert results.get("error_message") is not None, "应包含错误消息"
    assert results.get("error_message") == f"生成初始优化提示失败: {simulated_api_error_message}", \
        "返回的 error_message 与预期不符"
    assert results.get("error_details") == simulated_api_error_details, \
        "返回的 error_details 与预期不符"
    assert results.get("p1_initial_optimized_prompt") == "", "p1_initial_optimized_prompt 应为空字符串或未设置"
    assert results.get("final_prompt") == "", "final_prompt 应为空字符串或未设置"

# 测试成功使用结构化模板（无自我校正）
def test_generate_and_refine_prompt_structured_template_success_no_correction(monkeypatch):
    """
    测试当使用结构化模板且无自我校正时，函数是否正确调用
    load_and_format_structured_prompt 和 call_ollama_api。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "用Python写一个斐波那契函数。" # 这个请求本身可能不直接用，因为模板会覆盖
    task_type = "代码生成" # 假设这个任务类型会触发结构化模板逻辑
    template_name = "BasicCodeSnippet" # 假设这个模板存在
    template_vars = {"programming_language": "Python"}
    
    formatted_structured_prompt = "这是由BasicCodeSnippet模板和Python变量格式化后的核心指令。"
    expected_api_response = "def fibonacci(n): # 这是Ollama对结构化提示的响应"

    # 模拟 load_and_format_structured_prompt
    mock_load_format_calls = []
    def mock_successful_load_format(tn, ur, tv):
        mock_load_format_calls.append({"template_name": tn, "user_request": ur, "variables": tv})
        assert tn == template_name
        assert ur == user_raw_request # 确保原始请求被传递
        assert tv == template_vars
        return formatted_structured_prompt
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', mock_successful_load_format)

    # 模拟 call_ollama_api
    mock_call_ollama_api_calls = []
    def mock_successful_ollama_call_for_structured(prompt_content_sent, messages_history=None):
        mock_call_ollama_api_calls.append({"prompt_content_sent": prompt_content_sent})
        # 期望发送给Ollama的是格式化后的结构化提示
        assert prompt_content_sent == formatted_structured_prompt 
        return expected_api_response, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_successful_ollama_call_for_structured)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False,
        max_recursion_depth=0,
        use_structured_template_name=template_name, # 指定使用结构化模板
        structured_template_vars=template_vars
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    
    # 验证 load_and_format_structured_prompt 被正确调用
    assert len(mock_load_format_calls) == 1, "load_and_format_structured_prompt 应被调用1次"
    
    # 验证 call_ollama_api 被正确调用
    assert len(mock_call_ollama_api_calls) == 1, "call_ollama_api 应被调用1次"
    
    assert results.get("initial_core_prompt") == formatted_structured_prompt, \
        "initial_core_prompt 应为格式化后的结构化提示"
    assert results.get("p1_initial_optimized_prompt") == expected_api_response, \
        "p1_initial_optimized_prompt 与预期API响应不符"
    assert results.get("final_prompt") == expected_api_response, \
        "final_prompt 在此场景下应等于 p1_initial_optimized_prompt"

# 测试启用自我校正并成功完成一次迭代
def test_generate_and_refine_prompt_with_self_correction_one_iteration_success(monkeypatch):
    """
    测试启用自我校正 (max_recursion_depth=1) 时，函数是否按预期
    调用 call_ollama_api 三次 (P1, E1, P2) 并返回正确结果。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "写一个关于太空旅行的短故事。"
    task_type = "通用/问答" # 或其他适合的类型

    # 预设的API调用返回值
    expected_p1 = "初步优化的太空故事提示 (P1)"
    expected_e1 = "对P1的评估报告：P1很好，但可以更具体描述主角 (E1)"
    expected_p2 = "精炼后的太空故事提示，包含主角细节 (P2)"

    # 用于记录 call_ollama_api 的调用顺序和参数
    mock_ollama_call_log = []
    
    # 模拟 call_ollama_api 的行为，使其根据调用次数返回不同的结果
    # 这个内部函数将作为 monkeypatch 的目标
    def mock_ollama_multi_call(prompt_content_sent, messages_history=None):
        call_number = len(mock_ollama_call_log)
        mock_ollama_call_log.append({
            "call_order": call_number,
            "prompt_content_sent": prompt_content_sent,
            "messages_history_length": len(messages_history) if messages_history else 0
        })
        
        if call_number == 0: # 第一次调用，生成 P1
            # 验证发送的初始提示是否正确
            assert CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request) in prompt_content_sent
            return expected_p1, None
        elif call_number == 1: # 第二次调用，生成 E1
            # 验证发送的评估提示是否正确
            assert EVALUATION_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request, prompt_to_evaluate=expected_p1) in prompt_content_sent
            return expected_e1, None
        elif call_number == 2: # 第三次调用，生成 P2
            # 验证发送的精炼提示是否正确
            assert REFINEMENT_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request, previous_prompt=expected_p1, evaluation_report=expected_e1) in prompt_content_sent
            return expected_p2, None
        else:
            # 如果调用次数超出预期，测试应该失败或返回错误
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}

    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_multi_call)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True, # 启用自我校正
        max_recursion_depth=1,       # 限制递归深度为1 (P1 -> E1 -> P2)
        use_structured_template_name=None,
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    
    # 验证 call_ollama_api 被调用了预期的次数 (3次：P1, E1, P2)
    assert len(mock_ollama_call_log) == 3, \
        f"call_ollama_api 应被调用3次，实际调用了 {len(mock_ollama_call_log)} 次"

    # 验证结果字典中的内容
    assert results.get("p1_initial_optimized_prompt") == expected_p1, "P1 与预期不符"
    
    assert len(results.get("evaluation_reports", [])) == 1, "应有1份评估报告"
    assert results.get("evaluation_reports")[0] == expected_e1, "E1 与预期不符"
    
    assert len(results.get("refined_prompts", [])) == 1, "应有1份精炼提示 (P2)"
    assert results.get("refined_prompts")[0] == expected_p2, "P2 与预期不符"
    
    assert results.get("final_prompt") == expected_p2, "最终提示应为P2"

    # 验证 initial_core_prompt
    expected_initial_core = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert results.get("initial_core_prompt") == expected_initial_core, "initial_core_prompt 与预期不符"

    # 验证 messages_history 的传递 (可选，但有助于理解流程)
    # 第一次调用 P1，messages_history 应为 None (或空)
    assert mock_ollama_call_log[0]["messages_history_length"] == 0 
    # 第二次调用 E1，messages_history 应为空 (因为评估是独立的) -> 根据 agent.py 逻辑，eval_prompt_content 是独立发送的
    # 我们的 mock_ollama_multi_call 接收 messages_history，但 agent.py 中对评估的调用是 call_ollama_api(eval_prompt_content, [])
    # 所以这里 messages_history_length 应该是 0 (如果 [] 被视为空) 或者根据实际实现
    # 让我们检查 agent.py: call_ollama_api(eval_prompt_content, []) -> messages_history is []
    # 修正：评估调用的 messages_history 是 []，所以长度是0
    assert mock_ollama_call_log[1]["messages_history_length"] == 0, "E1调用的messages_history长度应为0"
    # 第三次调用 P2，messages_history 应包含 P1的请求和响应，以及E1的请求和响应
    # (user: initial_core_prompt, assistant: P1, user: eval_prompt, assistant: E1) -> 长度为4
    assert mock_ollama_call_log[2]["messages_history_length"] == 4, "P2调用的messages_history长度应为4"

# 测试自我校正因P2与P1相同而停止
def test_generate_and_refine_prompt_self_correction_stops_if_no_change(monkeypatch):
    """
    测试当精炼后的提示 (P2) 与前一版 (P1) 相同时，自我校正循环是否提前停止。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "一个不需要改变的完美请求。"
    task_type = "通用/问答"

    expected_p1 = "完美的初始提示 (P1)" # P1 和 P2 将会相同
    expected_e1 = "对P1的评估报告：P1已经很完美了 (E1)"
    # P2 将会与 P1 相同，以触发停止条件

    mock_ollama_call_log = []
    def mock_ollama_stops_on_no_change(prompt_content_sent, messages_history=None):
        call_number = len(mock_ollama_call_log)
        mock_ollama_call_log.append({
            "call_order": call_number,
            "prompt_content_sent": prompt_content_sent
        })
        
        if call_number == 0: # 生成 P1
            return expected_p1, None
        elif call_number == 1: # 生成 E1
            return expected_e1, None
        elif call_number == 2: # 生成 P2 (与 P1 相同)
            return expected_p1, None # 返回与 P1 相同的内容
        else:
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次（P2与P1相同后不应再调用）")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}

    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_stops_on_no_change)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True,
        max_recursion_depth=2, # 设置一个大于1的深度，以验证是否会提前停止
        use_structured_template_name=None,
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    
    # 验证 call_ollama_api 被调用了预期的次数 (3次：P1, E1, P2)
    # 即使 max_recursion_depth 允许更多，也应该在P2与P1相同时停止
    assert len(mock_ollama_call_log) == 3, \
        f"call_ollama_api 应被调用3次（P1, E1, P2），实际调用了 {len(mock_ollama_call_log)} 次"

    assert results.get("p1_initial_optimized_prompt") == expected_p1
    assert results.get("evaluation_reports")[0] == expected_e1
    
    # refined_prompts 列表应该只包含 P2 (即 expected_p1)
    # 或者，根据 agent.py 的实现，如果 P2==P1，refined_prompts 可能为空，
    # 因为没有“新的”精炼提示被加入。
    # 我们来检查 agent.py 的逻辑:
    # if refined_prompt.strip() == current_best_prompt.strip():
    #     results["log"].append("[代理信息] 精炼后的提示与上一版相同，停止递归。")
    #     break
    # current_best_prompt = refined_prompt 
    # results["refined_prompts"].append(refined_prompt) <-- 这行在 break 之后，所以不会被执行
    # 因此，当 P2==P1 时，refined_prompts 应该为空。
    # 不，refined_prompts 是在 current_best_prompt 更新 *之后* 添加的，但在 break *之前*。
    # 所以，即使P2==P1，P2（即expected_p1）也会被加入 refined_prompts。
    # 让我们重新检查 agent.py 中的循环逻辑：
    #   refined_prompt, error = call_ollama_api(...)
    #   results["refined_prompts"].append(refined_prompt)
    #   if refined_prompt.strip() == current_best_prompt.strip(): break
    #   current_best_prompt = refined_prompt
    # 所以，是的，P2 (即使等于P1) 也会被加入 refined_prompts 列表，然后才 break。
    assert len(results.get("refined_prompts", [])) == 1, "refined_prompts 列表应包含一个元素 (P2)"
    assert results.get("refined_prompts")[0] == expected_p1, "refined_prompts[0] (P2) 应等于 P1"
    
    assert results.get("final_prompt") == expected_p1, "最终提示应为 P1 (因为 P2 与 P1 相同)"

# 新增测试用例：测试评估API调用失败的情况
def test_generate_and_refine_prompt_evaluation_call_fails(monkeypatch):
    """
    测试当获取评估报告 (E1) 的 API 调用失败时，
    generate_and_refine_prompt 是否中断循环并返回 P1 作为最终结果。
    """
    # 1. 准备 (Arrange)
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
        if call_number == 0: # 生成 P1
            return expected_p1, None
        elif call_number == 1: # 尝试生成 E1，但失败
            return simulated_eval_error_message, simulated_eval_error_details
        else:
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次（评估失败后不应再调用）")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}
            
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_eval_fails)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True,
        max_recursion_depth=1, # 即使深度允许，也应在评估失败时停止
        use_structured_template_name=None,
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"顶层不应有错误消息（内部警告会被记录），但得到: {results.get('error_message')}"
    
    assert len(mock_ollama_call_log) == 2, \
        f"call_ollama_api 应被调用2次（P1, E1尝试），实际调用了 {len(mock_ollama_call_log)} 次"

    assert results.get("p1_initial_optimized_prompt") == expected_p1
    # 根据 agent.py 逻辑，如果评估失败，evaluation_reports 应该为空，因为 break 在 append 之前
    assert len(results.get("evaluation_reports", [])) == 0, "evaluation_reports 列表应为空"
    assert len(results.get("refined_prompts", [])) == 0, "refined_prompts 列表应为空"
    assert results.get("final_prompt") == expected_p1, "最终提示应为 P1 (因为评估失败)"

# 测试精炼API调用失败的情况
def test_generate_and_refine_prompt_refinement_call_fails(monkeypatch):
    """
    测试当获取精炼提示 (P2) 的 API 调用失败时，
    generate_and_refine_prompt 是否中断循环并返回 P1 作为最终结果。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "一个在精炼阶段会失败的请求。"
    task_type = "通用/问答"
    expected_p1 = "成功的初始提示 (P1)"
    expected_e1 = "对P1的成功评估 (E1)"
    simulated_refinement_error_message = "错误：模拟的精炼API调用失败"
    simulated_refinement_error_details = {"type": "HTTPError", "status_code": 500, "details": "精炼服务内部错误"}

    mock_ollama_call_log = []
    def mock_ollama_refinement_fails(prompt_content_sent, messages_history=None):
        call_number = len(mock_ollama_call_log)
        mock_ollama_call_log.append({
            "call_order": call_number,
            "prompt_content_sent": prompt_content_sent
        })
        if call_number == 0: # 生成 P1
            return expected_p1, None
        elif call_number == 1: # 生成 E1
            return expected_e1, None
        elif call_number == 2: # 尝试生成 P2，但失败
            return simulated_refinement_error_message, simulated_refinement_error_details
        else:
            pytest.fail(f"call_ollama_api被意外调用了 {call_number + 1} 次（精炼失败后不应再调用）")
            return "意外的API调用错误", {"type": "TestError", "details": "API调用次数超出预期"}
            
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_refinement_fails)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=True,
        max_recursion_depth=1, # 即使深度允许，也应在精炼失败时停止
        use_structured_template_name=None,
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"顶层不应有错误消息（内部警告会被记录），但得到: {results.get('error_message')}"
    
    assert len(mock_ollama_call_log) == 3, \
        f"call_ollama_api 应被调用3次（P1, E1, P2尝试），实际调用了 {len(mock_ollama_call_log)} 次"

    assert results.get("p1_initial_optimized_prompt") == expected_p1
    assert len(results.get("evaluation_reports", [])) == 1, "应有1份评估报告 (E1)"
    assert results.get("evaluation_reports")[0] == expected_e1
    
    # 根据 agent.py 逻辑，如果精炼失败，refined_prompts 应该为空，因为 break 在 append 之前
    assert len(results.get("refined_prompts", [])) == 0, "refined_prompts 列表应为空"
    assert results.get("final_prompt") == expected_p1, "最终提示应为 P1 (因为精炼失败)"

# 测试结构化模板加载失败时的回退行为
def test_generate_and_refine_prompt_structured_template_load_fails(monkeypatch):
    """
    测试当选择了结构化模板但 load_and_format_structured_prompt 失败时，
    函数是否回退到使用 CORE_META_PROMPT_TEMPLATE 并成功调用 call_ollama_api。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "一个请求，但其选择的结构化模板会加载失败。"
    task_type = "代码生成" # 假设这个类型通常会尝试结构化模板
    template_name_to_fail = "DetailedCodeFunction" # 假设这个模板会加载失败
    template_vars = {"programming_language": "Python", "function_name": "my_func"} # 提供变量

    expected_p1_from_core = "这是基于CORE_META_PROMPT的回退优化提示。"

    # 模拟 load_and_format_structured_prompt 使其返回 None
    mock_load_format_calls = []
    def mock_failing_load_format(tn, ur, tv):
        mock_load_format_calls.append({"template_name": tn, "user_request": ur, "variables": tv})
        assert tn == template_name_to_fail # 确保是针对我们期望失败的模板
        return None # 模拟加载/格式化失败
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', mock_failing_load_format)

    # 模拟 call_ollama_api，期望它接收到基于 CORE_META_PROMPT_TEMPLATE 的提示
    mock_ollama_calls = []
    def mock_ollama_receives_core_template(prompt_content_sent, messages_history=None):
        mock_ollama_calls.append({"prompt_content_sent": prompt_content_sent})
        # 验证发送的是否是回退后的核心模板内容
        expected_fallback_prompt = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
        assert prompt_content_sent == expected_fallback_prompt
        return expected_p1_from_core, None
    monkeypatch.setattr('meta_prompt_agent.core.agent.call_ollama_api', mock_ollama_receives_core_template)

    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False, # 关闭自我校正以简化测试
        max_recursion_depth=0,
        use_structured_template_name=template_name_to_fail, # 指定一个会加载失败的模板
        structured_template_vars=template_vars
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"不应有错误消息（内部模板加载失败会被处理），但得到: {results.get('error_message')}"
    
    # 验证 load_and_format_structured_prompt 被调用了
    assert len(mock_load_format_calls) == 1, "load_and_format_structured_prompt 应被调用1次"
    assert mock_load_format_calls[0]["template_name"] == template_name_to_fail
    
    # 验证 call_ollama_api 被调用了，并且接收的是回退后的提示
    assert len(mock_ollama_calls) == 1, "call_ollama_api 应被调用1次"
    
    # 验证 initial_core_prompt 是否是回退后的 CORE_META_PROMPT_TEMPLATE
    expected_initial_core_fallback = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
    assert results.get("initial_core_prompt") == expected_initial_core_fallback, \
        "initial_core_prompt 应为回退后的 CORE_META_PROMPT_TEMPLATE"
    
    assert results.get("p1_initial_optimized_prompt") == expected_p1_from_core
    assert results.get("final_prompt") == expected_p1_from_core

# 测试当 task_type 为 "图像生成" 且无结构化模板时，使用 BasicImageGen
def test_generate_and_refine_prompt_task_type_image_gen_fallback(monkeypatch):
    """
    测试当 task_type="图像生成" 且未选择结构化模板时，
    函数是否使用 STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"] 的核心模板。
    """
    # 1. 准备 (Arrange)
    user_raw_request = "一只在月球上戴着宇航员头盔的猫，数字艺术风格。"
    task_type = "图像生成"
    expected_p1_from_basic_image_gen = "这是由BasicImageGen优化后的图像提示。"

    # 确保 BasicImageGen 模板在 STRUCTURED_PROMPT_TEMPLATES 中存在且有 core_template_override
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

    # 确保 load_and_format_structured_prompt 不会被调用，因为我们没有提供模板名称
    mock_load_format_calls = []
    def mock_load_format_should_not_be_called(*args, **kwargs):
        mock_load_format_calls.append(True)
        pytest.fail("load_and_format_structured_prompt 不应在此场景下被调用")
    monkeypatch.setattr('meta_prompt_agent.core.agent.load_and_format_structured_prompt', mock_load_format_should_not_be_called)


    # 2. 执行 (Act)
    results = generate_and_refine_prompt(
        user_raw_request=user_raw_request,
        task_type=task_type,
        enable_self_correction=False,
        max_recursion_depth=0,
        use_structured_template_name=None, # 明确不使用特定结构化模板
        structured_template_vars=None
    )

    # 3. 断言 (Assert)
    assert results.get("error_message") is None, \
        f"不应有错误消息，但得到: {results.get('error_message')}"
    
    assert len(mock_load_format_calls) == 0, "load_and_format_structured_prompt 不应被调用"
    assert len(mock_ollama_calls) == 1, "call_ollama_api 应被调用1次"
    
    assert results.get("initial_core_prompt") == expected_initial_llm_prompt, \
        "initial_core_prompt 应为 BasicImageGen 的核心模板内容"
    
    assert results.get("p1_initial_optimized_prompt") == expected_p1_from_basic_image_gen
    assert results.get("final_prompt") == expected_p1_from_basic_image_gen