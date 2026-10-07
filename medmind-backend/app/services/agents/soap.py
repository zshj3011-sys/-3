"""SOAP 病历生成 Agent (医生端核心)"""
from typing import Optional
from app.services.agents._base import llm_call


SYSTEM_PROMPT = """你是 MedMind 医疗 AI 病历生成助手 (soap)。基于医患对话语音转写文本或预问诊摘要,生成符合 SOAP 格式的电子病历草稿。

要求:
1. 严格 SOAP 四段: S 主观 / O 客观 / A 评估 / P 计划
2. 使用规范医学术语, 包含 ICD-10 编码
3. 推断诊断时给出 confidence (0-1)
4. 若证据不足或矛盾,在 quality_warnings 列出
5. 必须列出 citations(指南/共识/文献)
6. 输出 JSON: {subjective, objective, assessment, plan, icd10_codes:[], confidence, quality_warnings:[], citations:[]}"""


class SOAPAgent:
    async def generate_draft(self, transcript: str, patient_context: Optional[str] = None) -> dict:
        user_prompt = ""
        if patient_context:
            user_prompt += f"患者背景:\n{patient_context}\n\n"
        user_prompt += f"对话转写/预问诊摘要:\n{transcript}\n\n请生成 SOAP 病历草稿 (JSON)。"

        _, data = await llm_call(SYSTEM_PROMPT, user_prompt, response_format="json", temperature=0.2)
        # 确保字段齐全
        data.setdefault("subjective", "")
        data.setdefault("objective", "")
        data.setdefault("assessment", "")
        data.setdefault("plan", "")
        data.setdefault("icd10_codes", [])
        data.setdefault("confidence", 0.0)
        data.setdefault("quality_warnings", [])
        data.setdefault("citations", [])
        return data
