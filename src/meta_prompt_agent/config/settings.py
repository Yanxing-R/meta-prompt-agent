# src/meta_prompt_agent/config/settings.py
import os
import platform
import subprocess
import json
from dotenv import load_dotenv
from functools import lru_cache
from typing import Dict, Any, Optional, List

load_dotenv()

# --- 环境检测 ---
# 是否在开发环境中运行
IS_DEV_ENV = os.getenv("META_PROMPT_ENV", "dev").lower() == "dev"

# 在控制台输出当前环境状态
print(f"当前环境: {'开发环境' if IS_DEV_ENV else '生产环境'}")
print(f"OLLAMA_API_URL: {os.getenv('OLLAMA_API_URL', 'http://localhost:11434')}")
print(f"ACTIVE_LLM_PROVIDER: {os.getenv('ACTIVE_LLM_PROVIDER', 'qwen').lower()}")

# --- Ollama 配置 ---
# 只保留配置，但默认不使用
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

# --- Gemini API 配置 ---
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest") 

# --- 通义千问 (Qwen) API 配置 ---
# DashScope SDK 优先查找 DASHSCOPE_API_KEY
# 我们也允许通过 QWEN_API_KEY 设置，但在 .env 中推荐使用 DASHSCOPE_API_KEY
QWEN_API_KEY_FROM_ENV: str | None = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
QWEN_MODEL_NAME: str = os.getenv("QWEN_MODEL_NAME", "qwen3-4b") # 默认使用青云3-4B模型

# --- 当前激活的LLM服务提供者 ---
ACTIVE_LLM_PROVIDER: str = os.getenv("ACTIVE_LLM_PROVIDER", "qwen").lower()

# --- 其他应用配置 ---
FEEDBACK_FILE: str = "user_feedback.json"

# --- 获取本地Ollama模型列表 ---
def get_ollama_models() -> List[Dict[str, str]]:
    """
    获取本地Ollama可用模型列表，仅在开发环境中调用
    
    Returns:
        List[Dict[str, str]]: 模型列表，每个模型包含名称、ID、提供商和分组信息
    """
    # 为安全起见，总是检查是否在开发环境
    if not IS_DEV_ENV:
        print("非开发环境，跳过获取Ollama模型")
        return []
        
    try:
        print("尝试获取本地Ollama模型...")
        # 判断操作系统类型
        system = platform.system().lower()
        cmd = ["ollama", "list"]
        
        try:
            # 执行命令获取模型列表
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout
            
            # 解析输出结果
            lines = output.strip().split('\n')
            if len(lines) <= 1:  # 只有标题行或无输出
                print("Ollama未返回任何模型")
                return []
                
            print(f"Ollama返回了 {len(lines)-1} 个模型")
            
            # 跳过标题行，处理数据行
            models = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    model_name = parts[0]
                    model_id = parts[1]
                    
                    # 识别模型系列并添加分组信息
                    provider = "ollama"
                    
                    if "qwen" in model_name.lower():
                        group = "Qwen系列"
                        display_name = f"Ollama-{model_name}"
                    elif "llama" in model_name.lower():
                        group = "Llama系列"
                        display_name = f"Ollama-{model_name}"
                    elif "gemma" in model_name.lower():
                        group = "Gemma系列"
                        display_name = f"Ollama-{model_name}"
                    elif "phi" in model_name.lower():
                        group = "Phi系列"
                        display_name = f"Ollama-{model_name}"
                    elif "deepseek" in model_name.lower() or "deepcoder" in model_name.lower():
                        group = "DeepSeek系列"
                        display_name = f"Ollama-{model_name}"
                    else:
                        group = "其他模型"
                        display_name = f"Ollama-{model_name}"
                    
                    models.append({
                        "name": display_name,
                        "value": model_name,
                        "id": model_id,
                        "provider": provider,
                        "group": group
                    })
                    print(f"添加Ollama模型: {display_name} ({model_name})")
            
            return models
        except subprocess.CalledProcessError as e:
            print(f"执行Ollama命令失败: {e}")
            return []
    except Exception as e:
        print(f"获取Ollama模型列表失败: {e}")
        return []

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
        "IS_DEV_ENV": IS_DEV_ENV,
        
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



