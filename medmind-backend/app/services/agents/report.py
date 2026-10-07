"""化验/影像报告 AI 解读"""
from typing import List
from app.services.agents._base import llm_call


SYSTEM_PROMPT = """你是 MedMind 医疗报告解读助手 (report_interpret)。把专业指标转换为患者易懂的语言。

要求:
1. 标记异常指标 (high/low),解释临床意义
2. 用大白话翻译, 避免专业术语
3. 给出 3-5 条生活建议
4. 紧急程度: normal/attention/urgent

输出 JSON: {summary, abnormal_indicators:[], plain_language_interpretation, suggestions:[], urgency}"""


class ReportInterpretAgent:
    async def interpret(self, indicators: List[dict], report_type: str = "blood_lipid") -> dict:
        prompt = f"报告类型: {report_type}\n指标:\n"
        for ind in indicators:
            prompt += f"  - {ind.get('name')}: {ind.get('value')} {ind.get('unit','')} (参考 {ind.get('range','')})\n"
        prompt += "\n请输出 JSON。"
        _, data = await llm_call(SYSTEM_PROMPT, prompt, response_format="json", temperature=0.3)
        data.setdefault("summary", "")
        data.setdefault("abnormal_indicators", [])
        data.setdefault("plain_language_interpretation", "")
        data.setdefault("suggestions", [])
        data.setdefault("urgency", "normal")
        return data
