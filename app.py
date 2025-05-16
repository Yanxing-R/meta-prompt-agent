# app.py (Updated for Task Types including Code Generation)
import streamlit as st
import json 

try:
    import agent_logic 
    from prompt_templates import STRUCTURED_PROMPT_TEMPLATES 
except ImportError as e:
    st.error(f"启动错误: {e}. 请确保 agent_logic.py 和 prompt_templates.py 文件在同一目录下。")
    st.stop() 

st.set_page_config(page_title="本地元提示代理", layout="wide", initial_sidebar_state="expanded")

st.title("本地元提示代理 (任务区分版) 🚀")
st.caption(f"使用 Ollama 模型: {agent_logic.OLLAMA_MODEL} | API: {agent_logic.OLLAMA_API_URL}")

# --- Session State Initialization ---
if 'processing_results' not in st.session_state:
    st.session_state.processing_results = None
if 'user_raw_request_for_feedback' not in st.session_state:
    st.session_state.user_raw_request_for_feedback = ""
if 'generated_prompt_for_feedback' not in st.session_state:
    st.session_state.generated_prompt_for_feedback = ""
if 'selected_task_type' not in st.session_state:
    st.session_state.selected_task_type = "通用/问答" # Default task type

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ 配置选项")

    # 1. 选择任务类型
    task_types_available = ["通用/问答", "深度研究", "图像生成", "代码生成"]
    # Get current index for selected_task_type to maintain selection across reruns
    current_task_index = 0
    if st.session_state.selected_task_type in task_types_available:
        current_task_index = task_types_available.index(st.session_state.selected_task_type)
    
    st.session_state.selected_task_type = st.selectbox(
        "选择任务类型:", 
        task_types_available, 
        index=current_task_index,
        key="sb_task_type"
    )
    # Extract the primary task type for logic (e.g., "通用" from "通用/问答")
    current_task_type_for_logic = st.session_state.selected_task_type.split('/')[0] 

    enable_self_correction_default = True 
    enable_self_correction = st.checkbox("启用自我校正 (递归优化)", value=enable_self_correction_default, key="cb_self_correct")
    
    max_recursion_depth_default = 1 
    max_recursion_depth = 0
    if enable_self_correction:
        max_recursion_depth = st.number_input("最大递归深度", min_value=0, max_value=3, value=max_recursion_depth_default, step=1, key="num_recursion_depth")

    st.subheader("结构化模板 (可选)")
    filtered_templates = {"无": {}} 
    for name, template_info in STRUCTURED_PROMPT_TEMPLATES.items():
        template_task_categories = template_info.get("task_type", [])
        if current_task_type_for_logic in template_task_categories or \
           ("通用" in template_task_categories and current_task_type_for_logic == "通用") or \
           ("问答" in template_task_categories and current_task_type_for_logic == "问答"): # More specific matching
            filtered_templates[name] = template_info
    
    selected_template_name = st.selectbox(
        "选择一个模板 (基于任务类型筛选):", 
        list(filtered_templates.keys()), 
        key="select_template_filtered"
    )
    
    structured_vars_input = {}
    if selected_template_name != "无" and selected_template_name in filtered_templates:
        st.caption(filtered_templates[selected_template_name].get("description", "没有描述"))
        template_vars_needed = filtered_templates[selected_template_name].get("variables", [])
        if template_vars_needed:
            st.markdown("**模板变量:**")
            for var_name in template_vars_needed:
                # Use text_area for potentially longer inputs in specific templates/variables
                if (selected_template_name == "DetailedImageGen" and var_name == "negative_prompts") or \
                   (selected_template_name == "DetailedCodeFunction" and var_name in ["input_params", "algorithms_steps", "error_handling", "documentation_level", "dependencies", "code_style", "include_tests"]):
                     structured_vars_input[var_name] = st.text_area(f"  {var_name}:", height=80, key=f"var_{selected_template_name}_{var_name}")
                else:
                    structured_vars_input[var_name] = st.text_input(f"  {var_name}:", key=f"var_{selected_template_name}_{var_name}")
        else:
            st.info("此模板不需要额外变量。")

# --- Main Area for Input and Output ---
st.subheader(f"1. 输入您的初步请求 (任务类型: {st.session_state.selected_task_type})")
user_raw_request_placeholder = "例如：帮我写一篇关于人工智能在医疗领域应用的博客文章大纲。"
if current_task_type_for_logic == "图像生成":
    user_raw_request_placeholder = "例如：一只在月球上看书的猫，赛博朋克风格。"
elif current_task_type_for_logic == "研究":
    user_raw_request_placeholder = "例如：分析气候变化对农业的长期影响。"
elif current_task_type_for_logic == "代码生成":
    user_raw_request_placeholder = "例如：用Python写一个函数，计算斐波那契数列的第n项，需要处理负数输入。"


user_raw_request = st.text_area("在此处输入您的请求:", height=150, key="text_user_request",
                                placeholder=user_raw_request_placeholder)

