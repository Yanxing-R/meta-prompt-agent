# src/meta_prompt_agent/api/main.py
import logging
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from meta_prompt_agent.core.agent import generate_and_refine_prompt, explain_term_in_prompt, load_feedback, save_feedback
    from meta_prompt_agent.config.logging_config import setup_logging
    # Ollama specific imports (get_ollama_models) are removed
    from meta_prompt_agent.config.settings import get_settings, IS_DEV_ENV # IS_DEV_ENV might still be useful for other dev-specific logic
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
    def custom_openapi_schema(app): # type: ignore
        def custom_openapi(): return {}
        return custom_openapi
    def get_settings(): return {"ACTIVE_LLM_PROVIDER": "default"} # type: ignore
    IS_DEV_ENV = False # type: ignore
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
                {"name": "Gemini 1.5 Pro", "value": "gemini-1.5-pro", "provider": "gemini", "group": "Gemini模型"},
                {"name": "Gemini 1.5 Flash", "value": "gemini-1.5-flash", "provider": "gemini", "group": "Gemini模型"},
                {"name": "Gemini 1.0 Pro", "value": "gemini-1.0-pro", "provider": "gemini", "group": "Gemini模型"}
            ],
            "qwen": [
                {"name": "通义千问-Max (qwen-max)", "value": "qwen-max", "provider": "qwen", "group": "通义千问 (API)"},
                {"name": "通义千问-Plus (qwen-plus)", "value": "qwen-plus", "provider": "qwen", "group": "通义千问 (API)"},
                {"name": "通义千问-Turbo (qwen-turbo)", "value": "qwen-turbo", "provider": "qwen", "group": "通义千问 (API)"},
                {"name": "通义千问-Long (qwen-long)", "value": "qwen-long", "provider": "qwen", "group": "通义千问 (API)"},
                {"name": "通义千问1.5-110B (qwen1.5-110b-chat)", "value": "qwen1.5-110b-chat", "provider": "qwen", "group": "通义千问1.5 (API)"},
                {"name": "通义千问1.5-72B (qwen1.5-72b-chat)", "value": "qwen1.5-72b-chat", "provider": "qwen", "group": "通义千问1.5 (API)"},
                {"name": "通义千问1.5-32B (qwen1.5-32b-chat)", "value": "qwen1.5-32b-chat", "provider": "qwen", "group": "通义千问1.5 (API)"},
                {"name": "通义千问1.5-14B (qwen1.5-14b-chat)", "value": "qwen1.5-14b-chat", "provider": "qwen", "group": "通义千问1.5 (API)"},
                {"name": "通义千问1.5-7B (qwen1.5-7b-chat)", "value": "qwen1.5-7b-chat", "provider": "qwen", "group": "通义千问1.5 (API)"},
                {"name": "通义千问1.5-1.8B (qwen1.5-1.8b-chat)", "value": "qwen1.5-1.8b-chat", "provider": "qwen", "group": "通义千问1.5 (API)"},
                {"name": "通义千问2-72B (qwen2-72b-instruct)", "value": "qwen2-72b-instruct", "provider": "qwen", "group": "通义千问2 (API)"},
                {"name": "通义千问2-57B-A14B (qwen2-57b-a14b-instruct)", "value": "qwen2-57b-a14b-instruct", "provider": "qwen", "group": "通义千问2 (API)"},
                {"name": "通义千问2-7B (qwen2-7b-instruct)", "value": "qwen2-7b-instruct", "provider": "qwen", "group": "通义千问2 (API)"},
                {"name": "通义千问2-1.5B (qwen2-1.5b-instruct)", "value": "qwen2-1.5b-instruct", "provider": "qwen", "group": "通义千问2 (API)"},
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
        if not callable(generate_and_refine_prompt):
             logger.error("核心函数 generate_and_refine_prompt 未成功导入或不可调用。")
             raise HTTPException(status_code=500, detail="服务器内部配置错误: 核心逻辑不可用。")

        model_override = None
        provider_override = None
        if request_data.model_info:
            model_override = request_data.model_info.model
            provider_override = request_data.model_info.provider
            logger.info(f"使用自定义模型: {model_override} (提供商: {provider_override})")

        results = await generate_and_refine_prompt(
            user_raw_request=request_data.raw_request,
            task_type=request_data.task_type,
            enable_self_correction=False,
            max_recursion_depth=0,
            use_structured_template_name=None,
            structured_template_vars=None,
            model_override=model_override,
            provider_override=provider_override
        )

        if results.get("error_message"):
            logger.error(f"生成P1时发生错误: {results.get('error_message')}, 详情: {results.get('error_details')}")
            raise HTTPException(
                status_code=500,
                detail=str(results.get('error_message', "生成P1时发生内部错误"))
            )

        p1_prompt = results.get("p1_initial_optimized_prompt")
        if not p1_prompt:
            logger.error("generate_and_refine_prompt 返回成功但 p1_initial_optimized_prompt 为空。")
            raise HTTPException(status_code=500, detail="无法生成P1提示，未知错误。")

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
        if not callable(generate_and_refine_prompt):
            logger.error("核心函数 generate_and_refine_prompt 未成功导入或不可调用。")
            raise HTTPException(status_code=500, detail="服务器内部配置错误: 核心逻辑不可用。")

        model_override = None
        provider_override = None
        if request_data.model_info:
            model_override = request_data.model_info.model
            provider_override = request_data.model_info.provider
            logger.info(f"使用自定义模型: {model_override} (提供商: {provider_override})")

        results = await generate_and_refine_prompt(
            user_raw_request=request_data.raw_request,
            task_type=request_data.task_type,
            enable_self_correction=request_data.enable_self_correction,
            max_recursion_depth=request_data.max_recursion_depth,
            use_structured_template_name=request_data.template_name,
            structured_template_vars=request_data.template_variables,
            model_override=model_override,
            provider_override=provider_override
        )

        if results.get("error_message"):
            logger.error(
                f"生成高级提示时发生错误: {results.get('error_message')}, "
                f"详情: {results.get('error_details')}"
            )
            raise HTTPException(
                status_code=500,
                detail=str(results.get('error_message', "生成高级提示时发生内部错误"))
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
        if not callable(explain_term_in_prompt):
            logger.error("核心函数 explain_term_in_prompt 未成功导入或不可调用。")
            raise HTTPException(status_code=500, detail="服务器内部配置错误: 解释逻辑不可用。")

        model_override = None
        provider_override = None
        if request_data.model_info:
            model_override = request_data.model_info.model
            provider_override = request_data.model_info.provider
            logger.info(f"使用自定义模型: {model_override} (提供商: {provider_override})")

        explanation_text, error_details_tuple = await explain_term_in_prompt(
            term_to_explain=request_data.term_to_explain,
            context_prompt=request_data.context_prompt,
            model_override=model_override,
            provider_override=provider_override
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

if __name__ == "__main__":
    if 'setup_logging' in globals() and callable(setup_logging):
       setup_logging(logging.INFO)
    else:
       logging.basicConfig(level=logging.INFO)
       logger.info("使用基础日志配置运行 (直接运行 main.py)。")

    logger.info("尝试直接运行 FastAPI 应用 (用于本地测试，生产环境请使用 Uvicorn)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)




