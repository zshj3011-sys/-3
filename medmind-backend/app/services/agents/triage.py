"""AI 预问诊 Agent (患者端核心)"""
from typing import Optional
from app.services.agents._base import llm_call, safe_parse_json
from app.services.llm import get_llm, ChatMessage


SYSTEM_PROMPT = """你是 MedMind 医疗 AI 预问诊助手 (pre_triage)。任务:与患者多轮对话,5-6 个问题后输出 SOAP 结构化摘要。

规则:
1. 每次只问 1 个最关键的问题, 简洁友好,提供 3 个快捷选项
2. 优先采集: 主诉/时间/性质/部位/伴随症状/既往史/用药史/家族史
3. 检测红色预警: 急性胸痛/意识障碍/严重出血/呼吸困难 -> triage_level=red 并提醒立即就医
4. 中度预警: 高血压未控制/胸痛伴出汗等 -> yellow
5. 完成时输出 JSON {completed:true, soap:{S,O,A,P}, chief_complaint, suggested_department, triage_level, confidence}
6. 未完成时输出 JSON {completed:false, content:"问题文本", quick_replies:["选项1","选项2","选项3"], step:N}

请始终用中文,保持温暖、专业、易懂。"""


class TriageAgent:
    async def next_message(self, history: list[dict], step: int) -> dict:
        """根据对话历史返回下一步 AI 消息或最终摘要"""
        # 拼接历史给 LLM
        history_text = "\n".join([
            f"{m['role']}: {m['content']}" for m in history[-12:]
        ])
        user_prompt = f"对话历史(step_{step}):\n{history_text}\n\n请输出 JSON 格式的回应。"

        llm = get_llm()
        resp = await llm.chat(
            [
                ChatMessage(role="system", content=SYSTEM_PROMPT),
                ChatMessage(role="user", content=user_prompt),
            ],
            temperature=0.4,
            response_format="json",
        )
        data = safe_parse_json(resp.content)
        if not data:
            # fallback
            data = {
                "completed": False,
                "content": "请详细描述您的症状,我会一步步引导您完成预问诊。",
                "quick_replies": [],
                "step": step,
            }
        return data