if st.button("🚀 生成优化提示词", key="btn_generate", type="primary", use_container_width=True):
    # Validation logic
    proceed_with_generation = False
    if selected_template_name != "无": # If a structured template is selected
        template_vars_needed = filtered_templates.get(selected_template_name, {}).get("variables", [])
        all_vars_filled = True
        if template_vars_needed: # Only check if template actually has variables defined
            for var_name in template_vars_needed:
                if not structured_vars_input.get(var_name, "").strip():
                    st.error(f"结构化模板 '{selected_template_name}' 需要变量 '{var_name}' 的值。")
                    all_vars_filled = False
                    break
        if all_vars_filled:
            proceed_with_generation = True
    elif user_raw_request.strip(): # No template, but raw request is present
        proceed_with_generation = True
    else: # No template and no raw request
        st.warning("请输入您的初步请求，或选择一个结构化模板并填写其变量。")

    if proceed_with_generation:
        st.session_state.processing_results = None 
        with st.spinner(f"🤖 代理正在为 '{st.session_state.selected_task_type}' 任务思考中..."):
            use_template_for_logic = selected_template_name if selected_template_name != "无" else None
            results = agent_logic.generate_and_refine_prompt(
                user_raw_request=user_raw_request, 
                task_type=current_task_type_for_logic,
                enable_self_correction=enable_self_correction,
                max_recursion_depth=max_recursion_depth,
                use_structured_template_name=use_template_for_logic,
                structured_template_vars=structured_vars_input if use_template_for_logic else None
            )
            st.session_state.processing_results = results
            st.session_state.user_raw_request_for_feedback = user_raw_request # Store the raw request for feedback context
            st.session_state.generated_prompt_for_feedback = results.get("final_prompt", "")


# --- Display Results ---
if st.session_state.processing_results:
    results = st.session_state.processing_results
    st.divider()
    st.subheader(f"2. 处理结果 (任务: {st.session_state.selected_task_type})")

    if results.get("error_message"):
        st.error(f"处理过程中发生错误: {results['error_message']}")
        if results.get("error_details"):
            st.json(results["error_details"]) 
    else:
        st.success("🎉 提示词已成功生成/优化！")

        with st.expander("查看详细处理日志和中间步骤", expanded=False):
            st.markdown("#### 内部处理日志:")
            log_container = st.container(height=200) 
            for log_entry in results.get("log", []):
                log_container.text(log_entry) 
            
            st.markdown("#### 初始核心提示 (发送给LLM):")
            st.text_area("初始核心提示内容:", value=results.get("initial_core_prompt", "未记录"), height=200, disabled=True, key="disp_initial_core")

            st.markdown("#### 初步优化后的提示词 (P1):")
            st.text_area("P1内容:", value=results.get("p1_initial_optimized_prompt", "未生成或未记录"), height=200, disabled=True, key="disp_p1")


            if results.get("evaluation_reports"):
                for i, report in enumerate(results["evaluation_reports"]):
                    st.markdown(f"#### 评估报告 (E{i+1}):")
                    st.text_area(f"E{i+1}内容:", value=report, height=200, disabled=True, key=f"disp_e{i+1}")
            
            if results.get("refined_prompts"):
                for i, prompt_text in enumerate(results["refined_prompts"]):
                    st.markdown(f"#### 第 {i+1} 轮精炼后的提示词 (P{i+2}):")
                    st.text_area(f"P{i+2}内容:", value=prompt_text, height=200, disabled=True, key=f"disp_p_refined{i+1}")
        
        st.subheader("🎯 最终优化后的目标提示词:")
        final_prompt_text = results.get("final_prompt", "未能生成最终提示词。")
        # Allow copying by making it a non-disabled text_area
        st.text_area("最终提示词内容 (可复制):", value=final_prompt_text, height=300, key="disp_final_prompt_copyable", help="您可以从此框中复制提示词。")
        
        st.divider()
        st.subheader("3. 提供反馈 (可选)")
        if st.session_state.generated_prompt_for_feedback and "错误：" not in st.session_state.generated_prompt_for_feedback :
            feedback_rating = st.slider("您对这个提示词的质量评分 (1=差, 5=优):", 1, 5, 3, key="slider_rating_tasks")
            feedback_comments = st.text_area("您的具体修改建议或评论:", key="text_feedback_comments_tasks", height=100)
            
            if st.button("提交反馈", key="btn_submit_feedback_tasks"):
                feedback_to_save = {
                    "rating": feedback_rating,
                    "comments": feedback_comments,
                    "original_request": st.session_state.user_raw_request_for_feedback,
                    "generated_prompt": st.session_state.generated_prompt_for_feedback,
                    "task_type": st.session_state.selected_task_type, 
                    "model_used": agent_logic.OLLAMA_MODEL, 
                    "self_correction_enabled": enable_self_correction, 
                    "recursion_depth_if_enabled": max_recursion_depth if enable_self_correction else 0,
                    "structured_template_used": selected_template_name if selected_template_name != "无" else "无"
                }
                
                current_feedback_list = agent_logic.load_feedback()
                current_feedback_list.append(feedback_to_save)
                if agent_logic.save_feedback(current_feedback_list):
                    st.success("感谢您的反馈！已保存。")
                else:
                    st.error("保存反馈失败。请检查后台日志。")
        else:
            st.info("生成提示词后可在此处提供反馈。")

st.sidebar.divider()
st.sidebar.info(
    "这是一个本地元提示代理的演示界面。\n\n"
    "它使用Ollama在您的计算机上本地运行LLM。"
)

