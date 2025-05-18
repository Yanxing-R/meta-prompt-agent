# src/meta_prompt_agent/core/agent.py
import logging
import requests
import json
import os
import google.generativeai as genai 
import dashscope 
from dashscope.api_entities.dashscope_response import Role 
from http import HTTPStatus 

from meta_prompt_agent.config import settings # 导入配置
from meta_prompt_agent.prompts.templates import (
    CORE_META_PROMPT_TEMPLATE,
    EVALUATION_META_PROMPT_TEMPLATE,
    REFINEMENT_META_PROMPT_TEMPLATE,
    STRUCTURED_PROMPT_TEMPLATES,
    EXPLAIN_TERM_TEMPLATE
)

logger = logging.getLogger(__name__)

# --- 通义千问 (Qwen) API 调用函数 (修正版) ---
def call_qwen_api(prompt_content: str, messages_history: list = None) -> tuple[str, dict | None]:
    """
    调用通义千问 (Qwen) API。
    """
    # 使用 settings.py 中定义的 QWEN_API_KEY_FROM_ENV
    loaded_api_key = settings.QWEN_API_KEY_FROM_ENV 

    if not loaded_api_key: # <--- 修改：使用 loaded_api_key (即 settings.QWEN_API_KEY_FROM_ENV)
        error_msg = "错误：通义千问 API 密钥 (DASHSCOPE_API_KEY 或 QWEN_API_KEY) 未在 .env 文件中配置。"
        logger.error(error_msg)
        return error_msg, {"type": "ConfigurationError", "details": "API key for Qwen is not set."}

    # 如果 .env 中设置的是 QWEN_API_KEY 而不是 DASHSCOPE_API_KEY, 
    # 并且 SDK 不会自动识别 QWEN_API_KEY, 我们可能需要显式设置。
    # 但如果 .env 中直接用了 DASHSCOPE_API_KEY, SDK 会自动处理。
    # 为了保险，如果 DASHSCOPE_API_KEY 环境变量不存在，我们尝试用 loaded_api_key 设置。
    if os.getenv('DASHSCOPE_API_KEY') is None and loaded_api_key:
        logger.info("DASHSCOPE_API_KEY 环境变量未设置，尝试使用 settings.QWEN_API_KEY_FROM_ENV 设置 dashscope.api_key。")
        dashscope.api_key = loaded_api_key
    # 注意：如果用户在.env中只设置了QWEN_API_KEY，而没有设置DASHSCOPE_API_KEY，
    # 并且dashscope.api_key = loaded_api_key 这一行由于某种原因没有正确生效或被SDK覆盖，
    # 那么SDK可能仍然找不到密钥。最稳妥的是在.env中使用DASHSCOPE_API_KEY。

    try:
        qwen_messages = []
        if messages_history:
            for msg in messages_history:
                role = msg.get("role")
                qwen_role = Role.USER 
                if role == "user": qwen_role = Role.USER
                elif role == "assistant": qwen_role = Role.ASSISTANT 
                elif role == "system": qwen_role = Role.SYSTEM
                else: logger.warning(f"未知的消息角色 '{role}'，默认为 'user'。")
                qwen_messages.append({'role': qwen_role, 'content': msg.get("content", "")})
        
        qwen_messages.append({'role': Role.USER, 'content': prompt_content})

        logger.debug(f"向通义千问 API ({settings.QWEN_MODEL_NAME}) 发送请求。最后提示: {prompt_content[:100]}...")
        
        response = dashscope.Generation.call(
            model=settings.QWEN_MODEL_NAME,
            messages=qwen_messages,
            result_format='message', 
        )

        if response.status_code == HTTPStatus.OK:
            if response.output and response.output.choices and response.output.choices[0].message and response.output.choices[0].message.content:
                generated_text = response.output.choices[0].message.content
                logger.info(f"成功从通义千问 API ({settings.QWEN_MODEL_NAME}) 获取响应。")
                cleaned_content = clean_llm_output(generated_text)
                return cleaned_content, None
            else:
                error_msg = "通义千问 API响应格式不符合预期（缺少output、choices或content）。"
                logger.warning(f"{error_msg} 响应: {response}")
                return f"错误：{error_msg}", {"type": "QwenFormatError", "details": str(response)}
        else:
            error_msg = (
                f"通义千问 API 调用失败。状态码: {response.status_code}。"
                f"请求ID: {response.request_id if hasattr(response, 'request_id') else 'N/A'}。"
                f"错误代码: {response.code if hasattr(response, 'code') else 'N/A'}。"
                f"错误消息: {response.message if hasattr(response, 'message') else 'N/A'}"
            )
            logger.error(error_msg)
            return f"错误：{error_msg}", {
                "type": "QwenAPIError", 
                "status_code": response.status_code,
                "request_id": response.request_id if hasattr(response, 'request_id') else None,
                "error_code": response.code if hasattr(response, 'code') else None,
                "error_message_from_api": response.message if hasattr(response, 'message') else None,
                "raw_response": str(response) 
            }

    except Exception as e:
        error_msg = f"调用通义千问 API ({settings.QWEN_MODEL_NAME}) 时发生SDK或未知错误: {type(e).__name__} - {e}"
        logger.exception(error_msg)
        return f"错误：{error_msg}", {"type": "QwenSDKError", "exception_type": type(e).__name__, "details": str(e)}

