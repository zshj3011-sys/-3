"""LLM 适配器 - 同一接口对接 Mock/DeepSeek/通义/智谱 等"""
from app.services.llm.base import BaseLLM, ChatMessage
from app.services.llm.factory import get_llm

__all__ = ["BaseLLM", "ChatMessage", "get_llm"]
