# src/meta_prompt_agent/core/agent.py
import logging
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union

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
from meta_prompt_agent.core.session_manager import (
    get_session_manager, 
    PromptSession, 
    SessionStage
)

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
    """
    生成并优化提示词的单一API，向后兼容原有功能
    
    将使用分步交互式功能自动完成整个生成过程
    """
    try:
        results = {
            "initial_core_prompt": "", "p1_initial_optimized_prompt": "",
            "evaluation_reports": [], "refined_prompts": [], "final_prompt": "",
            "error_message": None, "error_details": None,
        }
        
        logger.info(f"开始处理任务类型 '{task_type}' 的请求: '{user_raw_request[:50]}...' (提供者: {provider_override or settings.ACTIVE_LLM_PROVIDER}, 模型: {model_override or '默认'})")
        
        # 创建交互式会话
        session, error = await create_interactive_session(
            user_raw_request=user_raw_request,
            task_type=task_type,
            model_override=model_override,
            provider_override=provider_override,
            template_name=use_structured_template_name,
            template_variables=structured_template_vars,
            max_recursion_depth=max_recursion_depth
        )
        
        if error:
            logger.error(f"创建交互式会话失败: {error}")
            results["error_message"] = f"创建交互式会话失败: {error.get('message', '')}"
            results["error_details"] = error
            return results
        
        # 生成P1提示词
        session, error = await generate_p1_prompt_for_session(session.session_id)
        if error:
            logger.error(f"生成P1提示词失败: {error}")
            results["error_message"] = f"生成P1提示词失败: {error.get('message', '')}"
            results["error_details"] = error
            return results
        
        # 填充初始结果
        results["initial_core_prompt"] = session.initial_core_prompt
        results["p1_initial_optimized_prompt"] = session.p1_prompt
        
        # 如果不需要自我校正，直接返回结果
        if not enable_self_correction:
            results["final_prompt"] = session.p1_prompt
            return results
        
        # 执行自我校正循环
        for i in range(max_recursion_depth):
            # 评估当前提示词
            session, error = await evaluate_prompt_for_session(session.session_id)
            if error and error.get("type") != "InvalidStage":
                logger.warning(f"第 {i+1} 轮自我校正：评估提示词失败: {error}")
                break
            
            # 添加评估报告到结果
            if session.evaluation_reports and i < len(session.evaluation_reports):
                results["evaluation_reports"].append(session.evaluation_reports[i])
            
            # 优化当前提示词
            session, error = await refine_prompt_for_session(session.session_id)
            if error and error.get("type") not in ["InvalidStage", "MaxDepthReached"]:
                logger.warning(f"第 {i+1} 轮自我校正：优化提示词失败: {error}")
                break
            
            # 如果会话已完成，说明优化停止
            if session.stage == SessionStage.COMPLETED:
                logger.info(f"第 {i+1} 轮自我校正后优化完成")
                break
            
            # 添加优化提示词到结果
            if session.refined_prompts and i < len(session.refined_prompts):
                results["refined_prompts"].append(session.refined_prompts[i])
        
        # 完成会话
        session, error = await complete_session(session.session_id)
        if error:
            logger.warning(f"完成会话失败: {error}")
        
        # 设置最终提示词
        results["final_prompt"] = session.final_prompt or session.current_prompt or session.p1_prompt
        
        logger.info(f"成功生成最终提示。请求: '{user_raw_request[:50]}...'")
        return results
    
    except Exception as e: 
        logger.exception(f"在 generate_and_refine_prompt 处理过程中发生未捕获的严重错误。请求: '{user_raw_request[:50]}...'")
        return {
            "initial_core_prompt": "", "p1_initial_optimized_prompt": "",
            "evaluation_reports": [], "refined_prompts": [], "final_prompt": "",
            "error_message": f"未捕获的严重错误: {str(e)}",
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

# --- 分步交互式提示词生成函数 ---
async def create_interactive_session(
    user_raw_request: str, 
    task_type: str,
    model_override: str = None, 
    provider_override: str = None,
    template_name: str = None,
    template_variables: Dict[str, Any] = None,
    max_recursion_depth: int = 3
) -> Tuple[PromptSession, Optional[Dict[str, Any]]]:
    """
    创建交互式提示词生成会话
    
    Args:
        user_raw_request: 用户原始请求
        task_type: 任务类型
        model_override: 可选的模型覆盖
        provider_override: 可选的提供商覆盖
        template_name: 结构化模板名称
        template_variables: 模板变量
        max_recursion_depth: 最大递归深度
        
    Returns:
        Tuple[PromptSession, Optional[Dict[str, Any]]]: (会话对象, 错误信息)
    """
    try:
        # 获取会话管理器
        session_manager = get_session_manager()
        
        # 创建新会话
        session = await session_manager.create_session(
            user_raw_request=user_raw_request,
            task_type=task_type,
            model_override=model_override,
            provider_override=provider_override,
            template_name=template_name,
            template_variables=template_variables
        )
        
        # 设置最大递归深度
        session.max_recursion_depth = max_recursion_depth
        
        # 保存会话
        await session_manager.save_session(session)
        
        logger.info(f"成功创建交互式会话 {session.session_id}")
        return session, None
    except Exception as e:
        error_msg = f"创建交互式会话失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, {"type": "SessionCreationError", "message": error_msg}

async def generate_p1_prompt_for_session(session_id: str) -> Tuple[PromptSession, Optional[Dict[str, Any]]]:
    """
    为指定会话生成初步提示词 (P1)
    
    Args:
        session_id: 会话ID
        
    Returns:
        Tuple[PromptSession, Optional[Dict[str, Any]]]: (会话对象, 错误信息)
    """
    # 获取会话管理器和会话对象
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        error_msg = f"会话 {session_id} 不存在"
        logger.error(error_msg)
        return None, {"type": "SessionNotFound", "message": error_msg}
    
    # 检查会话状态
    if session.stage != SessionStage.CREATED:
        error_msg = f"会话 {session_id} 已经生成过P1提示词，当前阶段: {session.stage}"
        logger.warning(error_msg)
        return session, {"type": "InvalidStage", "message": error_msg}
    
    try:
        # 准备初始核心提示
        initial_core_prompt_for_llm = ""
        
        # 使用结构化模板（如果指定）
        if session.template_name and session.template_variables:
            formatted_prompt_from_structure = load_and_format_structured_prompt(
                session.template_name, session.user_raw_request, session.template_variables
            )
            if formatted_prompt_from_structure:
                initial_core_prompt_for_llm = formatted_prompt_from_structure
            else: 
                logger.warning(f"结构化模板 '{session.template_name}' 处理失败，回退。")
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=session.user_raw_request)
        else:
            # 根据任务类型选择不同的模板
            if session.task_type == "图像生成" and "BasicImageGen" in STRUCTURED_PROMPT_TEMPLATES:
                initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(user_raw_request=session.user_raw_request)
            elif session.task_type == "代码生成" and "BasicCodeSnippet" in STRUCTURED_PROMPT_TEMPLATES:
                initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicCodeSnippet"]["core_template_override"].format(user_raw_request=session.user_raw_request)
            elif session.task_type == "视频生成" and "BasicVideoGen" in STRUCTURED_PROMPT_TEMPLATES:
                initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicVideoGen"]["core_template_override"].format(user_raw_request=session.user_raw_request)
            else:
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=session.user_raw_request)
        
        # 保存初始核心提示
        session.initial_core_prompt = initial_core_prompt_for_llm
        
        # 调用LLM生成P1提示词
        p1, error = await invoke_llm(
            initial_core_prompt_for_llm, 
            None, 
            session.model_override, 
            session.provider_override
        )
        
        if error:
            session.record_error(f"生成初始优化提示失败: {p1}")
            session.increment_retry("p1_generation")
            await session_manager.save_session(session)
            return session, {"type": "LLMError", "message": f"调用LLM生成初始提示失败: {p1}", "details": error}
        
        # 更新会话状态
        session.p1_prompt = p1
        session.current_prompt = p1
        session.stage = SessionStage.P1_GENERATED
        
        # 添加到对话历史
        session.add_to_history("user", initial_core_prompt_for_llm)
        session.add_to_history("assistant", p1)
        
        # 保存会话
        await session_manager.save_session(session)
        
        logger.info(f"会话 {session_id} 成功生成P1提示词")
        return session, None
    
    except Exception as e:
        error_msg = f"生成P1提示词失败: {str(e)}"
        session.record_error(error_msg)
        session.increment_retry("p1_generation")
        await session_manager.save_session(session)
        logger.error(error_msg, exc_info=True)
        return session, {"type": "UnexpectedError", "message": error_msg}

