# src/meta_prompt_agent/api/main.py
import logging
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum

try:
    from meta_prompt_agent.core.agent import (
        generate_and_refine_prompt, 
        explain_term_in_prompt, 
        load_feedback, 
        save_feedback,
        create_interactive_session,
        generate_p1_prompt_for_session,
        evaluate_prompt_for_session,
        refine_prompt_for_session,
        complete_session,
        update_prompt_by_user
    )
    from meta_prompt_agent.core.session_manager import (
        get_session_manager,
        SessionStage,
        PromptSession
    )
    from meta_prompt_agent.config.logging_config import setup_logging
    from meta_prompt_agent.config.settings import get_settings, IS_DEV_ENV
    from meta_prompt_agent.api.docs import custom_openapi_schema
    # setup_logging()
except ImportError as e:
    print(f"导入错误: {e}. 请确保PYTHONPATH或运行目录正确。")
    async def generate_and_refine_prompt(*args, **kwargs): # type: ignore
        return {"error_message": "核心逻辑(g&r)未正确导入", "p1_initial_optimized_prompt": ""}
    async def explain_term_in_prompt(*args, **kwargs): # type: ignore
        return "错误：核心逻辑(explain)未正确导入", {"type": "ImportError", "details": str(e)}
    async def load_feedback(*args, **kwargs): # type: ignore
        return []
    async def save_feedback(*args, **kwargs): # type: ignore
        return False
    # 交互式会话相关函数的占位符
    async def create_interactive_session(*args, **kwargs): # type: ignore
        return None, {"type": "ImportError", "message": "核心逻辑未正确导入"}
    async def generate_p1_prompt_for_session(*args, **kwargs): # type: ignore
        return None, {"type": "ImportError", "message": "核心逻辑未正确导入"}
    async def evaluate_prompt_for_session(*args, **kwargs): # type: ignore
        return None, {"type": "ImportError", "message": "核心逻辑未正确导入"}
    async def refine_prompt_for_session(*args, **kwargs): # type: ignore
        return None, {"type": "ImportError", "message": "核心逻辑未正确导入"}
    async def complete_session(*args, **kwargs): # type: ignore
        return None, {"type": "ImportError", "message": "核心逻辑未正确导入"}
    async def update_prompt_by_user(*args, **kwargs): # type: ignore
        return None, {"type": "ImportError", "message": "核心逻辑未正确导入"}
    def get_session_manager(*args, **kwargs): # type: ignore
        return None
    def custom_openapi_schema(app): # type: ignore
        def custom_openapi(): return {}
        return custom_openapi
    def get_settings(): return {"ACTIVE_LLM_PROVIDER": "default"} # type: ignore
    IS_DEV_ENV = False # type: ignore
    class SessionStage(str, Enum): # type: ignore
        CREATED = "created"
        P1_GENERATED = "p1_generated"
        EVALUATION_COMPLETE = "evaluation_complete"
        REFINEMENT_COMPLETE = "refinement_complete"
        COMPLETED = "completed"
    pass


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Meta-Prompt Agent API",
    description="提供元提示生成与优化服务的API。",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.openapi = custom_openapi_schema(app)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_api_settings():
    return get_settings()

class ModelInfo(BaseModel):
    model: str = Field(..., description="模型名称")
    provider: str = Field(..., description="提供商名称")

class UserRequest(BaseModel):
    raw_request: str = Field(..., min_length=1, description="用户的原始文本请求")
    task_type: str = Field(default="通用/问答", description="任务类型")
    model_info: Optional[ModelInfo] = Field(None, description="模型和提供商信息")

class P1Response(BaseModel):
    p1_prompt: str
    original_request: str
    message: str | None = None

class ExplainTermRequest(BaseModel):
    term_to_explain: str = Field(..., min_length=1, description="需要解释的术语或短语")
    context_prompt: str = Field(..., min_length=1, description="包含该术语的完整提示词上下文")
    model_info: Optional[ModelInfo] = Field(None, description="模型和提供商信息")

class ExplanationResponse(BaseModel):
    explanation: str
    term: str
    context_snippet: str | None = None
    message: str | None = None

class FeedbackItem(BaseModel):
    prompt_id: str = Field(..., description="提示的唯一标识符")
    original_request: str = Field(..., description="原始用户请求")
    generated_prompt: str = Field(..., description="生成的优化提示")
    rating: int = Field(..., ge=1, le=5, description="用户评分(1-5)")
    comment: str | None = Field(None, description="用户反馈评论")
    timestamp: datetime = Field(default_factory=datetime.now)
    model: str | None = Field(None, description="使用的模型")

