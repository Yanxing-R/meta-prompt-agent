# tests/test_model_selection.py
import asyncio
import sys
import os
import json

# 将项目根目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 现在导入项目模块
from src.meta_prompt_agent.core.agent import invoke_llm
from src.meta_prompt_agent.config.settings import get_ollama_models

async def test_default_model():
    """测试默认模型调用"""
    print("\n===== 测试默认模型 =====")
    response, error = await invoke_llm("简单回答：你是谁？")
    if error:
        print(f"错误：{error}")
    else:
        print(f"响应：{response[:100]}...")

async def test_ollama_model():
    """测试Ollama模型调用"""
    print("\n===== 测试Ollama模型 =====")
    models = get_ollama_models()
    if not models:
        print("未找到Ollama模型")
        return
    
    # 选择第一个Ollama模型进行测试
    model_name = models[0]["value"]
    provider = models[0]["provider"]
    print(f"测试模型：{model_name} (提供商: {provider})")
    
    response, error = await invoke_llm(
        "简单回答：你是谁？", 
        model_override=model_name,
        provider_override=provider
    )
    
    if error:
        print(f"错误：{error}")
    else:
        print(f"响应：{response[:100]}...")

async def test_qwen_model():
    """测试千问模型调用"""
    print("\n===== 测试千问模型 =====")
    response, error = await invoke_llm(
        "简单回答：你是谁？", 
        model_override="qwen-plus",
        provider_override="qwen"
    )
    
    if error:
        print(f"错误：{error}")
    else:
        print(f"响应：{response[:100]}...")

async def main():
    """执行所有测试"""
    print("开始测试模型选择功能...")
    
    # 打印可用的Ollama模型
    print("\n可用的Ollama模型：")
    models = get_ollama_models()
    for model in models:
        print(f"  - {model['name']} ({model['value']})")
    
    # 测试默认模型
    await test_default_model()
    
    # 测试Ollama模型
    await test_ollama_model()
    
    # 测试千问模型
    await test_qwen_model()

if __name__ == "__main__":
    asyncio.run(main()) 