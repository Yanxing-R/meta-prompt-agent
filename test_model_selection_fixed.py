#!/usr/bin/env python3
"""
模型选择功能测试脚本
用于验证模型选择功能修复后是否正常工作
"""

import asyncio
import os
import sys
from pprint import pprint

# 设置环境变量确保在开发环境中运行
os.environ["META_PROMPT_ENV"] = "dev"
os.environ["OLLAMA_API_URL"] = "http://localhost:11434"
os.environ["ACTIVE_LLM_PROVIDER"] = "qwen"  # 默认使用千问

# 导入需要测试的模块
try:
    from src.meta_prompt_agent.core.agent import invoke_llm
    from src.meta_prompt_agent.config.settings import get_ollama_models, get_settings
    from src.meta_prompt_agent.core.llm.factory import LLMClientFactory
except ImportError as e:
    print(f"导入错误: {e}")
    print("请使用以下命令运行测试:")
    print("pdm run python test_model_selection_fixed.py")
    sys.exit(1)

async def test_model_factory():
    """测试模型工厂类"""
    print("\n===== 测试模型工厂类 =====")
    
    # 获取设置
    settings = get_settings()
    print(f"当前活跃提供商: {settings['ACTIVE_LLM_PROVIDER']}")
    
    # 测试默认客户端创建
    try:
        default_client = LLMClientFactory.create()
        print(f"成功创建默认客户端: {default_client.__class__.__name__}, 模型: {default_client.model_name}")
    except Exception as e:
        print(f"创建默认客户端失败: {e}")
    
    # 测试Ollama客户端创建
    try:
        ollama_client = LLMClientFactory.create("ollama")
        print(f"成功创建Ollama客户端: {ollama_client.__class__.__name__}, 模型: {ollama_client.model_name}")
    except Exception as e:
        print(f"创建Ollama客户端失败: {e}")
    
    # 测试带模型覆盖的客户端创建
    try:
        custom_client = LLMClientFactory.create("ollama", "llama3:latest")
        print(f"成功创建带模型覆盖的客户端: {custom_client.__class__.__name__}, 模型: {custom_client.model_name}")
    except Exception as e:
        print(f"创建带模型覆盖的客户端失败: {e}")

async def test_default_model():
    """测试默认模型调用"""
    print("\n===== 测试默认模型 =====")
    
    try:
        response, error = await invoke_llm("简单回答：你是谁？")
        
        if error:
            print(f"错误：{error}")
        else:
            print(f"响应：{response[:100]}...")
    except Exception as e:
        print(f"调用默认模型失败: {e}")

async def test_ollama_model():
    """测试Ollama模型调用"""
    print("\n===== 测试Ollama模型 =====")
    
    # 先检查Ollama服务状态
    from src.meta_prompt_agent.core.llm.clients.ollama import OllamaClient
    client = OllamaClient()
    available, status_msg = await client.check_service_status()
    
    if not available:
        print(f"Ollama服务不可用: {status_msg}")
        print("跳过Ollama模型测试")
        return
    
    print(f"Ollama服务状态: {status_msg}")
    
    # 获取可用的Ollama模型
    models = get_ollama_models()
    if not models:
        print("未找到Ollama模型")
        return
    
    # 定义要尝试的模型列表，按优先级排序
    models_to_try = ["qwen3:1.7b", "llama3:latest", "gemma3:1b", "phi3:latest"]
    provider = "ollama"
    
    # 尝试每个模型，直到有一个成功
    for model_name in models_to_try:
        print(f"尝试测试模型：{model_name} (提供商: {provider})")
        
        try:
            response, error = await invoke_llm(
                "简单回答：你是谁？", 
                model_override=model_name,
                provider_override=provider
            )
            
            if error:
                print(f"错误：{error}")
                print(f"模型 {model_name} 测试失败，尝试下一个模型...\n")
                continue
            else:
                print(f"模型 {model_name} 测试成功！")
                print(f"响应：{response[:100]}...")
                return  # 成功找到可用模型，结束测试
        except Exception as e:
            print(f"调用Ollama模型 {model_name} 失败: {e}")
            print(f"尝试下一个模型...\n")
    
    print("所有Ollama模型测试均失败，请检查Ollama服务状态。")

async def test_gemini_model():
    """测试Gemini模型调用"""
    print("\n===== 测试Gemini模型 =====")
    
    # 检查API密钥是否设置
    if not os.environ.get("GEMINI_API_KEY"):
        print("未设置GEMINI_API_KEY环境变量，跳过测试")
        return
    
    try:
        response, error = await invoke_llm(
            "简单回答：你是谁？", 
            model_override="gemini-1.5-flash",
            provider_override="gemini"
        )
        
        if error:
            print(f"错误：{error}")
        else:
            print(f"响应：{response[:100]}...")
    except Exception as e:
        print(f"调用Gemini模型失败: {e}")

async def main():
    """主函数"""
    print("===== 开始测试模型选择功能 =====")
    
    # 检查Ollama服务状态
    try:
        import httpx
        print("\n检查Ollama服务状态...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:11434/api/version", timeout=5.0)
                if response.status_code == 200:
                    version_info = response.json()
                    print(f"Ollama服务正常运行，版本: {version_info.get('version', '未知')}")
                    ollama_available = True
                else:
                    print(f"Ollama服务响应异常，状态码: {response.status_code}")
                    ollama_available = False
            except Exception as e:
                print(f"无法连接到Ollama服务: {e}")
                ollama_available = False
    except Exception as e:
        print(f"检查Ollama服务时出错: {e}")
        ollama_available = False
    
    # 获取可用的模型列表
    print("\n可用的Ollama模型：")
    models = []
    if ollama_available:
        models = get_ollama_models()
        for model in models:
            print(f"  - {model['name']} ({model['value']})")
    else:
        print("  无法获取Ollama模型列表，因为Ollama服务不可用")
    
    # 测试模型工厂类
    try:
        await test_model_factory()
    except Exception as e:
        print(f"测试模型工厂类时出错: {e}")
    
    # 测试默认模型调用
    try:
        await test_default_model()
    except Exception as e:
        print(f"测试默认模型时出错: {e}")
    
    # 测试Ollama模型调用
    if ollama_available:
        try:
            await test_ollama_model()
        except Exception as e:
            print(f"测试Ollama模型时出错: {e}")
    else:
        print("\n===== 跳过Ollama模型测试 =====")
        print("原因: Ollama服务不可用")
    
    # 跳过Gemini测试
    print("\n跳过Gemini模型测试")
    
    print("\n===== 测试完成 =====")

if __name__ == "__main__":
    asyncio.run(main()) 