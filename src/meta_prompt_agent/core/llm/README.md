# LLM 抽象层

本模块提供了统一的大型语言模型（LLM）接口抽象，让系统能够灵活地支持多种LLM服务提供商。

## 架构设计

LLM抽象层采用了以下设计模式：

1. **抽象工厂模式**：`LLMClientFactory` 负责创建和管理不同类型的LLM客户端
2. **策略模式**：不同的LLM客户端实现相同的接口，但有不同的实现策略
3. **单一职责原则**：每个客户端类只负责与特定LLM提供商的交互
4. **依赖注入**：使用配置管理和工厂方法实现依赖的灵活配置

## 核心组件

### 基类 (`base.py`)

提供了 `LLMClient` 抽象基类，定义了所有LLM客户端必须实现的接口：

```python
class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本响应"""
        pass
        
    @abstractmethod
    async def generate_with_metadata(self, prompt: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """生成文本响应及元数据"""
        pass
```

### 工厂 (`factory.py`)

提供了 `LLMClientFactory` 类，负责创建各种LLM客户端的实例：

```python
class LLMClientFactory:
    @classmethod
    def create(cls, provider: str = None, **kwargs) -> LLMClient:
        """创建LLM客户端实例"""
        # 如果没有指定提供商，使用配置中的活跃提供商
        ...
```

### 客户端实现 (`clients/`)

包含各种LLM服务提供商的具体实现：

- `ollama.py`: Ollama本地模型的客户端
- `gemini.py`: Google Gemini API的客户端
- `qwen.py`: 通义千问API的客户端

## 使用方法

### 基本用法

```python
from meta_prompt_agent.core.llm import LLMClientFactory

# 使用环境变量或配置中指定的默认提供商创建客户端
llm_client = LLMClientFactory.create()

# 或者明确指定提供商
ollama_client = LLMClientFactory.create("ollama")
gemini_client = LLMClientFactory.create("gemini")
qwen_client = LLMClientFactory.create("qwen")

# 异步调用生成文本
response = await llm_client.generate("你好，请生成一个创意故事。")

# 获取响应和元数据
response, metadata = await llm_client.generate_with_metadata(
    "分析下面这段代码的性能问题",
    temperature=0.2
)
```

### 支持的参数

所有LLM客户端实现都支持以下通用参数：

- `temperature`: 控制生成文本的随机性 (范围通常为0-1)
- `max_tokens`: 限制生成的最大token数量
- `messages_history`: 对话历史记录（用于支持上下文）

不同的客户端可能还支持特定的额外参数，详见各实现类的文档。

## 配置方式

LLM抽象层使用以下环境变量配置：

- `ACTIVE_LLM_PROVIDER`: 活跃的LLM提供商 ("ollama", "gemini", "qwen")
- `OLLAMA_MODEL`: Ollama模型名称
- `OLLAMA_API_URL`: Ollama API URL
- `GEMINI_API_KEY`: Google Gemini API密钥
- `GEMINI_MODEL_NAME`: Gemini模型名称
- `DASHSCOPE_API_KEY`/`QWEN_API_KEY`: 通义千问API密钥
- `QWEN_MODEL_NAME`: 通义千问模型名称

配置可以在 `.env` 文件中设置，或通过环境变量直接设置。

## 扩展新的LLM提供商

要添加新的LLM提供商支持，需要：

1. 在 `clients/` 目录中创建新的客户端实现类，继承 `LLMClient`
2. 实现必要的方法：`generate` 和 `generate_with_metadata`
3. 在 `clients/__init__.py` 中导出新类
4. 在 `factory.py` 的 `LLMClientFactory._clients` 字典中注册新类

## 错误处理

客户端实现应当处理特定于提供商的错误，并将其转换为通用的异常或返回格式。一般来说：

- API连接问题应当引发适当的异常
- API响应中的错误应当被捕获并以结构化方式返回
- 所有异常情况应当有适当的日志记录 