# --- Gemini API 调用函数 (保持不变) ---
def call_gemini_api(prompt_content: str, messages_history: list = None) -> tuple[str, dict | None]:
    # ... (您现有的 call_gemini_api 代码) ...
    if not settings.GEMINI_API_KEY:
        error_msg = "错误：Gemini API 密钥未配置。"
        logger.error(error_msg)
        return error_msg, {"type": "ConfigurationError", "details": "GEMINI_API_KEY is not set."}
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        contents_for_gemini = []
        if messages_history:
            for msg in messages_history:
                gemini_role = "user" if msg.get("role") == "user" else "model"
                contents_for_gemini.append({"role": gemini_role, "parts": [msg.get("content", "")]})
        contents_for_gemini.append({"role": "user", "parts": [prompt_content]})
        
        logger.debug(f"向 Gemini API ({settings.GEMINI_MODEL_NAME}) 发送请求。最后提示: {prompt_content[:100]}...")
        response = model.generate_content(contents_for_gemini)

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            generated_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            logger.info(f"成功从 Gemini API ({settings.GEMINI_MODEL_NAME}) 获取响应。")
            return generated_text.strip(), None
        else:
            block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "未知"
            safety_ratings_str = str(response.prompt_feedback.safety_ratings) if response.prompt_feedback else "无"
            error_msg = f"Gemini API 未返回有效内容。可能原因: 内容被安全过滤器阻止 (原因: {block_reason}). 安全评级: {safety_ratings_str}"
            logger.warning(error_msg)
            return f"错误：{error_msg}", {"type": "GeminiContentError", "block_reason": str(block_reason), "safety_ratings": safety_ratings_str, "raw_response": str(response)}
    except Exception as e:
        error_msg = f"调用 Gemini API ({settings.GEMINI_MODEL_NAME}) 时发生错误: {type(e).__name__} - {e}"
        logger.exception(error_msg) 
        return f"错误：{error_msg}", {"type": "GeminiAPIError", "exception_type": type(e).__name__, "details": str(e)}