async def evaluate_prompt_for_session(session_id: str) -> Tuple[PromptSession, Optional[Dict[str, Any]]]:
    """
    为指定会话评估当前提示词
    
    Args:
        session_id: 会话ID
        
    Returns:
        Tuple[PromptSession, Optional[Dict[str, Any]]]: (会话对象, 错误信息)
    """
    # 获取会话管理器和会话对象
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        error_msg = f"会话 {session_id} 不存在"
        logger.error(error_msg)
        return None, {"type": "SessionNotFound", "message": error_msg}
    
    # 检查会话状态
    valid_stages = [SessionStage.P1_GENERATED, SessionStage.REFINEMENT_COMPLETE]
    if session.stage not in valid_stages:
        error_msg = f"会话 {session_id} 当前阶段({session.stage})不允许进行评估，需要处于以下阶段之一: {valid_stages}"
        logger.warning(error_msg)
        return session, {"type": "InvalidStage", "message": error_msg}
    
    if not session.current_prompt:
        error_msg = f"会话 {session_id} 没有可评估的当前提示词"
        logger.error(error_msg)
        return session, {"type": "MissingPrompt", "message": error_msg}
    
    try:
        # 构建评估提示
        eval_prompt_content = EVALUATION_META_PROMPT_TEMPLATE.format(
            user_raw_request=session.user_raw_request, 
            prompt_to_evaluate=session.current_prompt
        )
        
        # 调用LLM获取评估报告
        evaluation_report_str, error = await invoke_llm(
            eval_prompt_content, 
            session.conversation_history, 
            session.model_override, 
            session.provider_override
        )
        
        if error:
            session.record_error(f"生成评估报告失败: {evaluation_report_str}")
            session.increment_retry("evaluation")
            await session_manager.save_session(session)
            return session, {"type": "LLMError", "message": f"调用LLM生成评估报告失败: {evaluation_report_str}", "details": error}
        
        # 尝试解析评估报告为JSON格式
        parsed_evaluation_report = None
        try:
            cleaned_report_str = evaluation_report_str.strip()
            # 处理可能的代码块包装
            if cleaned_report_str.startswith("```json"): 
                cleaned_report_str = cleaned_report_str[7:]
            if cleaned_report_str.endswith("```"): 
                cleaned_report_str = cleaned_report_str[:-3]
            cleaned_report_str = cleaned_report_str.strip()
            
            parsed_evaluation_report = json.loads(cleaned_report_str)
            logger.info(f"成功解析评估报告为JSON")
        except json.JSONDecodeError as json_e:
            logger.warning(f"无法将评估报告解析为JSON: {json_e}. 使用原始字符串。")
            parsed_evaluation_report = evaluation_report_str
        
        # 更新会话状态
        session.current_evaluation = parsed_evaluation_report
        session.evaluation_reports.append(parsed_evaluation_report)
        session.stage = SessionStage.EVALUATION_COMPLETE
        
        # 添加到对话历史
        session.add_to_history("user", eval_prompt_content)
        session.add_to_history("assistant", evaluation_report_str)
        
        # 保存会话
        await session_manager.save_session(session)
        
        logger.info(f"会话 {session_id} 成功生成评估报告")
        return session, None
    
    except Exception as e:
        error_msg = f"评估提示词失败: {str(e)}"
        session.record_error(error_msg)
        session.increment_retry("evaluation")
        await session_manager.save_session(session)
        logger.error(error_msg, exc_info=True)
        return session, {"type": "UnexpectedError", "message": error_msg}

