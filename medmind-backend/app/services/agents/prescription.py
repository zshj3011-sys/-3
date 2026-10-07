"""处方审核 / 辅助开方 Agent"""
from typing import List
from app.services.agents._base import llm_call


SYSTEM_PROMPT = """你是 MedMind 处方审核助手 (prescription_audit)。审核处方,检查:剂量合规 / 给药途径 / 禁忌症 / 过敏 / 配伍 / 相互作用 / 重复用药。

输出 JSON:
{
  score: 0-100,
  passed: bool,
  warnings: [{level: info|warn|error, category, title, detail, related_drugs:[]}],
  suggestions: [...],
  citations: [...]
}

严格依据药品说明书/最新指南, 不要凭空创造警告。"""


# v3.4 新增: AI 辅助开方 SYSTEM PROMPT
SUGGEST_SYSTEM_PROMPT = """你是 MedMind 辅助开方助手 (prescription_suggest)。根据诊断列表 + 过敏史 生成临床指南区推荐的药物治疗方案。

要求:
1. 遵循严格的临床诊疗指南 (ESC / AHA / NICE / 中华医学会)。
2. 明确指出药物名 / 规格 / 剂量 / 频次 / 疗程。
3. 需考虑过敏史禁忌, 避免重复用药与严重不良相互作用。
4. 每条推荐需给出 reason (适应症依据), contraindications (禁忌限制)。
5. 仅作临床辅助表达, 不代替医师决策。

输出 JSON:
{
  suggestions: [
    { drug_name, dosage, frequency, duration, route, reason, contraindications:[], evidence_level }
  ],
  combined_warnings: [...],   // 组合用药需注意点
  alternatives: [...],         // 可选替代方案
  citations: [...]             // 指南出处
}"""


class PrescriptionAuditAgent:
    async def audit(self, items: List[dict], diagnosis: str = "",
                    allergy_history: List[str] = None) -> dict:
        allergy_history = allergy_history or []
        prompt = f"诊断: {diagnosis}\n过敏史: {', '.join(allergy_history) or '无'}\n处方明细:\n"
        for it in items:
            prompt += f"  - {it.get('drug_name')} {it.get('dose')} {it.get('frequency')} × {it.get('duration_days','?')}天\n"
        prompt += "\n请输出审核 JSON。"

        _, data = await llm_call(SYSTEM_PROMPT, prompt, response_format="json", temperature=0.2)
        data.setdefault("score", 0)
        data.setdefault("passed", False)
        data.setdefault("warnings", [])
        data.setdefault("suggestions", [])
        data.setdefault("citations", [])
        return data

    async def suggest(self, diagnosis: List[str], allergy_history: List[str] = None,
                      patient_age: int = None, patient_gender: str = None,
                      current_meds: List[str] = None) -> dict:
        """v3.4 新增: AI 辅助开方 - PRD 6.1 /ai/prescriptions/suggest"""
        allergy_history = allergy_history or []
        current_meds = current_meds or []
        prompt = (
            f"患者信息: 年龄 {patient_age or '?'} | 性别 {patient_gender or '?'}\n"
            f"诊断: {'; '.join(diagnosis)}\n"
            f"过敏史: {', '.join(allergy_history) or '无'}\n"
            f"现用药: {', '.join(current_meds) or '无'}\n"
            "请根据临床指南辅助推荐药物治疗方案, 输出 JSON。"
        )
        _, data = await llm_call(SUGGEST_SYSTEM_PROMPT, prompt, response_format="json", temperature=0.2)
        data.setdefault("suggestions", [])
        data.setdefault("combined_warnings", [])
        data.setdefault("alternatives", [])
        data.setdefault("citations", [])
        return data
