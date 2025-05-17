import logging
import requests
import json
import os
from meta_prompt_agent.config import settings
from meta_prompt_agent.prompts.templates import (
    CORE_META_PROMPT_TEMPLATE,
    EVALUATION_META_PROMPT_TEMPLATE,
    REFINEMENT_META_PROMPT_TEMPLATE,
    STRUCTURED_PROMPT_TEMPLATES
)

logger = logging.getLogger(__name__)

def load_and_format_structured_prompt(template_name: str, user_request: str, variables: dict | None) -> str | None:
    # 调试导入的 STRUCTURED_PROMPT_TEMPLATES
    if not isinstance(STRUCTURED_PROMPT_TEMPLATES, dict):
        logger.critical(
            f"STRUCTURED_PROMPT_TEMPLATES 不是一个字典 (实际类型: {type(STRUCTURED_PROMPT_TEMPLATES)}). "
            "请检查 prompts/templates.py 中的定义。"
        )
        return None # 或者抛出一个更严重的配置错误

    logger.debug(f"尝试加载并格式化结构化模板: '{template_name}'，用户请求: '{user_request[:50]}...', 变量: {variables}")

    if template_name not in STRUCTURED_PROMPT_TEMPLATES:
        logger.warning(f"未找到名为 '{template_name}' 的结构化提示模板。可用模板: {list(STRUCTURED_PROMPT_TEMPLATES.keys())}")
        return None

    template_data = STRUCTURED_PROMPT_TEMPLATES[template_name]
    if not isinstance(template_data, dict):
        logger.error(f"模板 '{template_name}' 的数据格式不正确，期望是一个字典，实际是 {type(template_data)}。")
        return None

    required_vars = template_data.get("variables", [])
    if not isinstance(required_vars, list): # 确保 required_vars 是列表
        logger.error(f"模板 '{template_name}' 中的 'variables' 属性不是一个列表，实际是 {type(required_vars)}。")
        required_vars = [] # 作为一种容错处理，或者返回 None

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
        format_vars['user_raw_request'] = user_request # 确保 user_raw_request 总是存在

        core_template_str = template_data.get("core_template_override")
        if not isinstance(core_template_str, str): # 确保 core_template_override 是字符串
            logger.error(f"模板 '{template_name}' 中的 'core_template_override' 不是一个字符串或未定义。")
            return None

        final_prompt_content = core_template_str.format(**format_vars)
        logger.info(f"成功格式化结构化模板 '{template_name}'。")
        return final_prompt_content
    except KeyError as e:
        logger.error(
            f"格式化结构化提示模板 '{template_name}' 时缺少预期的变量占位符: '{e}'. "
            f"请检查模板字符串中的占位符与提供的/必需的变量是否匹配。格式化时使用的变量键: {list(format_vars.keys())}.",
            exc_info=True
        )
        return None
    except Exception as e:
        logger.exception(
            f"格式化结构化提示模板 '{template_name}' 时发生未知错误。"
        )
        return None

def call_ollama_api(prompt_content: str, messages_history: list = None) -> tuple[str, dict | None]:
    current_messages = []
    if messages_history:
        current_messages.extend(messages_history)
    current_messages.append({"role": "user", "content": prompt_content})

    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": current_messages,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(settings.OLLAMA_API_URL, headers=headers, data=json.dumps(payload), timeout=180)
        response.raise_for_status()
        response_data = response.json()
        if "message" in response_data and "content" in response_data["message"]:
            return response_data["message"]["content"].strip(), None
        else:
            error_msg = "Ollama API响应格式不符合预期"
            return f"错误：{error_msg}", {"type": "FormatError", "details": response_data}
    except requests.exceptions.ConnectionError as e:
        error_msg = f"无法连接到Ollama服务: {settings.OLLAMA_API_URL}"
        logger.error(f"{error_msg}. 详细错误: {e}", exc_info=True) # exc_info=True 会记录堆栈跟踪
        return f"错误：{error_msg}", {"type": "ConnectionError", "url": settings.OLLAMA_API_URL, "details": str(e)}
    except requests.exceptions.Timeout as e:
        error_msg = f"请求Ollama API超时 ({settings.OLLAMA_API_URL})"
        logger.error(f"{error_msg}. 详细错误: {e}", exc_info=True)
        return f"错误：{error_msg}", {"type": "TimeoutError", "url": settings.OLLAMA_API_URL, "details": str(e)}
    except requests.exceptions.HTTPError as e:
        error_text = f"Ollama API交互失败 (HTTP {e.response.status_code})"
        logger.error(f"{error_text}. 详细错误: {e}", exc_info=True)
        details = {"type": "HTTPError", "status_code": e.response.status_code, "raw_response": e.response.text}
        try: 
            error_details_json = e.response.json()
            if "error" in error_details_json:
                error_text += f" Ollama错误: {error_details_json['error']}"
                details["ollama_error"] = error_details_json['error']
        except json.JSONDecodeError as e:
            pass
        return f"错误：{error_text}", details
    except Exception as e:
        error_msg = f"调用Ollama API时发生未知内部错误"
        logger.error(f"{error_msg}", exc_info=True)
        return f"错误：{error_msg}", {"type": "UnknownError", "exception_type": e.__class__.__name__, "details": "详情请查看应用日志"}