# --- Ollama API 调用函数 (保持不变) ---
def call_ollama_api(prompt_content: str, messages_history: list = None) -> tuple[str, dict | None]:
    # ... (您现有的 call_ollama_api 代码) ...
    current_messages = []
    if messages_history:
        current_messages.extend(messages_history)
    current_messages.append({"role": "user", "content": prompt_content})
    payload = {
        "model": settings.OLLAMA_MODEL, "messages": current_messages, "stream": False
    }
    headers = {"Content-Type": "application/json"}
    error_msg_prefix = "错误："
    try:
        logger.debug(f"向 Ollama API ({settings.OLLAMA_API_URL}) 发送请求。模型: {settings.OLLAMA_MODEL}")
        response = requests.post(
            settings.OLLAMA_API_URL, headers=headers, data=json.dumps(payload), timeout=180
        )
        response.raise_for_status()
        response_data = response.json()
        if "message" in response_data and "content" in response_data["message"]:
            logger.info("成功从 Ollama API 获取响应。")
            raw_content = response_data["message"]["content"]
            cleaned_content = clean_llm_output(raw_content) 
            return cleaned_content, None
        else:
            error_msg = "Ollama API响应格式不符合预期"
            logger.warning(f"{error_msg}。响应数据: {response_data}")
            return f"{error_msg_prefix}{error_msg}", {"type": "FormatError", "details": response_data}
    except requests.exceptions.ConnectionError as e: 
        error_msg = f"无法连接到Ollama服务: {settings.OLLAMA_API_URL}"
        logger.error(f"{error_msg}. 详细错误: {e}", exc_info=True)
        return f"{error_msg_prefix}{error_msg}", {"type": "ConnectionError", "url": settings.OLLAMA_API_URL, "details": str(e)}
    except requests.exceptions.Timeout as e: 
        error_msg = f"请求Ollama API超时 ({settings.OLLAMA_API_URL})"
        logger.error(f"{error_msg}. 详细错误: {e}", exc_info=True)
        return f"{error_msg_prefix}{error_msg}", {"type": "TimeoutError", "url": settings.OLLAMA_API_URL, "details": str(e)}
    except requests.exceptions.HTTPError as e: 
        error_text_detail = f"Ollama API交互失败 (HTTP {e.response.status_code})"
        logger.error(f"{error_text_detail}. URL: {e.request.url if e.request else 'N/A'}. 响应内容: {e.response.text}", exc_info=True)
        details = {"type": "HTTPError", "status_code": e.response.status_code, "raw_response": e.response.text}
        error_text_for_user = error_text_detail
        try:
            error_details_json = e.response.json()
            if "error" in error_details_json:
                error_text_for_user += f". Ollama错误: {error_details_json['error']}"
                details["ollama_error"] = error_details_json['error']
        except json.JSONDecodeError:
            logger.warning("解析HTTPError的响应体为JSON时失败。")
            pass
        return f"{error_msg_prefix}{error_text_for_user}", details
    except json.JSONDecodeError as e: 
        error_msg = "解析Ollama API响应为JSON时失败"
        raw_response_text = "未知"
        if 'response' in locals() and hasattr(response, 'text'): 
            raw_response_text = response.text[:500]  
        logger.error(f"{error_msg}. 详细错误: {e}. 部分原始响应: {raw_response_text}", exc_info=True)
        return f"{error_msg_prefix}{error_msg}", {"type": "JSONDecodeError", "details": str(e), "raw_response_snippet": raw_response_text}
    except Exception as e: 
        error_msg = "调用Ollama API时发生未知内部错误" 
        logger.exception(f"调用Ollama API时发生未知错误。原始错误: {e}") 
        return f"{error_msg_prefix}{error_msg}", {"type": "UnknownError", "exception_type": e.__class__.__name__, "details": "详情请查看应用日志"}


# --- 通用 LLM 调用接口 (更新) ---
def invoke_llm(prompt_content: str, messages_history: list = None) -> tuple[str, dict | None]:
    """
    根据 ACTIVE_LLM_PROVIDER 配置调用相应的LLM API。
    """
    provider = settings.ACTIVE_LLM_PROVIDER
    logger.info(f"使用 LLM 服务提供者: {provider} (模型: {settings.QWEN_MODEL_NAME if provider == 'qwen' else (settings.GEMINI_MODEL_NAME if provider == 'gemini' else settings.OLLAMA_MODEL)})")

    if provider == "gemini":
        return call_gemini_api(prompt_content, messages_history)
    elif provider == "ollama":
        return call_ollama_api(prompt_content, messages_history)
    elif provider == "qwen": # 2. 添加对 qwen 的处理
        return call_qwen_api(prompt_content, messages_history)
    else:
        error_msg = f"错误：未知的LLM服务提供者配置 '{provider}'。"
        logger.error(error_msg)
        return error_msg, {"type": "ConfigurationError", "details": f"ACTIVE_LLM_PROVIDER '{provider}' 不被支持。"}

