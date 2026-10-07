"""离线 Mock LLM - 用于演示/CI/无 API Key 环境

返回的内容与前端 demo 数据保持一致, 保证演示路径完整流畅。
按场景 routing: 检测 prompt 关键字, 给出对应的医疗专业回复。
"""
import json
import re
from typing import List, Optional
from app.services.llm.base import BaseLLM, ChatMessage, LLMResponse


class MockLLM(BaseLLM):
    name = "mock"

    async def chat(
        self,
        messages: List[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        # 取最后一条用户消息内容来路由
        user_text = ""
        sys_text = ""
        for m in messages:
            if m.role == "user":
                user_text = m.content
            elif m.role == "system":
                sys_text += m.content + "\n"

        full = (sys_text + " " + user_text).lower()

        content = self._route(user_text, sys_text, full, response_format)
        return LLMResponse(
            content=content,
            model="mock-medical-v1",
            usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        )

    # -------- 场景路由 --------
    def _route(self, user_text: str, sys_text: str, full: str, response_format: Optional[str]) -> str:
        # 优先精确匹配 agent 标识 (放在系统提示词括号里 e.g. (soap)/(pre_triage)/...)
        if "(pre_triage)" in sys_text or "pre_triage" in user_text.lower():
            return self._triage_reply(user_text, response_format)
        if "(soap)" in sys_text or "soap" in user_text.lower():
            return self._soap_draft(response_format)
        if "(differential_diagnosis)" in sys_text:
            return self._diagnosis_reply(response_format)
        if "(prescription_audit)" in sys_text:
            return self._rx_audit(response_format)
        if "(prescription_suggest)" in sys_text:
            return self._rx_suggest(response_format)
        if "(report_interpret)" in sys_text:
            return self._report_interpret(response_format)

        # 退化关键字匹配
        if "预问诊" in sys_text:
            return self._triage_reply(user_text, response_format)
        if "病历草稿" in full or "病历生成" in full or "对话转写" in user_text:
            return self._soap_draft(response_format)

        # 诊断辅助
        if "鉴别诊断" in sys_text or "differential" in full:
            return self._diagnosis_reply(response_format)

        # 处方审核
        if "处方审核" in sys_text or "prescription_audit" in full:
            return self._rx_audit(response_format)

        # DRG
        if "drg" in full:
            return self._drg(response_format)

        # 报告解读
        if "报告解读" in sys_text or "report_interpret" in full or "化验" in user_text:
            return self._report_interpret(response_format)

        # 文献
        if "文献" in sys_text or "literature" in full or "pubmed" in full:
            return self._literature(response_format)

        # 标书
        if "标书" in sys_text or "国自然" in user_text or "grant" in full:
            return self._grant(response_format)

        # 论文润色
        if "润色" in user_text or "polish" in full:
            return self._paper_polish(response_format)

        # 默认通用回复
        return "您好,我是 MedMind 医疗 AI 助手。请详细描述您的问题,我会尽力帮您。"

    # -------- 预问诊 --------
    def _triage_reply(self, user_text: str, response_format: Optional[str]) -> str:
        # 解析 step
        step_match = re.search(r"step[_:]?(\d+)", user_text)
        step = int(step_match.group(1)) if step_match else 0

        scripts = [
            {"q": "您好,我是 MedMind 预问诊助手 🤖。请告诉我,您今天最不舒服的地方是哪里?什么时候开始的呢?",
             "quick": ["胸口疼,三天了", "头疼,今天早上", "咳嗽,已经一周"]},
            {"q": "明白了。请问疼痛主要在胸口的哪个位置?是闷痛、刺痛还是压榨样疼?",
             "quick": ["闷痛", "压榨样", "刺痛"]},
            {"q": "活动后、安静时、还是吃饱饭后疼?大概持续多久能缓解?",
             "quick": ["活动后", "安静时也疼", "吃饭后"]},
            {"q": "除了胸痛,您有没有伴随的症状?比如出汗、气短、恶心或左肩放射痛?",
             "quick": ["有出汗", "气短", "左肩疼"]},
            {"q": "您是否有高血压、糖尿病、高脂血症?最近在吃什么药?",
             "quick": ["有高血压", "有糖尿病", "在吃他汀"]},
            {"q": "最后一个问题:您是否吸烟?家里直系亲属有没有心脏病史?",
             "quick": ["吸烟", "父亲心梗", "都没有"]},
        ]

        if step < len(scripts):
            sc = scripts[step]
            if response_format == "json":
                return json.dumps({
                    "content": sc["q"],
                    "quick_replies": sc["quick"],
                    "step": step,
                    "completed": False,
                }, ensure_ascii=False)
            return sc["q"]

        # 完成,出 SOAP 摘要
        summary = {
            "completed": True,
            "soap": {
                "S": "反复胸痛 3 天,劳累后明显,压榨样痛",
                "O": "伴出汗、左肩放射痛,硝酸甘油可缓解 5-10 分钟",
                "A": "高度怀疑不稳定型心绞痛 / 心肌缺血",
                "P": "推荐心内科,建议心电图、心肌酶谱、肌钙蛋白检查",
            },
            "chief_complaint": "胸痛 3 天",
            "suggested_department": "心内科",
            "triage_level": "yellow",
            "confidence": 0.92,
            "content": "✅ 信息采集完毕,正在为您生成预问诊摘要..."
        }
        return json.dumps(summary, ensure_ascii=False)

    # -------- SOAP 病历草稿 --------
    def _soap_draft(self, response_format: Optional[str]) -> str:
        data = {
            "subjective": "患者女,56 岁,反复胸痛 3 天就诊。患者诉劳累后出现胸骨后压榨样疼痛,放射至左肩,持续 5-10 分钟,休息后可缓解。伴出汗,无恶心、呕吐。既往高血压病史 8 年,平素口服硝苯地平 30mg qd,血压控制可。高脂血症 5 年。否认糖尿病、冠心病家族史。吸烟史 20 年,每日 10 支。",
            "objective": "T 36.5°C,P 78 bpm,R 18,BP 138/86 mmHg。神清,皮肤巩膜无黄染。双肺呼吸音清,未及干湿啰音。心律齐,各瓣膜听诊区未及病理性杂音。腹软,无压痛。双下肢无水肿。心电图:V4-V6 导联 ST 段压低 0.1 mV。肌钙蛋白 I 0.08 ng/mL(正常<0.04)。LDL-C 4.2 mmol/L。",
            "assessment": "1. 不稳定型心绞痛(初步诊断,ICD-10: I20.0)\n2. 高血压病 2 级(ICD-10: I10)\n3. 高脂血症(ICD-10: E78.5)\n鉴别诊断:急性心肌梗死、主动脉夹层、肺栓塞。",
            "plan": "1. 收入心内科住院进一步诊治\n2. 完善冠脉 CTA 或冠脉造影\n3. 抗血小板:阿司匹林 100mg qd + 氯吡格雷 75mg qd\n4. 强化降脂:阿托伐他汀 40mg qn\n5. β 受体阻滞剂:美托洛尔 25mg bid\n6. 必要时硝酸异山梨酯舌下含服\n7. 监测心电图、心肌酶动态变化\n8. 出院前心脏康复指导",
            "icd10_codes": ["I20.0", "I10", "E78.5"],
            "confidence": 0.95,
            "quality_warnings": [],
            "citations": [
                {"title": "2026 ESC 慢性冠脉综合征管理指南", "source": "ESC Guidelines"},
                {"title": "中国 ACS 诊疗共识 2024", "source": "中华心血管病杂志"},
            ]
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- 诊断辅助 --------
    def _diagnosis_reply(self, response_format: Optional[str]) -> str:
        data = {
            "primary_diagnosis": {
                "diagnosis": "不稳定型心绞痛",
                "icd10": "I20.0",
                "probability": 0.86,
                "evidence": [
                    "压榨样胸痛伴左肩放射(典型心绞痛特征)",
                    "ST 段压低 0.1 mV(心肌缺血证据)",
                    "肌钙蛋白 I 轻度升高(心肌损伤标志物)",
                    "吸烟 20 年 + 高脂血症(危险因素)",
                ],
                "against": [],
                "recommended_tests": ["冠脉 CTA / 造影", "动态心电图", "心脏超声", "BNP"],
            },
            "differential_diagnoses": [
                {
                    "diagnosis": "急性非 ST 段抬高型心肌梗死",
                    "icd10": "I21.4", "probability": 0.42,
                    "evidence": ["肌钙蛋白升高", "ST 段改变"],
                    "against": ["心肌酶峰值未达 MI 标准"],
                    "recommended_tests": ["6h 复查肌钙蛋白"],
                },
                {
                    "diagnosis": "主动脉夹层",
                    "icd10": "I71.0", "probability": 0.08,
                    "evidence": ["突发剧烈胸痛"],
                    "against": ["疼痛性质为压榨样非撕裂样", "双上肢血压对称"],
                    "recommended_tests": ["主动脉 CTA"],
                },
                {
                    "diagnosis": "胃食管反流",
                    "icd10": "K21.0", "probability": 0.05,
                    "evidence": [], "against": ["胸痛与饮食无关", "硝酸甘油有效"],
                    "recommended_tests": [],
                },
            ],
            "hallucination_check": {
                "fact_check": "pass",
                "guideline_match": "pass",
                "contradiction_check": "pass",
                "confidence_threshold": "pass",
                "summary": "✅ 4 层幻觉防护全部通过, 诊断证据充分",
            },
            "citations": [
                {"title": "2026 ESC 慢性冠脉综合征指南", "url": "https://www.escardio.org"},
                {"title": "中国 ACS 诊疗共识 2024", "url": "#"},
            ],
            "confidence": 0.86,
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- AI 辅助开方 (v3.4 新增) --------
    def _rx_suggest(self, response_format):
        data = {
            "suggestions": [
                {
                    "drug_name": "阿司匹林",
                    "dosage": "100mg",
                    "frequency": "qd",
                    "duration": "长期",
                    "route": "口服",
                    "reason": "不稳定型心绞痛一级预防, ESC 2026 指南 IA 类推荐",
                    "contraindications": ["活动性消化道出血", "阿司匹林过敏"],
                    "evidence_level": "IA",
                },
                {
                    "drug_name": "氯吡格雷",
                    "dosage": "75mg",
                    "frequency": "qd",
                    "duration": "12 个月",
                    "route": "口服",
                    "reason": "ACS 双抗血小板治疗, DAPT 策略",
                    "contraindications": ["活动性出血", "严重肝功能不全"],
                    "evidence_level": "IA",
                },
                {
                    "drug_name": "阿托伐他汀",
                    "dosage": "40mg",
                    "frequency": "qn",
                    "duration": "长期",
                    "route": "口服",
                    "reason": "强化降脂, LDL-C 目标 <1.4 mmol/L",
                    "contraindications": ["活动性肝病", "肌病"],
                    "evidence_level": "IA",
                },
                {
                    "drug_name": "美托洛尔缓释片",
                    "dosage": "47.5mg",
                    "frequency": "qd",
                    "duration": "长期",
                    "route": "口服",
                    "reason": "β 受体阻滞剂, 控制心率、改善预后",
                    "contraindications": ["II 度以上 AVB", "哮喘"],
                    "evidence_level": "IA",
                },
            ],
            "combined_warnings": [
                "阿司匹林 + 氯吡格雷 DAPT 使用需联用 PPI 保护胃黏膜",
                "阿托伐他汀 40mg 后 4 周复查肝功能与肌酶",
            ],
            "alternatives": [
                {"场景": "阿司匹林不耐受", "替代": "改用氯吡格雷 75mg qd 单抗"},
                {"场景": "他汀不耐受", "替代": "换用依兹麦布 10mg qd"},
            ],
            "citations": [
                {"title": "2026 ESC 慢性冠脉综合征管理指南"},
                {"title": "中国 ACS 诊疗共识 2024"},
                {"title": "中国成人血脂异常防治指南 2025"},
            ],
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- 处方审核 --------
    def _rx_audit(self, response_format: Optional[str]) -> str:
        data = {
            "score": 96.0,
            "passed": True,
            "warnings": [
                {
                    "level": "warn", "category": "相互作用",
                    "title": "双抗血小板出血风险",
                    "detail": "阿司匹林 + 氯吡格雷联用出血风险升高。建议监测血常规、便潜血,必要时联用 PPI(如奥美拉唑 20mg qd)保护胃黏膜。",
                    "related_drugs": ["阿司匹林", "氯吡格雷"],
                },
                {
                    "level": "warn", "category": "剂量",
                    "title": "他汀剂量调整后需监测肝功能",
                    "detail": "阿托伐他汀从 20mg 调整为 40mg, 注意肝功能监测(4 周后复查 ALT、AST、CK)。",
                    "related_drugs": ["阿托伐他汀"],
                },
            ],
            "suggestions": [
                "联用 PPI 保护胃黏膜",
                "4 周后复查肝功能与肌酶",
                "教育患者识别出血表现",
            ],
            "citations": [
                {"title": "2026 ESC 慢性冠脉综合征指南"},
                {"title": "中国成人血脂异常防治指南 2025"},
            ],
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- DRG --------
    def _drg(self, response_format: Optional[str]) -> str:
        data = {
            "drg_code": "FB29",
            "drg_name": "经皮冠状动脉支架置入伴严重并发症",
            "payment_standard": 52800.0,
            "predicted_cost": 48500.0,
            "profit_loss": 4300.0,
            "risk_level": "green",
            "suggestions": [
                "病案首页主诊断填写规范, 编码无误",
                "建议入径前评估是否符合临床路径",
                "次均费用低于支付标准 8%, 财务安全",
            ],
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- 报告解读 --------
    def _report_interpret(self, response_format: Optional[str]) -> str:
        data = {
            "summary": "您的血脂检查显示低密度脂蛋白胆固醇 (LDL-C) 与总胆固醇均高于正常值,提示血脂代谢异常,是心血管疾病的重要危险因素。",
            "abnormal_indicators": [
                {"name": "LDL-C", "value": 4.2, "unit": "mmol/L", "range": "<3.4", "flag": "high"},
                {"name": "TC", "value": 6.8, "unit": "mmol/L", "range": "<5.2", "flag": "high"},
                {"name": "HDL-C", "value": 0.85, "unit": "mmol/L", "range": ">1.04", "flag": "low"},
            ],
            "plain_language_interpretation": "简单说,您体内的'坏胆固醇'偏多、'好胆固醇'偏少,长期下去容易引起动脉硬化和心血管疾病。",
            "suggestions": [
                "饮食上少吃油炸、肥肉、动物内脏",
                "每周至少 150 分钟中等强度运动",
                "4-6 周后复查, 如仍异常请到心内科就诊",
                "如已有高血压/糖尿病, 建议尽早到心内科评估是否启用他汀",
            ],
            "urgency": "attention",
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- 文献 --------
    def _literature(self, response_format: Optional[str]) -> str:
        data = {
            "results": [
                {
                    "title": "Empagliflozin in Patients with Coronary Artery Disease and Type 2 Diabetes",
                    "authors": ["Zinman B", "Wanner C", "Lachin JM"],
                    "journal": "N Engl J Med", "year": 2024, "impact_factor": 158.5,
                    "pmid": "39012345",
                    "abstract": "EMPA-REG 后续随访显示恩格列净在 CAD+T2DM 患者中显著降低 MACE 风险...",
                    "ai_summary": "SGLT2i 在 CAD+T2DM 人群 MACE 降低 23% (HR 0.77, 95%CI 0.65-0.91)。",
                    "tags": ["SGLT2i", "CAD", "T2DM", "MACE"],
                },
                {
                    "title": "Dapagliflozin and Cardiovascular Outcomes in Type 2 Diabetes",
                    "authors": ["Wiviott SD", "Raz I"],
                    "journal": "N Engl J Med", "year": 2023, "impact_factor": 158.5,
                    "pmid": "37123456",
                    "abstract": "DECLARE-TIMI 58 研究...",
                    "ai_summary": "达格列净显著降低心衰住院风险 (HR 0.73)。",
                    "tags": ["SGLT2i", "Dapagliflozin", "HF"],
                },
                {
                    "title": "中国 2 型糖尿病合并冠心病人群 SGLT2 抑制剂使用现状分析",
                    "authors": ["李明", "张华", "王强"],
                    "journal": "中华心血管病杂志", "year": 2025, "impact_factor": 2.1,
                    "abstract": "32 家三甲医院 12486 例横断面研究...",
                    "ai_summary": "我国 SGLT2i 在 CAD+T2DM 人群使用率仅 34.6%, 远低于欧美。",
                    "tags": ["SGLT2i", "中国人群", "处方率"],
                },
            ],
            "total": 3,
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- 标书 --------
    def _grant(self, response_format: Optional[str]) -> str:
        data = {
            "title": "SGLT2 抑制剂改善冠心病合并 2 型糖尿病患者心血管结局的机制研究",
            "sections": [
                {
                    "section": "1",
                    "title": "立项依据",
                    "content": "冠心病(CAD)合并 2 型糖尿病(T2DM)是当前全球心血管医学领域最严峻的临床问题之一。我国 35 岁以上人群 T2DM 患病率达 12.4%,其中约 35% 合并 CAD[1]。该类患者主要心血管不良事件(MACE)发生率是单纯 CAD 患者的 2.3 倍[2]。近 5 年,SGLT2 抑制剂在心血管获益方面取得突破性进展,EMPA-REG、DAPA-HF 等多项 RCT 证实其可显著降低 MACE 风险(约 20-30%)。然而其确切机制仍不明确,且现有研究主要基于欧美人群,中国人群的疗效及机制研究严重缺乏。本课题拟揭示 SGLT2i 在 CAD+T2DM 患者中的心血管保护机制,发现疗效预测的生物标志物,为个体化用药提供理论依据。",
                    "ai_score": 92,
                    "suggestions": ["建议补充具体的国内流行病学数据来源", "可强调'机制 + 临床转化'双重价值"]
                },
                {
                    "section": "2", "title": "研究内容与目标",
                    "content": "2.1 研究目标:通过前瞻性队列结合多组学分析,揭示 SGLT2i 心血管保护机制。\n2.2 研究内容:(1) 建立 800 例 CAD+T2DM 前瞻性队列;(2) 代谢组学 + 肠道菌群多组学分析;(3) 发现疗效预测标志物;(4) 构建个体化用药决策模型。",
                    "ai_score": 95, "suggestions": []
                },
                {
                    "section": "3", "title": "研究方案",
                    "content": "采用前瞻性队列研究 + 多组学联合分析,样本量 800 例,随访 24 个月。主要终点 MACE。统计采用 Cox 回归 + 随机森林。",
                    "ai_score": 91, "suggestions": ["统计方法建议增加 propensity score matching"]
                },
                {
                    "section": "4", "title": "可行性分析",
                    "content": "团队前期已完成 32 家医院 12486 例横断面研究,具备多中心合作基础。实验室已搭建代谢组学/肠道菌群分析平台。预实验数据已发表 4 篇 SCI。",
                    "ai_score": 89, "suggestions": ["建议补充团队既往主持的国自然项目"]
                },
                {
                    "section": "5", "title": "研究基础与工作条件",
                    "content": "申请人为博士生导师,主持过 2 项国自然面上项目,发表 SCI 40 篇(IF>10 共 6 篇)。所在科室为国家临床重点专科。",
                    "ai_score": 93, "suggestions": []
                },
            ],
            "overall_score": 92,
            "citations": [
                {"title": "EMPA-REG OUTCOME trial", "pmid": "26378978"},
                {"title": "Chinese Diabetes Society Guidelines 2024"},
            ],
        }
        return json.dumps(data, ensure_ascii=False)

    # -------- 论文润色 --------
    def _paper_polish(self, response_format: Optional[str]) -> str:
        data = {
            "polished_sentences": [
                {
                    "original": "We did a study about SGLT2 inhibitor in CAD patients with diabetes.",
                    "polished": "We conducted a prospective cohort study to investigate the cardiovascular benefits of SGLT2 inhibitors in patients with coronary artery disease (CAD) and type 2 diabetes mellitus (T2DM).",
                    "improvements": ["使用更专业的动词", "补充研究设计类型", "完整学术化术语"]
                },
            ],
            "journal_recommendations": [
                {"name": "Cardiovascular Diabetology", "if": 9.3, "acceptance_rate": 0.27, "match_score": 0.92},
                {"name": "JACC", "if": 24.0, "acceptance_rate": 0.15, "match_score": 0.85},
                {"name": "Diabetes Care", "if": 16.2, "acceptance_rate": 0.20, "match_score": 0.88},
            ],
        }
        return json.dumps(data, ensure_ascii=False)