async def refine_prompt_for_session(session_id: str) -> Tuple[PromptSession, Optional[Dict[str, Any]]]:
    """
    为指定会话优化当前提示词
    
    Args:
        session_id: 会话ID
        
    Returns:
        Tuple[PromptSession, Optional[Dict[str, Any]]]: (会话对象, 错误信息)
    """
    # 获取会话管理器和会话对象
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        error_msg = f"会话 {session_id} 不存在"
        logger.error(error_msg)
        return None, {"type": "SessionNotFound", "message": error_msg}
    
    # 检查会话状态
    if session.stage != SessionStage.EVALUATION_COMPLETE:
        error_msg = f"会话 {session_id} 当前阶段({session.stage})不允许进行优化，需要先完成评估"
        logger.warning(error_msg)
        return session, {"type": "InvalidStage", "message": error_msg}
    
    # 检查递归深度
    if session.current_recursion_depth >= session.max_recursion_depth:
        session.stage = SessionStage.COMPLETED
        session.final_prompt = session.current_prompt
        await session_manager.save_session(session)
        
        message = f"会话 {session_id} 已达到最大递归深度 {session.max_recursion_depth}，停止优化"
        logger.info(message)
        return session, {"type": "MaxDepthReached", "message": message}
    
    try:
        # 获取最近的评估报告
        latest_evaluation = session.current_evaluation
        evaluation_report_str = latest_evaluation
        
        # 如果评估报告是对象，转为字符串
        if isinstance(latest_evaluation, dict):
            try:
                evaluation_report_str = json.dumps(latest_evaluation, ensure_ascii=False)
            except:
                evaluation_report_str = str(latest_evaluation)
        
        # 构建优化提示
        refinement_prompt_content = REFINEMENT_META_PROMPT_TEMPLATE.format(
            user_raw_request=session.user_raw_request,
            previous_prompt=session.current_prompt,
            evaluation_report=evaluation_report_str 
        )
        
        # 调用LLM优化提示词
        refined_prompt, error = await invoke_llm(
            refinement_prompt_content, 
            session.conversation_history, 
            session.model_override, 
            session.provider_override
        )
        
        if error:
            session.record_error(f"生成优化提示失败: {refined_prompt}")
            session.increment_retry("refinement")
            await session_manager.save_session(session)
            return session, {"type": "LLMError", "message": f"调用LLM生成优化提示失败: {refined_prompt}", "details": error}
        
        # 检查优化提示是否与当前提示相同
        if refined_prompt.strip() == session.current_prompt.strip():
            logger.info(f"会话 {session_id} 优化后提示与当前提示相同，优化停止")
            session.stage = SessionStage.COMPLETED
            session.final_prompt = session.current_prompt
        else:
            # 更新会话状态
            session.refined_prompts.append(refined_prompt)
            session.current_prompt = refined_prompt
            session.stage = SessionStage.REFINEMENT_COMPLETE
            session.current_recursion_depth += 1
        
        # 添加到对话历史
        session.add_to_history("user", refinement_prompt_content)
        session.add_to_history("assistant", refined_prompt)
        
        # 保存会话
        await session_manager.save_session(session)
        
        logger.info(f"会话 {session_id} 成功生成优化提示词，当前递归深度: {session.current_recursion_depth}")
        return session, None
    
    except Exception as e:
        error_msg = f"优化提示词失败: {str(e)}"
        session.record_error(error_msg)
        session.increment_retry("refinement")
        await session_manager.save_session(session)
        logger.error(error_msg, exc_info=True)
        return session, {"type": "UnexpectedError", "message": error_msg}

