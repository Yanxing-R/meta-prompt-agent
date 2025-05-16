# agent_logic.py (Updated for Task Types including Code Generation)

import requests
import json
import sys
import os

try:
    from prompt_templates import (
        CORE_META_PROMPT_TEMPLATE,
        EVALUATION_META_PROMPT_TEMPLATE,
        REFINEMENT_META_PROMPT_TEMPLATE,
        STRUCTURED_PROMPT_TEMPLATES
    )
except ImportError:
    print("[错误] 无法导入 prompt_templates.py。请确保该文件与 agent_logic.py 在同一目录下。")
    raise ImportError("prompt_templates.py not found.")


OLLAMA_MODEL = 'qwen3:4b' 
OLLAMA_API_URL = 'http://localhost:11434/api/chat' 
FEEDBACK_FILE = "user_feedback.json" 

def load_and_format_structured_prompt(template_name: str, user_request: str, variables: dict) -> str | None:
    if template_name not in STRUCTURED_PROMPT_TEMPLATES:
        print(f"[警告] 未找到名为 '{template_name}' 的结构化提示模板。")
        return None

    template_data = STRUCTURED_PROMPT_TEMPLATES[template_name]
    required_vars = template_data.get("variables", [])
    
    if required_vars:
        missing_vars = [var for var in required_vars if var not in variables or not str(variables[var]).strip()] # Ensure value is not just whitespace
        if missing_vars:
            print(f"[警告] 结构化提示模板 '{template_name}' 需要以下变量的值: {', '.join(missing_vars)}。")
            return None

    try:
        format_vars = variables.copy()
        format_vars['user_raw_request'] = user_request 
        
        core_override = template_data.get("core_template_override")
        if not core_override:
            print(f"[信息] 结构化模板 '{template_name}' 没有提供 core_template_override。")
            return None 

        final_prompt_content = core_override.format(**format_vars)
        return final_prompt_content
    except KeyError as e:
        print(f"[警告] 结构化提示模板 '{template_name}' 格式化时缺少变量 '{e}'。请确保所有在模板中使用的占位符都在variables列表中定义，并已提供值。")
        return None
    except Exception as e:
        print(f"[错误] 格式化结构化提示 '{template_name}' 时出错: {e}")
        return None


def call_ollama_api(prompt_content: str, messages_history: list = None) -> tuple[str, dict | None]:
    current_messages = []
    if messages_history:
        current_messages.extend(messages_history)
    current_messages.append({"role": "user", "content": prompt_content})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": current_messages,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(OLLAMA_API_URL, headers=headers, data=json.dumps(payload), timeout=180)
        response.raise_for_status()
        response_data = response.json()
        if "message" in response_data and "content" in response_data["message"]:
            return response_data["message"]["content"].strip(), None
        else:
            error_msg = "Ollama API响应格式不符合预期"
            return f"错误：{error_msg}", {"type": "FormatError", "details": response_data}
    except requests.exceptions.ConnectionError:
        error_msg = f"无法连接到Ollama服务于 {OLLAMA_API_URL}"
        return f"错误：{error_msg}", {"type": "ConnectionError", "url": OLLAMA_API_URL}
    except requests.exceptions.Timeout:
        error_msg = f"请求Ollama API超时 ({OLLAMA_API_URL})"
        return f"错误：{error_msg}", {"type": "TimeoutError", "url": OLLAMA_API_URL}
    except requests.exceptions.HTTPError as e:
        error_text = f"Ollama API交互失败 (HTTP {e.response.status_code})"
        details = {"type": "HTTPError", "status_code": e.response.status_code, "raw_response": e.response.text}
        try: 
            error_details_json = e.response.json()
            if "error" in error_details_json:
                error_text += f" Ollama错误: {error_details_json['error']}"
                details["ollama_error"] = error_details_json['error']
        except json.JSONDecodeError:
            pass
        return f"错误：{error_text}", details
    except Exception as e:
        error_msg = f"调用Ollama API时发生错误: {e}"
        return f"错误：{error_msg}", {"type": "UnknownError", "exception": str(e)}


