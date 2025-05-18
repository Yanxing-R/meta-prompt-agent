# src/meta_prompt_agent/api/main.py
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel, Field 
import uvicorn 
import json 

try:
    from meta_prompt_agent.core.agent import generate_and_refine_prompt, explain_term_in_prompt # 1. 导入 explain_term_in_prompt
    from meta_prompt_agent.config.logging_config import setup_logging 
    # setup_logging() # 考虑在应用启动时配置
except ImportError as e:
    print(f"导入错误: {e}. 请确保PYTHONPATH或运行目录正确。")
    def generate_and_refine_prompt(*args, **kwargs): # type: ignore
        return {"error_message": "核心逻辑(g&r)未正确导入", "p1_initial_optimized_prompt": ""}
    def explain_term_in_prompt(*args, **kwargs): # type: ignore
        return "错误：核心逻辑(explain)未正确导入", {"type": "ImportError", "details": str(e)}
    pass


logger = logging.getLogger(__name__) 

app = FastAPI(
    title="Meta-Prompt Agent API",
    description="提供元提示生成与优化服务的API。",
    version="0.1.0",
)

# --- CORS 配置 ---
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

# --- Pydantic 模型定义 ---
class UserRequest(BaseModel):
    raw_request: str = Field(..., min_length=1, description="用户的原始文本请求")
    task_type: str = Field(default="通用/问答", description="任务类型")

class P1Response(BaseModel):
    p1_prompt: str
    original_request: str
    message: str | None = None

# 2. 为 /explain-term 端点定义新的请求和响应模型
class ExplainTermRequest(BaseModel):
    term_to_explain: str = Field(..., min_length=1, description="需要解释的术语或短语")
    context_prompt: str = Field(..., min_length=1, description="包含该术语的完整提示词上下文")

class ExplanationResponse(BaseModel):
    explanation: str
    term: str
    context_snippet: str | None = None # 可选，返回部分上下文以供参考
    message: str | None = None

class ErrorResponse(BaseModel):
    detail: str

# --- API 端点定义 ---

@app.get("/", tags=["General"])
async def read_root():
    logger.info("访问了根端点 /")
    return {"message": "欢迎使用 Meta-Prompt Agent API!"}

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
    logger.info(f"收到生成P1的请求: {request_data.raw_request[:50]}..., 任务类型: {request_data.task_type}")
    try:
        if 'generate_and_refine_prompt' not in globals() or not callable(generate_and_refine_prompt):
             logger.error("核心函数 generate_and_refine_prompt 未成功导入或不可调用。")
             raise HTTPException(status_code=500, detail="服务器内部配置错误: 核心逻辑不可用。")

        results = generate_and_refine_prompt(
            user_raw_request=request_data.raw_request,
            task_type=request_data.task_type,
            enable_self_correction=False, 
            max_recursion_depth=0,        
            use_structured_template_name=None, 
            structured_template_vars=None
        )

        if results.get("error_message"):
            logger.error(f"生成P1时发生错误: {results.get('error_message')}, 详情: {results.get('error_details')}")
            # error_message已经是 "错误：..." 开头，可以直接作为detail
            raise HTTPException(
                status_code=500, 
                detail=results.get('error_message', "生成P1时发生内部错误") 
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

# 3. 新增 /explain-term API 端点
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
    """
    接收一个术语和其上下文提示，返回对该术语的解释。
    """
    logger.info(f"收到解释术语的请求: '{request_data.term_to_explain}', 上下文长度: {len(request_data.context_prompt)}")
    try:
        if 'explain_term_in_prompt' not in globals() or not callable(explain_term_in_prompt):
            logger.error("核心函数 explain_term_in_prompt 未成功导入或不可调用。")
            raise HTTPException(status_code=500, detail="服务器内部配置错误: 解释逻辑不可用。")

        explanation_text, error_details = explain_term_in_prompt(
            term_to_explain=request_data.term_to_explain,
            context_prompt=request_data.context_prompt
        )

        if error_details:
            # explanation_text 在 agent.explain_term_in_prompt 中已经是 "错误：..." 开头
            logger.error(f"解释术语 '{request_data.term_to_explain}' 时发生错误: {explanation_text}, 详情: {error_details}")
            # 根据错误类型决定状态码，或者统一用500表示内部处理问题
            status_code = 400 if error_details.get("type") == "InputValidationError" else 500
            raise HTTPException(
                status_code=status_code,
                detail=explanation_text # 直接将 agent 返回的错误消息作为 detail
            )
        
        logger.info(f"成功解释术语 '{request_data.term_to_explain}'。")
        return ExplanationResponse(
            explanation=explanation_text,
            term=request_data.term_to_explain,
            # context_snippet=request_data.context_prompt[:100] + "..." # 可选：返回部分上下文
            message="术语已成功解释。"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"处理 /explain-term 请求时发生未预料的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器处理请求时发生意外错误: {str(e)}")


if __name__ == "__main__":
    if 'setup_logging' in globals() and callable(setup_logging):
       setup_logging()
    else:
       logging.basicConfig(level=logging.INFO) 
       logger.info("使用基础日志配置运行 (直接运行 main.py)。")
    
    print("尝试直接运行 FastAPI 应用 (用于本地测试，生产环境请使用 Uvicorn)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)


