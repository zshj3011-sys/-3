"""OpenAI 兼容协议的统一客户端 - 对接 DeepSeek/通义/智谱/Moonshot 等"""
from typing import List, Optional
import httpx
from app.services.llm.base import BaseLLM, ChatMessage, LLMResponse
from app.core.config import settings


class OpenAICompatibleLLM(BaseLLM):
    def __init__(self, api_key: str, api_base: str, model: str, name: str = "openai_compat"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.name = name

    async def chat(
        self,
        messages: List[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            r = await client.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
            r.raise_for_status()
            data = r.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            finish_reason=choice.get("finish_reason", "stop"),
            usage=data.get("usage", {}),
            raw=data,
        )