# --- 辅助函数 (如 clean_llm_output, load_and_format_structured_prompt 保持不变) ---
# ... (clean_llm_output, load_and_format_structured_prompt, generate_and_refine_prompt, explain_term_in_prompt, load_feedback, save_feedback 函数定义) ...
# 注意：generate_and_refine_prompt 和 explain_term_in_prompt 内部调用 invoke_llm 的逻辑不需要改变。
def clean_llm_output(text: str) -> str:
    opening_marker = "<<think>>"
    closing_marker = "<</think>>" 
    last_closing_marker_index = text.rfind(closing_marker)
    if last_closing_marker_index != -1:
        content_after_last_closing = text[last_closing_marker_index + len(closing_marker):].strip()
        logger.debug(f"找到闭合思考标记 '{closing_marker}'，提取其后内容。")
        return content_after_last_closing
    else:
        first_opening_marker_index = text.find(opening_marker)
        if first_opening_marker_index != -1:
            logger.warning(
                f"在LLM输出中找到起始思考标记 '{opening_marker}' 但未找到对应的闭合标记 '{closing_marker}'。"
            )
            return text 
        else:
            logger.debug("未在LLM输出中找到思考标记，返回原始文本。")
            return text.strip()

def load_and_format_structured_prompt(template_name: str, user_request: str, variables: dict | None) -> str | None:
    if not isinstance(STRUCTURED_PROMPT_TEMPLATES, dict):
        logger.critical(
            f"STRUCTURED_PROMPT_TEMPLATES 不是一个字典 (实际类型: {type(STRUCTURED_PROMPT_TEMPLATES)}). "
        )
        return None 
    logger.debug(f"尝试加载并格式化结构化模板: '{template_name}'，用户请求: '{user_request[:50]}...', 变量: {variables}")
    if template_name not in STRUCTURED_PROMPT_TEMPLATES:
        logger.warning(f"未找到名为 '{template_name}' 的结构化提示模板。可用模板: {list(STRUCTURED_PROMPT_TEMPLATES.keys())}")
        return None
    template_data = STRUCTURED_PROMPT_TEMPLATES[template_name]
    if not isinstance(template_data, dict):
        logger.error(f"模板 '{template_name}' 的数据格式不正确，期望是一个字典，实际是 {type(template_data)}。")
        return None
    required_vars = template_data.get("variables", [])
    if not isinstance(required_vars, list): 
        logger.error(f"模板 '{template_name}' 中的 'variables' 属性不是一个列表，实际是 {type(required_vars)}。")
        required_vars = [] 
    if required_vars:
        actual_vars = variables if variables is not None else {}
        missing_vars = [
            var for var in required_vars
            if var not in actual_vars or not str(actual_vars.get(var, "")).strip()
        ]
        if missing_vars:
            logger.warning(
                f"结构化提示模板 '{template_name}' 需要以下变量的值，但未提供或为空: {', '.join(missing_vars)}。"
                f"提供的变量键: {list(actual_vars.keys())}"
            )
            return None
    try:
        format_vars = variables.copy() if variables is not None else {}
        format_vars['user_raw_request'] = user_request 
        core_template_str = template_data.get("core_template_override")
        if not isinstance(core_template_str, str): 
            logger.error(f"模板 '{template_name}' 中的 'core_template_override' 不是一个字符串或未定义。")
            return None
        final_prompt_content = core_template_str.format(**format_vars)
        logger.info(f"成功格式化结构化模板 '{template_name}'。")
        return final_prompt_content
    except KeyError as e:
        logger.error(
            f"格式化结构化提示模板 '{template_name}' 时缺少预期的变量占位符: '{e}'. ", exc_info=True
        )
        return None
    except Exception as e:
        logger.exception(f"格式化结构化提示模板 '{template_name}' 时发生未知错误。")
        return None

