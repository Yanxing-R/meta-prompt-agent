# src/meta_prompt_agent/core/agent.py
import logging
import json
import os

from meta_prompt_agent.config import settings # 导入配置
from meta_prompt_agent.config.settings import get_settings # 导入get_settings函数
from meta_prompt_agent.prompts.templates import (
    CORE_META_PROMPT_TEMPLATE,
    EVALUATION_META_PROMPT_TEMPLATE,
    REFINEMENT_META_PROMPT_TEMPLATE,
    STRUCTURED_PROMPT_TEMPLATES,
    EXPLAIN_TERM_TEMPLATE
)
from meta_prompt_agent.core.llm import LLMClientFactory # 导入LLM工厂

logger = logging.getLogger(__name__)

# --- 统一的LLM调用接口 ---
async def invoke_llm(prompt_content: str, messages_history: list = None, model_override: str = None, provider_override: str = None) -> tuple[str, dict | None]:
    """
    使用LLM抽象层调用当前活跃的语言模型。
    
    Args:
        prompt_content (str): 提示内容
        messages_history (list, optional): 对话历史记录
        model_override (str, optional): 覆盖默认模型的指定模型名称
        provider_override (str, optional): 覆盖默认提供商的指定提供商名称
        
    Returns:
        tuple[str, dict | None]: (生成的文本, 错误信息)
    """
    try:
        # 获取配置
        settings_dict = get_settings()
        
        # 确定使用的提供商
        provider = provider_override if provider_override else settings_dict["ACTIVE_LLM_PROVIDER"]
        
        logger.info(f"尝试使用提供商 '{provider}' {f'和模型 {model_override}' if model_override else ''} 生成响应...")
        
        # 获取当前活跃的LLM客户端（根据provider_override可能使用不同的提供商）
        llm_client = LLMClientFactory.create(provider, model_override)
        
        # 确认使用的模型名称（在日志中记录）
        model_name = model_override if model_override else llm_client.model_name
        
        logger.info(f"使用 LLM 服务提供者: {provider} (模型: {model_name})")
        
        # 如果有对话历史，构建消息格式
        kwargs = {}
        if messages_history:
            # 注意：这里我们将传递历史消息，不同LLM客户端实现将负责处理适当的格式转换
            kwargs["messages_history"] = messages_history
            
        # 如果有模型覆盖，添加到kwargs
        if model_override:
            kwargs["model_override"] = model_override
            logger.info(f"使用模型覆盖: {model_override}")
        
        # 调用LLM生成文本
        response_text, metadata = await llm_client.generate_with_metadata(prompt_content, **kwargs)
        
        # 处理生成的文本
        cleaned_response = clean_llm_output(response_text)
        logger.info(f"成功从 {provider} ({model_name}) 获取响应。")
        
        return cleaned_response, None
        
    except ValueError as e:
        error_msg = f"错误：LLM配置或请求无效: {str(e)}"
        logger.error(error_msg)
        return error_msg, {"type": "ConfigurationError", "details": str(e)}
        
    except Exception as e:
        error_msg = f"错误：调用 {provider_override or settings_dict['ACTIVE_LLM_PROVIDER']} 时发生未知错误: {type(e).__name__} - {str(e)}"
        logger.exception(error_msg)
        return error_msg, {"type": "LLMError", "exception_type": type(e).__name__, "details": str(e)}

# --- 辅助函数 ---
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

async def generate_and_refine_prompt(
    user_raw_request: str, task_type: str, enable_self_correction: bool,
    max_recursion_depth: int, use_structured_template_name: str = None,
    structured_template_vars: dict = None, model_override: str = None,
    provider_override: str = None
) -> dict:
    try:
        results = {
            "initial_core_prompt": "", "p1_initial_optimized_prompt": "",
            "evaluation_reports": [], "refined_prompts": [], "final_prompt": "",
            "error_message": None, "error_details": None,
        }
        logger.info(f"开始处理任务类型 '{task_type}' 的请求: '{user_raw_request[:50]}...' (提供者: {provider_override or settings.ACTIVE_LLM_PROVIDER}, 模型: {model_override or '默认'})")
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
            elif task_type == "视频生成" and "BasicVideoGen" in STRUCTURED_PROMPT_TEMPLATES:
                initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicVideoGen"]["core_template_override"].format(user_raw_request=user_raw_request)
            else:
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
        results["initial_core_prompt"] = initial_core_prompt_for_llm
        conversation_history = []
        p1, error = await invoke_llm(initial_core_prompt_for_llm, None, model_override, provider_override)
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
            evaluation_report_str, error = await invoke_llm(eval_prompt_content, [], model_override, provider_override) 
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
            refined_prompt, error = await invoke_llm(refinement_prompt_content, conversation_history, model_override, provider_override)
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

async def explain_term_in_prompt(term_to_explain: str, context_prompt: str, model_override: str = None, provider_override: str = None) -> tuple[str, dict | None]:
    """解释提示词中的特定术语"""
    logger.info(f"解释术语 '{term_to_explain}' (在长度为 {len(context_prompt)} 的上下文中), 模型: {model_override or '默认'}, 提供商: {provider_override or '默认'}")
    
    if not term_to_explain or not term_to_explain.strip():
        err_msg = "错误：要解释的术语不能为空。"
        logger.warning(err_msg)
        return err_msg, {"type": "InputValidationError", "details": "术语不能为空"}
        
    if not context_prompt or not context_prompt.strip():
        err_msg = "错误：需要提供上下文才能解释术语。"
        logger.warning(err_msg)
        return err_msg, {"type": "InputValidationError", "details": "上下文不能为空"}
    
    explanation_prompt = EXPLAIN_TERM_TEMPLATE.format(
        term_to_explain=term_to_explain,
        context=context_prompt
    )
    
    explanation, error = await invoke_llm(explanation_prompt, None, model_override, provider_override)
    
    if error:
        err_msg = f"错误：解释术语时发生问题: {explanation}"
        logger.error(f"调用LLM解释术语失败，返回的错误: {explanation}")
        return err_msg, error
    
    logger.info(f"成功获取术语 '{term_to_explain}' 的解释")
    return explanation, None

def load_feedback() -> list:
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