async def complete_session(session_id: str) -> Tuple[PromptSession, Optional[Dict[str, Any]]]:
    """
    完成会话，将当前提示词标记为最终提示词
    
    Args:
        session_id: 会话ID
        
    Returns:
        Tuple[PromptSession, Optional[Dict[str, Any]]]: (会话对象, 错误信息)
    """
    # 获取会话管理器和会话对象
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        error_msg = f"会话 {session_id} 不存在"
        logger.error(error_msg)
        return None, {"type": "SessionNotFound", "message": error_msg}
    
    # 检查是否有可完成的提示词
    if not session.current_prompt:
        error_msg = f"会话 {session_id} 没有可标记为最终的当前提示词"
        logger.error(error_msg)
        return session, {"type": "MissingPrompt", "message": error_msg}
    
    try:
        # 更新会话状态
        session.final_prompt = session.current_prompt
        session.stage = SessionStage.COMPLETED
        
        # 保存会话
        await session_manager.save_session(session)
        
        logger.info(f"会话 {session_id} 已完成，最终提示词已设置")
        return session, None
    
    except Exception as e:
        error_msg = f"完成会话失败: {str(e)}"
        session.record_error(error_msg)
        await session_manager.save_session(session)
        logger.error(error_msg, exc_info=True)
        return session, {"type": "UnexpectedError", "message": error_msg}