class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str | None = None

class FeedbackListResponse(BaseModel):
    feedback_items: List[FeedbackItem]
    total_count: int

class AdvancedPromptRequest(BaseModel):
    raw_request: str = Field(..., min_length=1, description="用户的原始文本请求")
    task_type: str = Field(default="通用/问答", description="任务类型")
    enable_self_correction: bool = Field(default=True, description="是否启用自我校正")
    max_recursion_depth: int = Field(default=2, ge=0, le=5, description="最大递归深度")
    template_name: str | None = Field(None, description="结构化模板名称")
    template_variables: Dict[str, Any] | None = Field(None, description="模板变量")
    model_info: Optional[ModelInfo] = Field(None, description="模型和提供商信息")

class AdvancedPromptResponse(BaseModel):
    final_prompt: str
    initial_prompt: str
    refined_prompts: List[str] | None = None
    evaluation_reports: List[Any] | None = None
    message: str | None = None

class ErrorResponse(BaseModel):
    detail: str

class SystemInfoResponse(BaseModel):
    active_llm_provider: str
    model_name: str
    available_providers: List[str]
    version: str = "0.1.0"
    structured_templates: List[str] | None = None
    available_models: List[Dict[str, Any]] | None = None

# 添加一个辅助函数，用于从ModelInfo创建代理
def get_agent(model_info: Optional[ModelInfo] = None):
    """
    从模型信息创建Agent
    
    Args:
        model_info: 可选的模型信息
        
    Returns:
        返回一个Agent类，能够生成提示
    """
    class Agent:
        def __init__(self, model_override=None, provider_override=None):
            self.model_override = model_override
            self.provider_override = provider_override
            logger.info(f"创建Agent: model_override={model_override}, provider_override={provider_override}")
            
        async def generate_p1_prompt(self, raw_request, task_type):
            """生成简单的P1提示"""
            logger.info(f"Agent开始生成P1提示: {raw_request[:50]}..., 任务类型: {task_type}")
            result = await generate_and_refine_prompt(
                user_raw_request=raw_request, 
                task_type=task_type, 
                enable_self_correction=False, 
                max_recursion_depth=0,
                model_override=self.model_override,
                provider_override=self.provider_override
            )
            
            if result.get("error_message"):
                raise Exception(result.get("error_message"))
                
            return result.get("p1_initial_optimized_prompt", "")
            
        async def generate_advanced_prompt(self, raw_request, task_type, enable_self_correction=True, max_recursion_depth=2, template_name=None, template_variables=None):
            """生成高级提示，支持自我校正"""
            logger.info(f"Agent开始生成高级提示: {raw_request[:50]}..., 任务类型: {task_type}, 自我校正: {enable_self_correction}, 递归深度: {max_recursion_depth}")
            result = await generate_and_refine_prompt(
                user_raw_request=raw_request, 
                task_type=task_type, 
                enable_self_correction=enable_self_correction, 
                max_recursion_depth=max_recursion_depth,
                use_structured_template_name=template_name,
                structured_template_vars=template_variables,
                model_override=self.model_override,
                provider_override=self.provider_override
            )
            
            if result.get("error_message"):
                raise Exception(result.get("error_message"))
                
            return result
            
        async def explain_term_in_prompt(self, term_to_explain, context_prompt):
            """解释提示中的特定术语"""
            logger.info(f"Agent开始解释术语: {term_to_explain}, 上下文长度: {len(context_prompt)}")
            return await explain_term_in_prompt(
                term_to_explain=term_to_explain,
                context_prompt=context_prompt,
                model_override=self.model_override,
                provider_override=self.provider_override
            )
    
    # 获取模型和提供商覆盖
    model_override = None
    provider_override = None
    
    if model_info:
        if model_info.model and model_info.model != "default":
            model_override = model_info.model
            logger.info(f"使用指定模型: {model_override}")
            
        if model_info.provider:
            provider_override = model_info.provider
            logger.info(f"使用指定提供商: {provider_override}")
    
    return Agent(model_override, provider_override)

@app.get("/", tags=["General"])
async def read_root():
    logger.info("访问了根端点 /")
    return {"message": "欢迎使用 Meta-Prompt Agent API!"}

