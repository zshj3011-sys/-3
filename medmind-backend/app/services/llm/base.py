"""LLM 适配器基类 - 统一接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional, Dict, Any


@dataclass
class ChatMessage:
    role: str  # system | user | assistant | tool
    content: str
    name: Optional[str] = None


@dataclass
class LLMResponse:
    content: str
    model: str
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    raw: Optional[Any] = None


class BaseLLM(ABC):
    name: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[str] = None,  # json | text
        **kwargs,
    ) -> LLMResponse:
        ...

    async def chat_stream(
        self, messages: List[ChatMessage], **kwargs
    ) -> AsyncIterator[str]:
        """流式输出 - 默认实现退化为整段返回"""
        resp = await self.chat(messages, **kwargs)
        for ch in resp.content:
            yield ch
