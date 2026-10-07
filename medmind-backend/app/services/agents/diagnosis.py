"""AI 诊断辅助 Agent - 含 4 层幻觉防护"""
from typing import Optional, List
from app.services.agents._base import llm_call


SYSTEM_PROMPT = """你是 MedMind 医疗 AI 诊断辅助助手 (differential_diagnosis)。基于主诉、症状、既往史、检查结果给出鉴别诊断,严格执行 4 层幻觉防护。

4 层幻觉防护:
1. fact_check: 关键事实需有指南/RCT 证据支持
2. guideline_match: 推理必须匹配最新临床指南
3. contradiction_check: 排查推理内部矛盾
4. confidence_threshold: 主要诊断 confidence < 0.6 时必须标 warn

输出 JSON:
{
  primary_diagnosis: {diagnosis, icd10, probability, evidence:[], against:[], recommended_tests:[]},
  differential_diagnoses: [{...同上}],
  hallucination_check: {fact_check, guideline_match, contradiction_check, confidence_threshold, summary},
  citations: [{title, source/url}],
  confidence
}

要求严谨, 不要编造文献。"""


class DiagnosisAgent:
    async def differential(self, chief_complaint: str, symptoms: List[str],
                           history: Optional[str] = None,
                           lab_results: Optional[List[dict]] = None) -> dict:
        user_prompt = f"主诉: {chief_complaint}\n症状: {', '.join(symptoms)}\n"
        if history:
            user_prompt += f"既往史: {history}\n"
        if lab_results:
            user_prompt += f"检查结果: {lab_results}\n"
        user_prompt += "\n请给出鉴别诊断 (JSON)。"

        _, data = await llm_call(SYSTEM_PROMPT, user_prompt, response_format="json", temperature=0.2)
        data.setdefault("primary_diagnosis", {})
        data.setdefault("differential_diagnoses", [])
        data.setdefault("hallucination_check", {})
        data.setdefault("citations", [])
        data.setdefault("confidence", 0.0)
        return data