@app.get(
    "/system/info",
    response_model=SystemInfoResponse,
    tags=["System"],
    summary="获取系统信息",
)
async def get_system_info(settings: dict = Depends(get_api_settings)):
    """获取API系统信息，包括活跃的LLM提供商、可用提供商和版本信息。"""
    from meta_prompt_agent.core.llm.factory import LLMClientFactory
    from meta_prompt_agent.prompts.templates import STRUCTURED_PROMPT_TEMPLATES

    try:
        active_provider = settings["ACTIVE_LLM_PROVIDER"]
        default_llm_client = LLMClientFactory.create(active_provider)
        default_model_name = default_llm_client.model_name

        available_providers_from_factory = list(LLMClientFactory._clients.keys())
        # If "ollama" is still in available_providers_from_factory but we removed its config,
        # it might lead to issues if selected. Consider filtering it out here if not fully removed from factory.
        # For now, we assume if it's in factory, its client can handle missing specific ollama settings.
        
        structured_template_names = list(STRUCTURED_PROMPT_TEMPLATES.keys()) if STRUCTURED_PROMPT_TEMPLATES else []

        all_available_models: List[Dict[str, Any]] = []

        cloud_provider_definitions = {
            "gemini": [
                {"name": "Gemini 2.0 Flash", "value": "gemini-2.0-flash", "provider": "gemini", "group": "Gemini模型"},
                {"name": "Gemini 2.5 Flash", "value": "gemini-2.5-flash-preview-05-20", "provider": "gemini", "group": "Gemini模型"}
            ],
            "qwen": [
                {"name": "通义千问-Max (qwen-max)", "value": "qwen-max", "provider": "qwen", "group": "通义千问 (API)"},
                {"name": "通义千问-Plus (qwen-plus)", "value": "qwen-plus", "provider": "qwen", "group": "通义千问 (API)"},
                {"name": "通义千问-Turbo (qwen-turbo)", "value": "qwen-turbo", "provider": "qwen", "group": "通义千问 (API)"},
                {"name": "通义千问-Plus (qwen-plus-2025-04-28)", "value": "qwen-plus-2025-04-28", "provider": "qwen", "group": "通义千问 (API)"}
            ],
            "openai": [
                {"name": "GPT-4", "value": "gpt-4", "provider": "openai", "group": "OpenAI模型"},
                {"name": "GPT-4 Turbo", "value": "gpt-4-turbo", "provider": "openai", "group": "OpenAI模型"}
            ],
            "anthropic": [
                {"name": "Claude 3 Opus", "value": "claude-3-opus", "provider": "anthropic", "group": "Claude模型"},
                {"name": "Claude 3 Sonnet", "value": "claude-3-sonnet", "provider": "anthropic", "group": "Claude模型"}
            ]
        }

        for provider_id, models in cloud_provider_definitions.items():
            if provider_id in available_providers_from_factory:
                all_available_models.extend(models)

        # Ollama models are no longer fetched or added here
        # if "ollama" in available_providers_from_factory:
        #     ollama_models_list = get_ollama_models() # This function is removed from settings
        #     if ollama_models_list:
        #         all_available_models.extend(ollama_models_list)
        #     elif IS_DEV_ENV:
        #         logger.info("Ollama provider might be in factory, but get_ollama_models is removed or returned no models.")

        return SystemInfoResponse(
            active_llm_provider=active_provider,
            model_name=default_model_name,
            available_providers=available_providers_from_factory,
            structured_templates=structured_template_names,
            available_models=all_available_models
        )
    except Exception as e:
        logger.exception(f"获取系统信息时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")