async def update_prompt_by_user(
    session_id: str, 
    updated_prompt: str, 
    stage: str = "current",
    comments: str = None
) -> Tuple[PromptSession, Optional[Dict[str, Any]]]:
    """
    用户修改会话中的提示词
    
    Args:
        session_id: 会话ID
        updated_prompt: 用户修改后的提示词
        stage: 要修改的提示词阶段 ("p1", "current", "final")
        comments: 用户对修改的说明
        
    Returns:
        Tuple[PromptSession, Optional[Dict[str, Any]]]: (会话对象, 错误信息)
    """
    # 获取会话管理器和会话对象
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        error_msg = f"会话 {session_id} 不存在"
        logger.error(error_msg)
        return None, {"type": "SessionNotFound", "message": error_msg}
    
    try:
        # 获取原始提示词
        original_prompt = ""
        
        # 根据stage更新相应的提示词
        if stage == "p1":
            original_prompt = session.p1_prompt
            session.p1_prompt = updated_prompt
            session.current_prompt = updated_prompt
            # 如果已经有评估或优化，返回到P1生成后的状态
            session.stage = SessionStage.P1_GENERATED
        elif stage == "current":
            original_prompt = session.current_prompt
            session.current_prompt = updated_prompt
            # 状态保持不变，因为用户只是修改了当前提示词
        elif stage == "final":
            original_prompt = session.final_prompt or session.current_prompt
            session.current_prompt = updated_prompt
            session.final_prompt = updated_prompt
            session.stage = SessionStage.COMPLETED
        else:
            error_msg = f"无效的提示词修改阶段: {stage}，支持的阶段: p1, current, final"
            logger.warning(error_msg)
            return session, {"type": "InvalidStage", "message": error_msg}
        
        # 记录用户修改
        session.record_user_modification(stage, original_prompt, updated_prompt, comments)
        
        # 保存会话
        await session_manager.save_session(session)
        
        logger.info(f"用户成功修改会话 {session_id} 的 {stage} 阶段提示词")
        return session, None
    
    except Exception as e:
        error_msg = f"用户修改提示词失败: {str(e)}"
        session.record_error(error_msg)
        await session_manager.save_session(session)
        logger.error(error_msg, exc_info=True)
        return session, {"type": "UnexpectedError", "message": error_msg}