def generate_and_refine_prompt(
    user_raw_request: str, 
    task_type: str, 
    enable_self_correction: bool,
    max_recursion_depth: int,
    use_structured_template_name: str = None, 
    structured_template_vars: dict = None
) -> dict:

    try:
        results = {
            "initial_core_prompt": "",
            "p1_initial_optimized_prompt": "",
            "evaluation_reports": [],
            "refined_prompts": [],
            "final_prompt": "",
            "error_message": None,
            "error_details": None
        }

        logger.info(f"开始处理任务类型 '{task_type}' 的请求: '{user_raw_request[:50]}...'")

        initial_core_prompt_for_llm = ""

        if use_structured_template_name and structured_template_vars:
            logger.info(f"[代理信息] 尝试使用结构化模板: {use_structured_template_name}")
            selected_template_data = STRUCTURED_PROMPT_TEMPLATES.get(use_structured_template_name, {})
            template_task_types = selected_template_data.get("task_type", ["通用"])
            if task_type not in template_task_types and "通用" not in template_task_types:
                logger.warning(f"[警告] 所选结构化模板 '{use_structured_template_name}' (类型: {template_task_types}) 与当前任务类型 '{task_type}' 可能不完全匹配。")

            formatted_prompt_from_structure = load_and_format_structured_prompt(
                use_structured_template_name, 
                user_raw_request,
                structured_template_vars
            )
            if formatted_prompt_from_structure:
                initial_core_prompt_for_llm = formatted_prompt_from_structure
                logger.info(f"[代理信息] 使用格式化后的结构化模板 '{use_structured_template_name}' 作为核心指令。")
            else: # Structured template failed or not applicable
                logger.warning(f"[代理信息] 结构化模板 '{use_structured_template_name}' 处理失败或不适用，回退到基于任务类型的默认核心模板。")
                # Fallback logic based on task_type
                if task_type == "图像生成" and "BasicImageGen" in STRUCTURED_PROMPT_TEMPLATES:
                     initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(user_raw_request=user_raw_request)
                     logger.info("[代理信息] 使用 'BasicImageGen' 模板作为图像生成的默认核心指令。")
                elif task_type == "代码生成" and "BasicCodeSnippet" in STRUCTURED_PROMPT_TEMPLATES:
                     # For basic code gen, we need programming_language, which might not be in user_raw_request directly
                    # This fallback might need user to specify language in their raw request for BasicCodeSnippet
                    # Or we assume a default language or ask the LLM to infer.
                    # For simplicity, if BasicCodeSnippet is chosen as fallback, it expects {programming_language}
                    # This part might need more sophisticated handling if language isn't in structured_template_vars
                    # For now, let's assume if this fallback is hit, user_raw_request should imply the language for BasicCodeSnippet
                    # Or, more robustly, BasicCodeSnippet should be used via structured selection where language is a var.
                    # If BasicCodeSnippet is a fallback, it's hard to get `programming_language`.
                    # So, for now, fallback for code gen will also be CORE_META_PROMPT_TEMPLATE.
                    # User should ideally select a structured template for code gen.
                    #results["log"].append("[代理信息] 代码生成任务回退到通用核心模板 (建议使用结构化模板)。")
                    logger.info("[代理信息] 代码生成任务回退到通用核心模板 (建议使用结构化模板)。")
                    initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
                else:
                    initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
                    logger.info("[代理信息] 使用通用核心模板。")

        else: # No structured template selected
            if task_type == "图像生成" and "BasicImageGen" in STRUCTURED_PROMPT_TEMPLATES:
                 initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(user_raw_request=user_raw_request)
                 logger.info("[代理信息] 未选择结构化模板，使用 'BasicImageGen' 模板作为图像生成的默认核心指令。")
            elif task_type == "代码生成" and "BasicCodeSnippet" in STRUCTURED_PROMPT_TEMPLATES:
                # Similar to above, BasicCodeSnippet needs 'programming_language'.
                # If user just types "write a python function for sum" and doesn't use structured template,
                # this fallback is tricky. We'll use CORE_META_PROMPT_TEMPLATE.
                logger.info("[代理信息] 未选择结构化模板，代码生成任务使用通用核心模板 (建议使用结构化模板并提供编程语言)。")
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
            else:
                initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
                logger.info("[代理信息] 未选择结构化模板，使用通用核心模板。")

        results["initial_core_prompt"] = initial_core_prompt_for_llm
        conversation_history = []
    
        p1, error = call_ollama_api(initial_core_prompt_for_llm, None)
        if error:
            error_msg_for_results = f"生成初始优化提示失败: {p1}" # p1 已经是 "错误：..."
            logger.error(f"调用Ollama API生成初始提示失败。API返回: {p1}, 错误详情: {error}")
            results["error_message"] = error_msg_for_results
            results["error_details"] = error
            return results
    
        results["p1_initial_optimized_prompt"] = p1
        conversation_history.append({"role": "user", "content": str(initial_core_prompt_for_llm)})
        conversation_history.append({"role": "assistant", "content": str(p1)})
    
        current_best_prompt = p1
        logger.info("\n---------- 初步优化后的提示词 (P1) ----------")
        logger.info(current_best_prompt)
        logger.info("--------------------------------------------")

        if not enable_self_correction:
            results["final_prompt"] = current_best_prompt
            return results

        for i in range(max_recursion_depth):
            logger.info(f"开始第 {i+1} 轮自我校正 (任务类型: {task_type})...")
            
            # 使用新的 EVALUATION_META_PROMPT_TEMPLATE
            eval_prompt_content = EVALUATION_META_PROMPT_TEMPLATE.format(
                user_raw_request=user_raw_request, 
                prompt_to_evaluate=current_best_prompt
            )
            logger.debug(f"发送给Ollama进行评估的提示内容 (E{i+1}):\n{eval_prompt_content}")
            
            evaluation_report_str, error = call_ollama_api(eval_prompt_content, []) # 评估通常不需要历史
            if error:
                logger.warning(f"第 {i+1} 轮自我校正：生成评估报告失败。API返回: {evaluation_report_str}, 错误详情: {error}")
                break # 评估失败，中断自我校正，使用当前最好的提示
            
            logger.info(f"从Ollama获取的原始评估报告字符串 (E{i+1}):\n{evaluation_report_str}")

            # --- 新增：尝试解析JSON评估报告 ---
            parsed_evaluation_report = None
            try:
                # 尝试去除可能的Markdown代码块标记 (```json ... ```)
                # 有些LLM可能会在JSON前后加上这个
                cleaned_report_str = evaluation_report_str.strip()
                if cleaned_report_str.startswith("```json"):
                    cleaned_report_str = cleaned_report_str[7:] # 去除 ```json
                if cleaned_report_str.endswith("```"):
                    cleaned_report_str = cleaned_report_str[:-3] # 去除 ```
                cleaned_report_str = cleaned_report_str.strip() # 再次去除可能的空白

                parsed_evaluation_report = json.loads(cleaned_report_str)
                results["evaluation_reports"].append(parsed_evaluation_report) # 存储解析后的字典
                logger.info(f"成功解析评估报告 (E{i+1}) 为JSON对象。")
                logger.debug(f"解析后的评估报告 (E{i+1}) 内容: {json.dumps(parsed_evaluation_report, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError as json_e:
                logger.warning(
                    f"无法将评估报告 (E{i+1}) 解析为JSON。错误: {json_e}. "
                    f"将使用原始字符串作为评估报告。原始报告: \n{evaluation_report_str}"
                )
                results["evaluation_reports"].append(evaluation_report_str) # 存储原始字符串
            # --- JSON解析结束 ---
            
            # 记录到对话历史时，确保内容是字符串
            conversation_history.append({"role": "user", "content": str(eval_prompt_content)}) 
            conversation_history.append({"role": "assistant", "content": str(evaluation_report_str)}) # 历史中存原始字符串

            # 使用原始字符串（或未来可以用解析后的结构化信息）来格式化精炼提示
            refinement_prompt_content = REFINEMENT_META_PROMPT_TEMPLATE.format(
                user_raw_request=user_raw_request,
                previous_prompt=current_best_prompt,
                evaluation_report=evaluation_report_str # 精炼模板暂时还使用原始字符串
            )
            logger.debug(f"发送给Ollama进行精炼的提示内容 (P{i+2}):\n{refinement_prompt_content}")

            refined_prompt, error = call_ollama_api(refinement_prompt_content, conversation_history)
            if error:
                logger.warning(f"第 {i+1} 轮自我校正：生成精炼提示失败。API返回: {refined_prompt}, 错误详情: {error}")
                break # 精炼失败，中断自我校正
            
            logger.info(f"第 {i+1} 轮精炼后的提示词 (P{i+2}):\n{refined_prompt}")
            results["refined_prompts"].append(refined_prompt)
            
            if refined_prompt.strip() == current_best_prompt.strip():
                 logger.info("精炼后的提示与上一版相同，停止递归。")
                 break
            
            current_best_prompt = refined_prompt
            # 记录到对话历史
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
        return [] # 或者根据策略抛出异常或返回特定错误对象
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
    except TypeError as e: # json.dump 可能会因为数据类型问题抛出 TypeError
        logger.error(f"序列化反馈数据到 '{settings.FEEDBACK_FILE}' 时发生类型错误: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.exception(f"保存反馈数据到 '{settings.FEEDBACK_FILE}' 时发生未知错误。")
        return False

if __name__ == '__main__':
    print("Testing agent_logic.py with task types including Code Generation...")
    
    # 测试代码生成 (使用详细结构化模板)
    test_code_vars = {
        "programming_language": "Python",
        "function_name": "calculate_factorial",
        "input_params": "n: int (非负整数)",
        "return_value": "int (n的阶乘)",
        "algorithms_steps": "使用递归或循环实现阶乘计算",
        "error_handling": "如果n是负数，应引发ValueError",
        "documentation_level": "需要包含函数文档字符串，解释功能、参数和返回值",
        "dependencies": "无",
        "code_style": "PEP 8",
        "include_tests": "是，请提供至少3个pytest测试用例，包括边界条件和错误情况"
    }
    results_code = generate_and_refine_prompt(
        user_raw_request="我需要一个计算阶乘的Python函数，要健壮且有测试。", 
        task_type="代码生成",
        enable_self_correction=True, 
        max_recursion_depth=1, # Set to 1 for faster testing
        use_structured_template_name="DetailedCodeFunction",
        structured_template_vars=test_code_vars
    )
    print("\n=== DETAILED CODE GENERATION RESULTS ===")
    print(f"Initial Core Prompt for LLM:\n{results_code['initial_core_prompt']}\n")
    print(f"P1 Initial Optimized Prompt:\n{results_code['p1_initial_optimized_prompt']}\n")
    if results_code.get("evaluation_reports"):
        print(f"Evaluation Report E1:\n{results_code['evaluation_reports'][0]}\n")
    if results_code.get("refined_prompts"):
        print(f"Refined Prompt P2:\n{results_code['refined_prompts'][0]}\n")
    print(f"Final Prompt to use for Code LLM:\n{results_code['final_prompt']}")
    if results_code['error_message']:
        print(f"Error: {results_code['error_message']}")
    print("\nFull Log:")
    for log_entry in results_code.get("log", []): print(log_entry)

    # 测试基础代码片段 (不使用结构化模板，依赖 user_raw_request 包含语言信息)
    # test_basic_code_request = "写一个JavaScript函数，检查字符串是否是回文串。"
    # results_basic_code = generate_and_refine_prompt(
    #     test_basic_code_request,
    #     task_type="代码生成",
    #     enable_self_correction=False,
    #     max_recursion_depth=0
    #     # Note: BasicCodeSnippet template expects 'programming_language' as a variable.
    #     # If not using structured_template_vars, the fallback logic needs to handle this.
    #     # Current fallback for code gen is CORE_META_PROMPT_TEMPLATE if language isn't obvious.
    # )
    # print("\n=== BASIC CODE SNIPPET RESULTS (using CORE_META_PROMPT_TEMPLATE as fallback) ===")
    # print(f"Final Prompt: {results_basic_code['final_prompt']}")
    # for log_entry in results_basic_code.get("log", []): print(log_entry)