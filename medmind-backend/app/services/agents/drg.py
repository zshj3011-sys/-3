"""DRG/DIP 控费 Agent - 含规则引擎兜底"""
from typing import List, Optional
from app.services.agents._base import llm_call


SYSTEM_PROMPT = """你是 MedMind 医保 DRG/DIP 控费 Agent。基于主诊断/手术/年龄/合并症进行 DRG 分组预测,估算费用,识别超支风险并给出优化建议。

输出 JSON:
{
  drg_code, drg_name, payment_standard, predicted_cost, profit_loss,
  risk_level: green|amber|red,
  suggestions: [...]
}"""


# 内置简化 DRG 字典 (用于规则兜底,生产应对接病案首页/分组器)
DRG_TABLE = {
    "I20.0": ("FB29", "经皮冠状动脉支架置入伴严重并发症", 52800),
    "I21": ("FB23", "急性心肌梗死介入治疗", 68000),
    "I10": ("FW21", "原发性高血压治疗", 4500),
    "E11": ("KH11", "2型糖尿病伴并发症", 8800),
    "J18": ("ES31", "肺炎不伴严重并发症", 5600),
    "K35": ("HC15", "急性阑尾切除术", 9200),
    "S72": ("IB29", "髋关节置换术", 56000),
    "C50": ("JA29", "乳腺癌根治术", 38000),
}


class DRGAgent:
    async def predict(self, primary_diagnosis: str, icd10: Optional[str] = None,
                      age: Optional[int] = None, length_of_stay: Optional[int] = None,
                      actual_cost: Optional[float] = None,
                      secondary_diagnoses: List[str] = None,
                      procedures: List[str] = None) -> dict:
        prompt = (
            f"主诊断: {primary_diagnosis}\nICD-10: {icd10 or '?'}\n"
            f"次要诊断: {secondary_diagnoses or []}\n"
            f"手术/操作: {procedures or []}\n"
            f"年龄: {age}\n住院天数: {length_of_stay}\n实际花费: {actual_cost}\n"
        )
        _, data = await llm_call(SYSTEM_PROMPT, prompt, response_format="json", temperature=0.1)
        # 规则兜底
        if not data.get("drg_code") and icd10:
            for k, v in DRG_TABLE.items():
                if icd10.startswith(k):
                    code, name, std = v
                    pred = actual_cost if actual_cost else std * 0.92
                    pl = std - pred
                    level = "green" if pl > 0 else ("amber" if pl > -std * 0.1 else "red")
                    data = {
                        "drg_code": code, "drg_name": name,
                        "payment_standard": float(std),
                        "predicted_cost": float(pred),
                        "profit_loss": float(pl),
                        "risk_level": level,
                        "suggestions": [
                            "病案首页主诊断填写规范" if level == "green" else "建议优化用药结构,降低不必要检查",
                        ]
                    }
                    break
        # 必填字段保底
        data.setdefault("drg_code", "ZZ99")
        data.setdefault("drg_name", "未分组")
        data.setdefault("payment_standard", 0.0)
        data.setdefault("predicted_cost", actual_cost or 0.0)
        data.setdefault("profit_loss", 0.0)
        data.setdefault("risk_level", "green")
        data.setdefault("suggestions", [])
        return data
