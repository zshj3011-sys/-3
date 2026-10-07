"""LLM 工厂 - 根据配置返回 LLM 实例

支持 mock / deepseek / openai / qwen / zhipu / moonshot 等
所有非mock provider都走 OpenAI 兼容协议
"""
from functools import lru_cache
from app.core.config import settings
from app.services.llm.base import BaseLLM
from app.services.llm.mock import MockLLM
from app.services.llm.openai_compatible import OpenAICompatibleLLM


_PROVIDER_DEFAULTS = {
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    "zhipu": ("https://open.bigmodel.cn/api/paas/v4", "glm-4-flash"),
    "moonshot": ("https://api.moonshot.cn/v1", "moonshot-v1-8k"),
}


@lru_cache()
def get_llm() -> BaseLLM:
    provider = (settings.LLM_PROVIDER or "mock").lower()

    if provider == "mock" or not settings.LLM_API_KEY:
        return MockLLM()

    # 取默认
    default_base, default_model = _PROVIDER_DEFAULTS.get(provider, ("", ""))
    base = settings.LLM_API_BASE or default_base
    model = settings.LLM_MODEL or default_model
    if not base or not model:
        # 配置不完整,退回 Mock
        return MockLLM()
    return OpenAICompatibleLLM(
        api_key=settings.LLM_API_KEY,
        api_base=base,
        model=model,
        name=provider,
    )
