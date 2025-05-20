# Think Twice API 使用指南

Think Twice API提供了一系列端点，用于生成和优化提示词，以及提交用户反馈。本文档介绍了如何使用这些API。

## 目录

1. [API概述](#api概述)
2. [启动API服务](#启动api服务)
3. [使用Python客户端](#使用python客户端)
4. [使用命令行工具](#使用命令行工具)
5. [API端点详解](#api端点详解)
6. [错误处理](#错误处理)

## API概述

Think Twice API是一个RESTful API，提供以下功能：

- 生成简单优化提示
- 生成带自我校正的高级提示
- 解释提示词中的特定术语
- 提交和查询用户反馈
- 获取系统信息

所有API都返回JSON格式的数据，并使用标准的HTTP状态码表示请求的状态。

## 启动API服务

要启动API服务，请按照以下步骤操作：

1. 确保已安装所有依赖：

```
pdm install
```

2. 启动API服务：

```
cd src/meta_prompt_agent
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后，可以通过访问 http://localhost:8000/docs 查看API文档。

## 使用Python客户端

我们提供了一个Python客户端类，可以轻松地与API进行交互：

```python
from meta_prompt_agent.api.client import ThinkTwiceAPIClient

# 创建客户端实例
client = ThinkTwiceAPIClient(base_url="http://localhost:8000")

# 获取系统信息
system_info = client.get_system_info()
print(f"当前活跃的LLM提供者: {system_info['active_llm_provider']}")
print(f"当前模型: {system_info['model_name']}")

# 生成简单提示
result = client.generate_simple_prompt(
    raw_request="我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战",
    task_type="深度研究"
)

if not result.get("error"):
    print(f"生成的提示: {result['p1_prompt']}")
else:
    print(f"生成失败: {result['detail']}")
```

## 使用命令行工具

我们还提供了一个命令行工具，可以方便地从命令行使用API：

```bash
# 获取系统信息
python scripts/api_cli.py info

# 生成简单提示
python scripts/api_cli.py simple --request "我想了解中短期天气预报" --task-type "深度研究"

# 生成高级提示（带自我校正）
python scripts/api_cli.py advanced --request "我想了解中短期天气预报" --self-correction --depth 2

# 解释术语
python scripts/api_cli.py explain --term "S2S" --context "我想了解中短期天气、S2S及年际预报"

# 提交反馈
python scripts/api_cli.py feedback --id "prompt-123" --request "原始请求" --prompt "生成的提示" --rating 5 --comment "很好"

# 列出反馈
python scripts/api_cli.py list-feedback --limit 10 --offset 0 --min-rating 3
```

## API端点详解

### 生成简单提示

**端点:** `/generate-simple-p1`

**方法:** POST

**请求体:**
```json
{
  "raw_request": "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战",
  "task_type": "深度研究"
}
```

**响应:**
```json
{
  "p1_prompt": "这是一个优化后的提示词...",
  "original_request": "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战",
  "message": "P1提示已成功生成。"
}
```

### 生成高级提示

**端点:** `/generate-advanced-prompt`

**方法:** POST

**请求体:**
```json
{
  "raw_request": "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战",
  "task_type": "深度研究",
  "enable_self_correction": true,
  "max_recursion_depth": 2,
  "template_name": null,
  "template_variables": null
}
```

**响应:**
```json
{
  "final_prompt": "这是最终优化后的提示词...",
  "initial_prompt": "这是初步优化的提示词...",
  "refined_prompts": ["第一轮优化...", "第二轮优化..."],
  "evaluation_reports": [{...}, {...}],
  "message": "高级提示已成功生成。"
}
```

### 解释术语

**端点:** `/explain-term`

**方法:** POST

**请求体:**
```json
{
  "term_to_explain": "S2S",
  "context_prompt": "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战"
}
```

**响应:**
```json
{
  "explanation": "S2S (Subseasonal to Seasonal) 是指次季节到季节时间尺度的预报...",
  "term": "S2S",
  "message": "术语已成功解释。"
}
```

### 获取系统信息

**端点:** `/system/info`

**方法:** GET

**响应:**
```json
{
  "active_llm_provider": "qwen",
  "model_name": "qwen-plus-2025-04-28",
  "available_providers": ["ollama", "gemini", "qwen"],
  "version": "0.1.0",
  "structured_templates": ["BasicImageGen", "BasicCodeSnippet"]
}
```

### 提交反馈

**端点:** `/feedback/submit`

**方法:** POST

**请求体:**
```json
{
  "prompt_id": "prompt-123",
  "original_request": "我想了解中短期天气预报",
  "generated_prompt": "这是生成的提示",
  "rating": 5,
  "comment": "非常好的提示优化"
}
```

**响应:**
```json
{
  "success": true,
  "message": "反馈已成功提交",
  "feedback_id": "prompt-123"
}
```

### 获取反馈列表

**端点:** `/feedback/list`

**方法:** GET

**参数:**
- `limit`: 返回数量（默认20）
- `offset`: 分页起始位置（默认0）
- `min_rating`: 最低评分过滤（可选）

**响应:**
```json
{
  "feedback_items": [
    {
      "prompt_id": "prompt-123",
      "original_request": "我想了解中短期天气预报",
      "generated_prompt": "这是生成的提示",
      "rating": 5,
      "comment": "非常好的提示优化",
      "timestamp": "2023-05-01T12:00:00"
    }
  ],
  "total_count": 1
}
```

## 错误处理

API使用标准的HTTP状态码表示请求的状态：

- 200: 请求成功
- 201: 创建成功（用于POST请求）
- 400: 请求参数错误
- 422: 请求体验证失败
- 500: 服务器内部错误

当发生错误时，API会返回具体的错误信息：

```json
{
  "detail": "错误消息详情"
}
```

Python客户端会将这些错误包装成易于处理的格式：

```python
{
  "error": true,
  "status_code": 500,
  "detail": "错误消息详情"
}
``` 