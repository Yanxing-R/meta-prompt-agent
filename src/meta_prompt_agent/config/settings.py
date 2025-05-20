# src/meta_prompt_agent/config/settings.py
import os
from dotenv import load_dotenv
from functools import lru_cache
from typing import Dict, Any, Optional

load_dotenv()

# --- Ollama 配置 ---
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")

# --- Gemini API 配置 ---
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest") 

# --- 通义千问 (Qwen) API 配置 ---
# DashScope SDK 优先查找 DASHSCOPE_API_KEY
# 我们也允许通过 QWEN_API_KEY 设置，但在 .env 中推荐使用 DASHSCOPE_API_KEY
QWEN_API_KEY_FROM_ENV: str | None = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
QWEN_MODEL_NAME: str = os.getenv("QWEN_MODEL_NAME", "qwen-plus-2025-04-28") # 您指定的模型

# --- 当前激活的LLM服务提供者 ---
ACTIVE_LLM_PROVIDER: str = os.getenv("ACTIVE_LLM_PROVIDER", "qwen").lower()

# --- 其他应用配置 ---
FEEDBACK_FILE: str = "user_feedback.json"

# --- 应用配置获取函数 ---
@lru_cache()
def get_settings() -> Dict[str, Any]:
    """
    获取应用配置。使用缓存确保整个应用程序中使用相同的配置实例。
    
    Returns:
        Dict[str, Any]: 包含所有配置项的字典
    """
    return {
        # 系统配置
        "ACTIVE_LLM_PROVIDER": ACTIVE_LLM_PROVIDER,
        
        # Ollama配置
        "OLLAMA_MODEL": OLLAMA_MODEL,
        "OLLAMA_API_URL": OLLAMA_API_URL,
        
        # Gemini配置
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "GEMINI_MODEL_NAME": GEMINI_MODEL_NAME,
        
        # 通义千问配置
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
        "QWEN_API_KEY": os.getenv("QWEN_API_KEY"),
        "QWEN_API_KEY_FROM_ENV": QWEN_API_KEY_FROM_ENV,
        "QWEN_MODEL_NAME": QWEN_MODEL_NAME,
        
        # 其他应用配置
        "FEEDBACK_FILE": FEEDBACK_FILE,
    }

def check_configurations():
    provider = ACTIVE_LLM_PROVIDER
    if provider == "gemini" and not GEMINI_API_KEY:
        raise ValueError("错误：ACTIVE_LLM_PROVIDER 设置为 'gemini'，但 GEMINI_API_KEY 未配置。")
    elif provider == "qwen" and not QWEN_API_KEY_FROM_ENV: # 使用新的合并变量检查
        raise ValueError(
            "错误：ACTIVE_LLM_PROVIDER 设置为 'qwen'，但 DASHSCOPE_API_KEY (或 QWEN_API_KEY) 未在 .env 文件中设置。"
        )
    
    if provider == "qwen":
        print(
            f"提示：ACTIVE_LLM_PROVIDER 设置为 'qwen'，将使用模型 '{QWEN_MODEL_NAME}'。"
            f"请确保 DASHSCOPE_API_KEY (或 QWEN_API_KEY) 已正确配置且模型名称有效。"
        )

if __name__ == '__main__':
    print(f"Ollama Model: {OLLAMA_MODEL}")
    print(f"Gemini API Key Loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
    print(f"Gemini Model Name: {GEMINI_MODEL_NAME}")
    print(f"Qwen/DashScope API Key Loaded (from DASHSCOPE_API_KEY or QWEN_API_KEY): {'Yes' if QWEN_API_KEY_FROM_ENV else 'No'}")
    print(f"Qwen Model Name: {QWEN_MODEL_NAME}")
    print(f"Active LLM Provider: {ACTIVE_LLM_PROVIDER}")
    try:
        check_configurations()
        print("配置检查通过。")
    except ValueError as e:
        print(f"配置检查失败: {e}")



