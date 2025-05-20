"""
LLM集成抽象层

提供统一的大型语言模型集成接口，支持多种模型提供商。
"""

from .factory import LLMClientFactory
from .base import LLMClient

__all__ = ["LLMClientFactory", "LLMClient"] 