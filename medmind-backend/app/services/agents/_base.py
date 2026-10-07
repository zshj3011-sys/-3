"""Agent 公共工具"""
import json
import re
from typing import Any
from app.services.llm import get_llm, ChatMessage


def safe_parse_json(text: str) -> dict:
    """从模型输出里尽力解析 JSON"""
    if not text:
        return {}
    text = text.strip()
    # 提取最大花括号块
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    # 尝试整个 parse
    try:
        return json.loads(text)
    except Exception:
        return {}


async def llm_call(system_prompt: str, user_prompt: str,
                   *, response_format: str = "json", temperature: float = 0.3) -> tuple[str, dict]:
    """调用 LLM 并返回 (raw, json_parsed)"""
    llm = get_llm()
    resp = await llm.chat(
        [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ],
        temperature=temperature,
        response_format=response_format,
    )
    parsed = safe_parse_json(resp.content) if response_format == "json" else {}
    return resp.content, parsed