@app.get(
    "/system/current-model",
    tags=["System"],
    summary="获取当前使用的模型信息",
)
async def get_current_model_info(settings: dict = Depends(get_api_settings)):
    """获取当前正在使用的模型和提供商信息"""
    from meta_prompt_agent.core.llm.factory import LLMClientFactory
    
    try:
        active_provider = settings["ACTIVE_LLM_PROVIDER"]
        llm_client = LLMClientFactory.create(active_provider)
        model_name = llm_client.model_name
        
        return {
            "provider": active_provider,
            "model_name": model_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception(f"获取当前模型信息时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取当前模型信息失败: {str(e)}")

@app.post(
    "/generate-simple-p1",
    response_model=P1Response,
    tags=["Prompt Generation"],
    summary="生成初步优化提示 (P1)",
    responses={
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def generate_simple_p1_endpoint(request_data: UserRequest):
    logger.info(f"收到生成P1的请求: {request_data.raw_request[:50]}..., 任务类型: {request_data.task_type}, 模型信息: {request_data.model_info}")
    try:
        agent = get_agent(request_data.model_info)
        p1_prompt = await agent.generate_p1_prompt(request_data.raw_request, request_data.task_type)

        logger.info(f"成功为请求 '{request_data.raw_request[:50]}...' 生成P1提示。")
        return P1Response(
            p1_prompt=p1_prompt,
            original_request=request_data.raw_request,
            message="P1提示已成功生成。"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"处理 /generate-simple-p1 请求时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/generate-advanced-prompt",
    response_model=AdvancedPromptResponse,
    tags=["Prompt Generation"],
    summary="生成高级优化提示，支持自我校正和模板",
    responses={
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def generate_advanced_prompt_endpoint(request_data: AdvancedPromptRequest):
    logger.info(
        f"收到生成高级提示的请求: {request_data.raw_request[:50]}..., "
        f"任务类型: {request_data.task_type}, 自我校正: {request_data.enable_self_correction}, "
        f"最大递归深度: {request_data.max_recursion_depth}, 模板: {request_data.template_name}, 模型信息: {request_data.model_info}"
    )
    try:
        agent = get_agent(request_data.model_info)
        results = await agent.generate_advanced_prompt(
            request_data.raw_request, request_data.task_type,
            request_data.enable_self_correction, request_data.max_recursion_depth,
            request_data.template_name, request_data.template_variables
        )

        final_prompt = results.get("final_prompt")
        initial_prompt = results.get("p1_initial_optimized_prompt")

        if not final_prompt:
            logger.error("generate_and_refine_prompt 返回成功但 final_prompt 为空。")
            raise HTTPException(status_code=500, detail="无法生成高级提示，未知错误。")
        if not initial_prompt:
             logger.warning("generate_and_refine_prompt 返回成功但 p1_initial_optimized_prompt 为空 for advanced gen.")
             initial_prompt = "Initial prompt not recorded."


        logger.info(f"成功为请求 '{request_data.raw_request[:50]}...' 生成高级提示。")
        return AdvancedPromptResponse(
            final_prompt=final_prompt,
            initial_prompt=initial_prompt,
            refined_prompts=results.get("refined_prompts", []),
            evaluation_reports=results.get("evaluation_reports", []),
            message="高级提示已成功生成。"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"处理 /generate-advanced-prompt 请求时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/explain-term",
    response_model=ExplanationResponse,
    tags=["AI Utilities"],
    summary="解释提示词中的特定术语",
    responses={
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def explain_term_endpoint(request_data: ExplainTermRequest):
    logger.info(f"收到解释术语的请求: '{request_data.term_to_explain}', 上下文长度: {len(request_data.context_prompt)}, 模型信息: {request_data.model_info}")
    try:
        agent = get_agent(request_data.model_info)
        explanation_text, error_details_tuple = await agent.explain_term_in_prompt(
            request_data.term_to_explain, request_data.context_prompt
        )

        if error_details_tuple:
            logger.error(f"解释术语 '{request_data.term_to_explain}' 时发生错误: {explanation_text}, 详情: {error_details_tuple}")
            status_code = 400 if error_details_tuple.get("type") == "InputValidationError" else 500
            raise HTTPException(
                status_code=status_code,
                detail=str(explanation_text)
            )

        logger.info(f"成功解释术语 '{request_data.term_to_explain}'。")
        return ExplanationResponse(
            explanation=explanation_text,
            term=request_data.term_to_explain,
            message="术语已成功解释。"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"处理 /explain-term 请求时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/feedback/submit",
    response_model=FeedbackResponse,
    tags=["Feedback"],
    summary="提交用户反馈",
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def submit_feedback(feedback_data: FeedbackItem):
    logger.info(f"收到反馈提交: prompt_id={feedback_data.prompt_id}, rating={feedback_data.rating}")
    try:
        all_feedback = load_feedback()
        feedback_dict = feedback_data.model_dump()
        if isinstance(feedback_dict["timestamp"], datetime):
            feedback_dict["timestamp"] = feedback_dict["timestamp"].isoformat()

        all_feedback.append(feedback_dict)
        success = save_feedback(all_feedback)

        if not success:
            logger.error("保存反馈数据失败")
            raise HTTPException(status_code=500, detail="无法保存反馈数据")

        logger.info(f"成功保存反馈: prompt_id={feedback_data.prompt_id}")
        return FeedbackResponse(
            success=True,
            message="反馈已成功提交",
            feedback_id=feedback_data.prompt_id
        )
    except Exception as e:
        logger.exception(f"提交反馈时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"提交反馈时发生错误: {str(e)}")

@app.get(
    "/feedback/list",
    response_model=FeedbackListResponse,
    tags=["Feedback"],
    summary="获取反馈列表",
    responses={
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def list_feedback(
    limit: int = Query(20, ge=1, le=100, description="要返回的反馈项数量"),
    offset: int = Query(0, ge=0, description="分页起始位置"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="最低评分过滤")
):
    logger.info(f"收到反馈列表请求: limit={limit}, offset={offset}, min_rating={min_rating}")
    try:
        all_feedback = load_feedback()
        if min_rating is not None:
            all_feedback = [fb for fb in all_feedback if fb.get("rating", 0) >= min_rating]

        total_count = len(all_feedback)
        paginated_feedback = all_feedback[offset:offset + limit]
        feedback_items = []
        for fb_dict in paginated_feedback:
            if isinstance(fb_dict.get("timestamp"), str):
                try:
                    fb_dict["timestamp"] = datetime.fromisoformat(fb_dict["timestamp"])
                except ValueError:
                    fb_dict["timestamp"] = datetime.now()
            elif not isinstance(fb_dict.get("timestamp"), datetime):
                 fb_dict["timestamp"] = datetime.now()

            feedback_items.append(FeedbackItem(**fb_dict))

        logger.info(f"成功检索 {len(feedback_items)} 条反馈 (总计 {total_count} 条)")
        return FeedbackListResponse(
            feedback_items=feedback_items,
            total_count=total_count
        )
    except Exception as e:
        logger.exception(f"获取反馈列表时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取反馈列表时发生错误: {str(e)}")

# --- 交互式会话API的Pydantic模型 ---
class SessionCreateRequest(BaseModel):
    """创建交互式会话的请求模型"""
    raw_request: str = Field(..., min_length=1, description="用户的原始文本请求")
    task_type: str = Field(default="通用/问答", description="任务类型")
    model_info: Optional[ModelInfo] = Field(None, description="模型和提供商信息")
    template_name: Optional[str] = Field(None, description="结构化模板名称")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="模板变量")
    max_recursion_depth: int = Field(default=3, ge=1, le=5, description="最大递归深度")

class SessionResponse(BaseModel):
    """会话响应的基础模型"""
    session_id: str
    stage: str
    message: Optional[str] = None
    error: Optional[str] = None

class UserPromptUpdate(BaseModel):
    """用户对提示词的修改请求"""
    updated_prompt: str = Field(..., min_length=1, description="用户修改后的提示词")
    stage: Literal["p1", "current", "final"] = Field(default="current", description="要修改的提示词阶段")
    comments: Optional[str] = Field(None, description="用户对修改的说明")

class PromptGenerationResponse(BaseModel):
    """提示词生成响应"""
    session_id: str
    stage: str
    prompt: str
    original_request: str
    message: Optional[str] = None
    error: Optional[str] = None

class EvaluationResponse(BaseModel):
    """评估报告响应"""
    session_id: str
    stage: str
    prompt: str
    evaluation_report: Any
    message: Optional[str] = None
    error: Optional[str] = None

class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[Dict[str, Any]]
    total_count: int
    
class SessionDetailResponse(BaseModel):
    """会话详情响应"""
    session_id: str
    user_raw_request: str
    task_type: str
    stage: str
    created_at: str
    last_updated: str
    p1_prompt: str
    evaluation_reports: List[Any]
    refined_prompts: List[str]
    current_prompt: str
    final_prompt: str
    model_override: Optional[str]
    provider_override: Optional[str]
    conversation_history: List[Dict[str, str]]
    user_modifications: List[Dict[str, Any]]
    error: Optional[Dict[str, Any]] = None

# --- 交互式会话API端点 ---
@app.post(
    "/sessions",
    response_model=SessionResponse,
    tags=["Interactive Sessions"],
    summary="创建新的交互式会话",
    responses={
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def create_session_endpoint(request_data: SessionCreateRequest):
    """创建新的交互式提示词生成会话"""
    logger.info(f"收到创建会话请求: {request_data.raw_request[:50]}..., 任务类型: {request_data.task_type}")
    
    try:
        # 获取模型和提供商
        model_override = None
        provider_override = None
        
        if request_data.model_info:
            if request_data.model_info.model and request_data.model_info.model != "default":
                model_override = request_data.model_info.model
            if request_data.model_info.provider:
                provider_override = request_data.model_info.provider
        
        # 创建会话
        session, error = await create_interactive_session(
            user_raw_request=request_data.raw_request,
            task_type=request_data.task_type,
            model_override=model_override,
            provider_override=provider_override,
            template_name=request_data.template_name,
            template_variables=request_data.template_variables,
            max_recursion_depth=request_data.max_recursion_depth
        )
        
        if error:
            logger.error(f"创建会话失败: {error}")
            raise HTTPException(status_code=500, detail=f"创建会话失败: {error.get('message', '未知错误')}")
        
        logger.info(f"成功创建会话: {session.session_id}")
        return SessionResponse(
            session_id=session.session_id,
            stage=session.stage,
            message="会话创建成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"创建会话时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/sessions/{session_id}/generate-p1",
    response_model=PromptGenerationResponse,
    tags=["Interactive Sessions"],
    summary="为会话生成初步P1提示词",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def generate_p1_for_session_endpoint(session_id: str):
    """为指定会话生成初步提示词 (P1)"""
    logger.info(f"收到为会话 {session_id} 生成P1提示词的请求")
    
    try:
        # 生成P1提示词
        session, error = await generate_p1_prompt_for_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        if error and error.get("type") != "InvalidStage":
            logger.error(f"生成P1提示词失败: {error}")
            return PromptGenerationResponse(
                session_id=session_id,
                stage=session.stage,
                prompt=session.p1_prompt or "",
                original_request=session.user_raw_request,
                error=error.get("message", "生成P1提示词失败")
            )
        
        logger.info(f"成功为会话 {session_id} 生成P1提示词")
        return PromptGenerationResponse(
            session_id=session_id,
            stage=session.stage,
            prompt=session.p1_prompt,
            original_request=session.user_raw_request,
            message="P1提示词已成功生成"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"生成P1提示词时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/sessions/{session_id}/evaluate",
    response_model=EvaluationResponse,
    tags=["Interactive Sessions"],
    summary="评估会话中的当前提示词",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def evaluate_prompt_for_session_endpoint(session_id: str):
    """评估指定会话的当前提示词"""
    logger.info(f"收到评估会话 {session_id} 当前提示词的请求")
    
    try:
        # 评估提示词
        session, error = await evaluate_prompt_for_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        if error and error.get("type") not in ["InvalidStage"]:
            logger.error(f"评估提示词失败: {error}")
            return EvaluationResponse(
                session_id=session_id,
                stage=session.stage,
                prompt=session.current_prompt or "",
                evaluation_report=session.current_evaluation or {},
                error=error.get("message", "评估提示词失败")
            )
        
        logger.info(f"成功评估会话 {session_id} 的当前提示词")
        return EvaluationResponse(
            session_id=session_id,
            stage=session.stage,
            prompt=session.current_prompt,
            evaluation_report=session.current_evaluation or session.evaluation_reports[-1] if session.evaluation_reports else {},
            message="提示词评估已完成"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"评估提示词时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/sessions/{session_id}/refine",
    response_model=PromptGenerationResponse,
    tags=["Interactive Sessions"],
    summary="优化会话中的当前提示词",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def refine_prompt_for_session_endpoint(session_id: str):
    """优化指定会话的当前提示词"""
    logger.info(f"收到优化会话 {session_id} 当前提示词的请求")
    
    try:
        # 优化提示词
        session, error = await refine_prompt_for_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        if error and error.get("type") not in ["InvalidStage", "MaxDepthReached"]:
            logger.error(f"优化提示词失败: {error}")
            return PromptGenerationResponse(
                session_id=session_id,
                stage=session.stage,
                prompt=session.current_prompt or "",
                original_request=session.user_raw_request,
                error=error.get("message", "优化提示词失败")
            )
        
        logger.info(f"成功优化会话 {session_id} 的当前提示词")
        return PromptGenerationResponse(
            session_id=session_id,
            stage=session.stage,
            prompt=session.current_prompt,
            original_request=session.user_raw_request,
            message="提示词优化已完成" + (" (已达到最大递归深度)" if error and error.get("type") == "MaxDepthReached" else "")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"优化提示词时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/sessions/{session_id}/complete",
    response_model=PromptGenerationResponse,
    tags=["Interactive Sessions"],
    summary="完成会话，将当前提示词标记为最终提示词",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def complete_session_endpoint(session_id: str):
    """完成指定会话，将当前提示词标记为最终提示词"""
    logger.info(f"收到完成会话 {session_id} 的请求")
    
    try:
        # 完成会话
        session, error = await complete_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        if error:
            logger.error(f"完成会话失败: {error}")
            return PromptGenerationResponse(
                session_id=session_id,
                stage=session.stage,
                prompt=session.current_prompt or "",
                original_request=session.user_raw_request,
                error=error.get("message", "完成会话失败")
            )
        
        logger.info(f"成功完成会话 {session_id}")
        return PromptGenerationResponse(
            session_id=session_id,
            stage=session.stage,
            prompt=session.final_prompt,
            original_request=session.user_raw_request,
            message="会话已完成，最终提示词已设置"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"完成会话时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/sessions/{session_id}/user-update",
    response_model=PromptGenerationResponse,
    tags=["Interactive Sessions"],
    summary="用户修改会话中的提示词",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        422: {"model": ErrorResponse, "description": "请求体验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def update_prompt_by_user_endpoint(session_id: str, update_data: UserPromptUpdate):
    """用户修改指定会话中的提示词"""
    logger.info(f"收到用户修改会话 {session_id} 提示词的请求，阶段: {update_data.stage}")
    
    try:
        # 用户修改提示词
        session, error = await update_prompt_by_user(
            session_id=session_id,
            updated_prompt=update_data.updated_prompt,
            stage=update_data.stage,
            comments=update_data.comments
        )
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        if error:
            logger.error(f"用户修改提示词失败: {error}")
            return PromptGenerationResponse(
                session_id=session_id,
                stage=session.stage,
                prompt=session.current_prompt or "",
                original_request=session.user_raw_request,
                error=error.get("message", "用户修改提示词失败")
            )
        
        logger.info(f"用户成功修改会话 {session_id} 的提示词")
        return PromptGenerationResponse(
            session_id=session_id,
            stage=session.stage,
            prompt=session.current_prompt,
            original_request=session.user_raw_request,
            message=f"提示词已成功修改 (阶段: {update_data.stage})"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"用户修改提示词时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.get(
    "/sessions",
    response_model=SessionListResponse,
    tags=["Interactive Sessions"],
    summary="获取会话列表",
    responses={
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def list_sessions_endpoint(
    limit: int = Query(20, ge=1, le=100, description="要返回的会话数量"),
    offset: int = Query(0, ge=0, description="分页起始位置")
):
    """获取会话列表"""
    logger.info(f"收到获取会话列表请求: limit={limit}, offset={offset}")
    
    try:
        # 获取会话管理器
        session_manager = get_session_manager()
        
        # 获取会话列表
        sessions = await session_manager.list_sessions(limit=limit, offset=offset)
        
        logger.info(f"成功获取 {len(sessions)} 个会话")
        return SessionListResponse(
            sessions=sessions,
            total_count=len(sessions)  # 这里是简化实现，实际中可能需要单独查询总数
        )
    
    except Exception as e:
        logger.exception(f"获取会话列表时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    tags=["Interactive Sessions"],
    summary="获取会话详情",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def get_session_endpoint(session_id: str):
    """获取指定会话的详细信息"""
    logger.info(f"收到获取会话 {session_id} 详情的请求")
    
    try:
        # 获取会话管理器
        session_manager = get_session_manager()
        
        # 获取会话
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        # 构造响应
        response_data = {
            "session_id": session.session_id,
            "user_raw_request": session.user_raw_request,
            "task_type": session.task_type,
            "stage": session.stage,
            "created_at": session.created_at,
            "last_updated": session.last_updated,
            "p1_prompt": session.p1_prompt,
            "evaluation_reports": session.evaluation_reports,
            "refined_prompts": session.refined_prompts,
            "current_prompt": session.current_prompt,
            "final_prompt": session.final_prompt,
            "model_override": session.model_override,
            "provider_override": session.provider_override,
            "conversation_history": session.conversation_history,
            "user_modifications": session.user_modifications
        }
        
        if session.last_error:
            response_data["error"] = {
                "message": session.last_error,
                "stage": session.error_stage
            }
        
        logger.info(f"成功获取会话 {session_id} 详情")
        return SessionDetailResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取会话详情时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.delete(
    "/sessions/{session_id}",
    response_model=Dict[str, Any],
    tags=["Interactive Sessions"],
    summary="删除会话",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def delete_session_endpoint(session_id: str):
    """删除指定会话"""
    logger.info(f"收到删除会话 {session_id} 的请求")
    
    try:
        # 获取会话管理器
        session_manager = get_session_manager()
        
        # 删除会话
        success = await session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或删除失败")
        
        logger.info(f"成功删除会话 {session_id}")
        return {
            "success": True,
            "message": f"会话 {session_id} 已成功删除"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"删除会话时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

@app.post(
    "/sessions/{session_id}/auto-process",
    response_model=PromptGenerationResponse,
    tags=["Interactive Sessions"],
    summary="自动处理会话直到完成",
    responses={
        404: {"model": ErrorResponse, "description": "会话不存在"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def auto_process_session_endpoint(session_id: str):
    """自动处理会话，执行完整流程直到完成"""
    logger.info(f"收到自动处理会话 {session_id} 的请求")
    
    try:
        # 获取会话管理器
        session_manager = get_session_manager()
        
        # 获取会话
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        # 根据当前阶段自动处理
        if session.stage == SessionStage.CREATED:
            # 生成P1提示词
            session, error = await generate_p1_prompt_for_session(session_id)
            if error and error.get("type") != "InvalidStage":
                raise HTTPException(status_code=500, detail=f"生成P1提示词失败: {error.get('message', '未知错误')}")
        
        # 评估与优化循环
        max_iterations = session.max_recursion_depth
        current_iterations = 0
        
        while session.stage != SessionStage.COMPLETED and current_iterations < max_iterations:
            if session.stage == SessionStage.P1_GENERATED or session.stage == SessionStage.REFINEMENT_COMPLETE:
                # 评估当前提示词
                session, error = await evaluate_prompt_for_session(session_id)
                if error and error.get("type") != "InvalidStage":
                    raise HTTPException(status_code=500, detail=f"评估提示词失败: {error.get('message', '未知错误')}")
            
            if session.stage == SessionStage.EVALUATION_COMPLETE:
                # 优化当前提示词
                session, error = await refine_prompt_for_session(session_id)
                if error and error.get("type") not in ["InvalidStage", "MaxDepthReached"]:
                    raise HTTPException(status_code=500, detail=f"优化提示词失败: {error.get('message', '未知错误')}")
                
                # 如果达到最大深度或优化停止，完成会话
                if error and error.get("type") == "MaxDepthReached":
                    break
            
            current_iterations += 1
        
        # 完成会话
        session, error = await complete_session(session_id)
        if error:
            logger.warning(f"完成会话失败: {error}")
        
        logger.info(f"成功自动处理会话 {session_id}")
        return PromptGenerationResponse(
            session_id=session_id,
            stage=session.stage,
            prompt=session.final_prompt or session.current_prompt or "",
            original_request=session.user_raw_request,
            message=f"会话已自动处理完成，执行了 {current_iterations} 轮迭代"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"自动处理会话时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

# 定时任务端点
@app.post(
    "/system/clean-expired-sessions",
    tags=["System"],
    summary="清理过期会话",
    responses={
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def clean_expired_sessions_endpoint():
    """清理过期的会话"""
    logger.info("收到清理过期会话的请求")
    
    try:
        # 获取会话管理器
        session_manager = get_session_manager()
        
        # 清理过期会话
        cleaned_count = await session_manager.clean_expired_sessions()
        
        logger.info(f"成功清理 {cleaned_count} 个过期会话")
        return {
            "success": True,
            "message": f"已清理 {cleaned_count} 个过期会话",
            "cleaned_count": cleaned_count
        }
    
    except Exception as e:
        logger.exception(f"清理过期会话时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")

if __name__ == "__main__":
    if 'setup_logging' in globals() and callable(setup_logging):
       setup_logging(logging.INFO)
    else:
       logging.basicConfig(level=logging.INFO)
       logger.info("使用基础日志配置运行 (直接运行 main.py)。")

    logger.info("尝试直接运行 FastAPI 应用 (用于本地测试，生产环境请使用 Uvicorn)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)




