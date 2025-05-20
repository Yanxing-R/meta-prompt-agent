#!/usr/bin/env python3
"""
修复模型选择功能脚本
此脚本用于检查前后端模型选择匹配问题，并提供修复建议
"""

import json
import os
import sys
import subprocess
from pprint import pprint

def check_ollama_models():
    """检查本地可用的Ollama模型"""
    print("\n===== 检查Ollama模型 =====")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        output = result.stdout
        
        # 解析输出结果
        lines = output.strip().split('\n')
        if len(lines) <= 1:  # 只有标题行或无输出
            print("未找到Ollama模型")
            return []
            
        # 跳过标题行，处理数据行
        print("\n可用的Ollama模型:")
        models = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                model_name = parts[0]
                model_id = parts[1]
                print(f"  - {model_name} (ID: {model_id})")
                models.append({"name": model_name, "id": model_id})
        
        return models
    except Exception as e:
        print(f"检查Ollama模型失败: {e}")
        return []

def check_env_variables():
    """检查环境变量设置"""
    print("\n===== 检查环境变量 =====")
    
    # 检查.env文件是否存在
    if not os.path.exists(".env"):
        print("警告: .env文件不存在，将使用默认配置")
    else:
        print(".env文件存在")
        
    # 检查重要的环境变量
    env_vars = {
        "META_PROMPT_ENV": os.getenv("META_PROMPT_ENV", "dev"),
        "ACTIVE_LLM_PROVIDER": os.getenv("ACTIVE_LLM_PROVIDER", "qwen"),
        "OLLAMA_API_URL": os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "qwen3:4b"),
        "QWEN_MODEL_NAME": os.getenv("QWEN_MODEL_NAME", "qwen-plus-2025-04-28"),
        "GEMINI_MODEL_NAME": os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest")
    }
    
    print("\n当前环境变量设置:")
    for key, value in env_vars.items():
        print(f"  - {key}: {value}")
    
    # 检查是否在开发环境
    if env_vars["META_PROMPT_ENV"].lower() == "dev":
        print("\n当前为开发环境，Ollama模型将显示在前端")
    else:
        print("\n当前非开发环境，Ollama模型将不显示在前端")
    
    return env_vars

def check_api_compatibility():
    """检查API兼容性"""
    print("\n===== 检查API兼容性 =====")
    
    # 检查前端代码中的模型选择逻辑
    frontend_path = os.path.join("frontend", "src", "App.tsx")
    if not os.path.exists(frontend_path):
        print(f"错误: 前端文件不存在: {frontend_path}")
        return False
        
    print("前端代码 (App.tsx) 存在")
    
    # 检查后端API代码
    api_path = os.path.join("src", "meta_prompt_agent", "api", "main.py")
    if not os.path.exists(api_path):
        print(f"错误: API文件不存在: {api_path}")
        return False
        
    print("后端API代码 (main.py) 存在")
    
    # 检查LLM工厂类
    factory_path = os.path.join("src", "meta_prompt_agent", "core", "llm", "factory.py")
    if not os.path.exists(factory_path):
        print(f"错误: LLM工厂类文件不存在: {factory_path}")
        return False
        
    print("LLM工厂类 (factory.py) 存在")
    
    # 检查模型客户端实现
    clients_dir = os.path.join("src", "meta_prompt_agent", "core", "llm", "clients")
    if not os.path.exists(clients_dir):
        print(f"错误: 客户端目录不存在: {clients_dir}")
        return False
        
    clients = [f for f in os.listdir(clients_dir) if f.endswith(".py") and f != "__init__.py"]
    print(f"找到 {len(clients)} 个LLM客户端实现: {', '.join(clients)}")
    
    return True

def print_recommendations():
    """打印修复建议"""
    print("\n===== 修复建议 =====")
    
    print("""1. 确保前端正确发送模型信息:
  - 检查前端是否在请求中包含了 'model_info' 字段
  - 确保 'model_info' 包含了 'model' 和 'provider' 两个字段

2. 确保后端正确处理模型信息:
  - 在Agent调用invoke_llm时传递model_override和provider_override参数
  - 在LLMClientFactory.create()方法中处理provider参数
  - 在各LLM客户端中处理model_override参数

3. 更新Ollama客户端:
  - 检查Ollama API URL是否正确
  - 确保请求格式与Ollama API兼容
  - 处理模型名称映射

4. 配置环境变量:
  - 设置 META_PROMPT_ENV=dev 以启用开发环境功能
  - 检查各模型的配置是否正确""")

def main():
    """主函数"""
    print("===== 模型选择功能检查工具 =====")
    
    # 检查Ollama模型
    ollama_models = check_ollama_models()
    
    # 检查环境变量
    env_vars = check_env_variables()
    
    # 检查API兼容性
    api_compatible = check_api_compatibility()
    
    # 打印修复建议
    print_recommendations()
    
    print("\n===== 检查完成 =====")

if __name__ == "__main__":
    main() 