def generate_and_refine_prompt(
    user_raw_request: str, task_type: str, enable_self_correction: bool,
    max_recursion_depth: int, use_structured_template_name: str = None,
    structured_template_vars: dict = None
) -> dict:
    try:
        results = {
            "initial_core_prompt": "", "p1_initial_optimized_prompt": "",
            "evaluation_reports": [], "refined_prompts": [], "final_prompt": "",
            "error_message": None, "error_details": None,
        }
        logger.info(f"开始处理任务类型 '{task_type}' 的请求: '{user_raw_request[:50]}...' (提供者: {settings.ACTIVE_LLM_PROVIDER})")
        initial_core_prompt_for_llm = ""
        if use_structured_template_name and structured_template_vars:
            formatted_prompt_from_structure = load_and_format_structured_prompt(
                use_structured_template_name, user_raw_request, structured_template_vars
            )
            if formatted_prompt_from_structure:
                initial_core_prompt_for_llm = formatted_prompt_from_structure
            else: 
                logger.warning(f"结构化模板 '{use_structured_template_name}' 处理失败，回退。")
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
        else:
            if task_type == "图像生成" and "BasicImageGen" in STRUCTURED_PROMPT_TEMPLATES:
                 initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(user_raw_request=user_raw_request)
            elif task_type == "代码生成" and "BasicCodeSnippet" in STRUCTURED_PROMPT_TEMPLATES:
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
            else:
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
        results["initial_core_prompt"] = initial_core_prompt_for_llm
        conversation_history = []
        p1, error = invoke_llm(initial_core_prompt_for_llm, None)
        if error:
            error_msg_for_results = f"生成初始优化提示失败: {p1}"
            logger.error(f"调用LLM生成初始提示失败。API返回: {p1}, 错误详情: {error}")
            results["error_message"] = error_msg_for_results
            results["error_details"] = error
            return results
        results["p1_initial_optimized_prompt"] = p1
        conversation_history.append({"role": "user", "content": str(initial_core_prompt_for_llm)})
        conversation_history.append({"role": "assistant", "content": str(p1)})
        current_best_prompt = p1
        logger.info(f"初步优化后的提示词 (P1):\n{current_best_prompt}")
        if not enable_self_correction:
            results["final_prompt"] = current_best_prompt
            return results
        for i in range(max_recursion_depth):
            logger.info(f"开始第 {i+1} 轮自我校正...")
            eval_prompt_content = EVALUATION_META_PROMPT_TEMPLATE.format(
                user_raw_request=user_raw_request, prompt_to_evaluate=current_best_prompt
            )
            evaluation_report_str, error = invoke_llm(eval_prompt_content, []) 
            if error:
                logger.warning(f"第 {i+1} 轮自我校正：生成评估报告失败。API返回: {evaluation_report_str}, 错误详情: {error}")
                break
            logger.info(f"原始评估报告字符串 (E{i+1}):\n{evaluation_report_str}")
            parsed_evaluation_report = None
            try:
                cleaned_report_str = evaluation_report_str.strip()
                if cleaned_report_str.startswith("```json"): cleaned_report_str = cleaned_report_str[7:]
                if cleaned_report_str.endswith("```"): cleaned_report_str = cleaned_report_str[:-3]
                cleaned_report_str = cleaned_report_str.strip()
                parsed_evaluation_report = json.loads(cleaned_report_str)
                results["evaluation_reports"].append(parsed_evaluation_report)
                logger.info(f"成功解析评估报告 (E{i+1}) 为JSON。")
            except json.JSONDecodeError as json_e:
                logger.warning(f"无法将评估报告 (E{i+1}) 解析为JSON。错误: {json_e}. 使用原始字符串。")
                results["evaluation_reports"].append(evaluation_report_str)
            conversation_history.append({"role": "user", "content": str(eval_prompt_content)})
            conversation_history.append({"role": "assistant", "content": str(evaluation_report_str)})
            refinement_prompt_content = REFINEMENT_META_PROMPT_TEMPLATE.format(
                user_raw_request=user_raw_request,
                previous_prompt=current_best_prompt,
                evaluation_report=evaluation_report_str 
            )
            refined_prompt, error = invoke_llm(refinement_prompt_content, conversation_history)
            if error:
                logger.warning(f"第 {i+1} 轮自我校正：生成精炼提示失败。API返回: {refined_prompt}, 错误详情: {error}")
                break
            logger.info(f"第 {i+1} 轮精炼后的提示词 (P{i+2}):\n{refined_prompt}")
            results["refined_prompts"].append(refined_prompt)
            if refined_prompt.strip() == current_best_prompt.strip():
                 logger.info("精炼后的提示与上一版相同，停止递归。")
                 break
            current_best_prompt = refined_prompt
            conversation_history.append({"role": "user", "content": str(refinement_prompt_content)})
            conversation_history.append({"role": "assistant", "content": str(refined_prompt)})
        results["final_prompt"] = current_best_prompt
        logger.info(f"成功生成最终提示。请求: '{user_raw_request[:50]}...'")
        return results
    except Exception as e: 
        logger.exception(f"在 generate_and_refine_prompt 处理过程中发生未捕获的严重错误。请求: '{user_raw_request[:50]}...'")
        return {
            "initial_core_prompt": "", "p1_initial_optimized_prompt": "",
            "evaluation_reports": [], "refined_prompts": [], "final_prompt": "",
            "error_message": "处理请求时发生内部错误，请稍后再试或联系管理员。",
            "error_details": {"type": "UnhandledException", "exception_type": e.__class__.__name__, "message": str(e)},
        }