def generate_and_refine_prompt(
    user_raw_request: str, 
    task_type: str, 
    enable_self_correction: bool,
    max_recursion_depth: int,
    use_structured_template_name: str = None, 
    structured_template_vars: dict = None
) -> dict:
    results = {
        "initial_core_prompt": "",
        "p1_initial_optimized_prompt": "",
        "evaluation_reports": [],
        "refined_prompts": [],
        "final_prompt": "",
        "error_message": None,
        "error_details": None,
        "log": []
    }
    
    results["log"].append(f"[代理信息] 任务类型: {task_type}")
    results["log"].append("[代理信息] 开始生成初始优化提示...")
    
    initial_core_prompt_for_llm = ""

    if use_structured_template_name and structured_template_vars:
        results["log"].append(f"[代理信息] 尝试使用结构化模板: {use_structured_template_name}")
        selected_template_data = STRUCTURED_PROMPT_TEMPLATES.get(use_structured_template_name, {})
        template_task_types = selected_template_data.get("task_type", ["通用"])
        if task_type not in template_task_types and "通用" not in template_task_types:
            results["log"].append(f"[警告] 所选结构化模板 '{use_structured_template_name}' (类型: {template_task_types}) 与当前任务类型 '{task_type}' 可能不完全匹配。")

        formatted_prompt_from_structure = load_and_format_structured_prompt(
            use_structured_template_name, 
            user_raw_request,
            structured_template_vars
        )
        if formatted_prompt_from_structure:
            initial_core_prompt_for_llm = formatted_prompt_from_structure
            results["log"].append(f"[代理信息] 使用格式化后的结构化模板 '{use_structured_template_name}' 作为核心指令。")
        else: # Structured template failed or not applicable
            results["log"].append(f"[代理信息] 结构化模板 '{use_structured_template_name}' 处理失败或不适用，回退到基于任务类型的默认核心模板。")
            # Fallback logic based on task_type
            if task_type == "图像生成" and "BasicImageGen" in STRUCTURED_PROMPT_TEMPLATES:
                 initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(user_raw_request=user_raw_request)
                 results["log"].append("[代理信息] 使用 'BasicImageGen' 模板作为图像生成的默认核心指令。")
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
                 results["log"].append("[代理信息] 代码生成任务回退到通用核心模板 (建议使用结构化模板)。")
                 initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
            else:
                 initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
                 results["log"].append("[代理信息] 使用通用核心模板。")
    else: # No structured template selected
        if task_type == "图像生成" and "BasicImageGen" in STRUCTURED_PROMPT_TEMPLATES:
             initial_core_prompt_for_llm = STRUCTURED_PROMPT_TEMPLATES["BasicImageGen"]["core_template_override"].format(user_raw_request=user_raw_request)
             results["log"].append("[代理信息] 未选择结构化模板，使用 'BasicImageGen' 模板作为图像生成的默认核心指令。")
        elif task_type == "代码生成" and "BasicCodeSnippet" in STRUCTURED_PROMPT_TEMPLATES:
            # Similar to above, BasicCodeSnippet needs 'programming_language'.
            # If user just types "write a python function for sum" and doesn't use structured template,
            # this fallback is tricky. We'll use CORE_META_PROMPT_TEMPLATE.
            results["log"].append("[代理信息] 未选择结构化模板，代码生成任务使用通用核心模板 (建议使用结构化模板并提供编程语言)。")
            initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
        else:
            initial_core_prompt_for_llm = CORE_META_PROMPT_TEMPLATE.format(user_raw_request=user_raw_request)
            results["log"].append("[代理信息] 未选择结构化模板，使用通用核心模板。")

    results["initial_core_prompt"] = initial_core_prompt_for_llm
    conversation_history = []
    
    p1, error = call_ollama_api(initial_core_prompt_for_llm, None)
    if error:
        results["error_message"] = p1
        results["error_details"] = error
        results["log"].append(f"[错误] 初始提示生成失败: {p1}")
        return results
    
    results["p1_initial_optimized_prompt"] = p1
    conversation_history.append({"role": "user", "content": initial_core_prompt_for_llm})
    conversation_history.append({"role": "assistant", "content": p1})
    
    current_best_prompt = p1
    results["log"].append("\n---------- 初步优化后的提示词 (P1) ----------")
    results["log"].append(current_best_prompt)
    results["log"].append("--------------------------------------------")

    if not enable_self_correction:
        results["final_prompt"] = current_best_prompt
        return results

    for i in range(max_recursion_depth):
        results["log"].append(f"\n[代理信息] 开始第 {i+1} 轮自我校正 (任务类型: {task_type})...")
        eval_prompt_content = EVALUATION_META_PROMPT_TEMPLATE.format(
            user_raw_request=user_raw_request, 
            prompt_to_evaluate=current_best_prompt
        )
        evaluation_report, error = call_ollama_api(eval_prompt_content, [])
        if error:
            results["log"].append(f"[警告] 生成评估报告失败: {evaluation_report}")
            break 
        
        results["evaluation_reports"].append(evaluation_report)
        conversation_history.append({"role": "user", "content": eval_prompt_content}) 
        conversation_history.append({"role": "assistant", "content": evaluation_report})
        results["log"].append("\n---------- 评估报告 (E) ----------")
        results["log"].append(evaluation_report)
        results["log"].append("----------------------------------")

        refinement_prompt_content = REFINEMENT_META_PROMPT_TEMPLATE.format(
            user_raw_request=user_raw_request,
            previous_prompt=current_best_prompt,
            evaluation_report=evaluation_report
        )
        refined_prompt, error = call_ollama_api(refinement_prompt_content, conversation_history)
        if error:
            results["log"].append(f"[警告] 生成精炼提示失败: {refined_prompt}")
            break 
        
        results["refined_prompts"].append(refined_prompt)
        conversation_history.append({"role": "user", "content": refinement_prompt_content})
        conversation_history.append({"role": "assistant", "content": refined_prompt})

        if refined_prompt.strip() == current_best_prompt.strip():
             results["log"].append("[代理信息] 精炼后的提示与上一版相同，停止递归。")
             break
        
        current_best_prompt = refined_prompt
        results["log"].append(f"\n---------- 第 {i+1} 轮精炼后的提示词 (P{i+2}) ----------")
        results["log"].append(current_best_prompt)
        results["log"].append("-------------------------------------------------")
             
    results["final_prompt"] = current_best_prompt
    return results

def load_feedback():
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[警告] 加载反馈文件失败: {e}")
            return []
    return []

def save_feedback(all_feedback_data):
    try:
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_feedback_data, f, ensure_ascii=False, indent=4)
        print(f"[代理信息] 反馈已保存到 {FEEDBACK_FILE}") 
        return True
    except IOError as e:
        print(f"[错误] 保存反馈文件失败: {e}")
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