def explain_term_in_prompt(term_to_explain: str, context_prompt: str) -> tuple[str, dict | None]:
    if not term_to_explain or not term_to_explain.strip():
        logger.warning("explain_term_in_prompt: 'term_to_explain' 参数为空。")
        return "错误：需要提供要解释的术语。", {"type": "InputValidationError", "details": "待解释术语不能为空。"}
    if not context_prompt or not context_prompt.strip():
        logger.warning("explain_term_in_prompt: 'context_prompt' 参数为空。")
        return "错误：需要提供术语所在的上下文提示。", {"type": "InputValidationError", "details": "上下文提示不能为空。"}
    try:
        explanation_request_prompt = EXPLAIN_TERM_TEMPLATE.format(
            term_to_explain=term_to_explain,
            context_prompt=context_prompt
        )
        logger.info(f"为术语 '{term_to_explain}' 生成解释请求 (提供者: {settings.ACTIVE_LLM_PROVIDER})...")
        explanation_text, error_details = invoke_llm(explanation_request_prompt) # 使用 invoke_llm
        if error_details:
            logger.error(f"调用LLM解释术语 '{term_to_explain}' 时失败。API返回: {explanation_text}, 错误详情: {error_details}")
            return explanation_text, error_details
        logger.info(f"成功获取术语 '{term_to_explain}' 的解释。")
        return explanation_text.strip(), None
    except KeyError as e:
        logger.exception(f"格式化 EXPLAIN_TERM_TEMPLATE 时发生 KeyError: {e}.")
        return "错误：解释模板格式化失败。", {"type": "TemplateFormatError", "details": str(e)}
    except Exception as e:
        logger.exception(f"解释术语 '{term_to_explain}' 时发生未知错误。")
        return "错误：解释过程中发生未知内部错误。", {"type": "UnknownExplanationError", "details": str(e)}

def load_feedback() -> list:
    # ... (保持不变) ...
    if not os.path.exists(settings.FEEDBACK_FILE):
        logger.info(f"反馈文件 '{settings.FEEDBACK_FILE}' 不存在，将返回空列表。")
        return []
    try:
        with open(settings.FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            feedback_data = json.load(f)
            logger.info(f"成功从 '{settings.FEEDBACK_FILE}' 加载反馈数据。")
            return feedback_data
    except json.JSONDecodeError as e:
        logger.error(f"解析反馈文件 '{settings.FEEDBACK_FILE}' 时发生JSON解码错误: {e}", exc_info=True)
        return [] 
    except IOError as e:
        logger.error(f"读取反馈文件 '{settings.FEEDBACK_FILE}' 时发生IO错误: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.exception(f"加载反馈文件 '{settings.FEEDBACK_FILE}' 时发生未知错误。")
        return []

def save_feedback(all_feedback_data: list) -> bool:
    # ... (保持不变) ...
    try:
        with open(settings.FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_feedback_data, f, ensure_ascii=False, indent=4)
        logger.info(f"反馈数据已成功保存到 '{settings.FEEDBACK_FILE}'。")
        return True
    except IOError as e:
        logger.error(f"保存反馈数据到 '{settings.FEEDBACK_FILE}' 时发生IO错误: {e}", exc_info=True)
        return False
    except TypeError as e: 
        logger.error(f"序列化反馈数据到 '{settings.FEEDBACK_FILE}' 时发生类型错误: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.exception(f"保存反馈数据到 '{settings.FEEDBACK_FILE}' 时发生未知错误。")
        return False
