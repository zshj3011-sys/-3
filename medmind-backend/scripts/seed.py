"""演示数据播种 - 一份完整可用的演示数据集"""
import asyncio
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import hash_password, generate_id
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.medical_record import MedicalRecord
from app.models.prescription import Prescription, PrescriptionItem
from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.safety_event import SafetyEvent           # v3.6.2
from app.models.research_dataset import ResearchDataset   # v3.6.2
from app.models.drg import DRGCase
from app.models.lab_report import LabReport


async def seed_users(db: AsyncSession):
    users = [
        {"username": "admin", "password": "admin123", "role": "admin", "full_name": "管理员"},
        {"username": "dr_zhang", "password": "doctor123", "role": "doctor", "full_name": "张为民"},
        {"username": "dr_li", "password": "doctor123", "role": "doctor", "full_name": "李芳"},
        {"username": "dr_wang", "password": "doctor123", "role": "doctor", "full_name": "王建国"},
        {"username": "prof_zhao", "password": "researcher123", "role": "researcher", "full_name": "赵教授"},
        {"username": "pharm_wang", "password": "pharm123", "role": "pharmacist", "full_name": "王药师"},
        {"username": "patient_li", "password": "patient123", "role": "patient", "full_name": "李秀芳"},
        {"username": "patient_wang", "password": "patient123", "role": "patient", "full_name": "王志强"},
    ]
    created = {}
    for u in users:
        user = User(
            username=u["username"], password_hash=hash_password(u["password"]),
            role=u["role"], full_name=u["full_name"], is_active=True,
        )
        db.add(user); await db.flush()
        created[u["username"]] = user
    return created


async def seed_departments(db: AsyncSession):
    items = [
        {"code": "INT", "name": "内科", "description": "心血管/呼吸/消化/内分泌"},
        {"code": "CAR", "name": "心内科", "description": "心血管疾病诊疗"},
        {"code": "SUR", "name": "外科", "description": "普外/骨科/泌尿"},
        {"code": "PED", "name": "儿科", "description": "儿童常见病诊疗"},
        {"code": "OBG", "name": "妇产科", "description": "妇科/产科"},
        {"code": "ORT", "name": "骨科", "description": "骨科疾病诊疗"},
        {"code": "OPH", "name": "眼科", "description": "眼科疾病诊疗"},
        {"code": "ENT", "name": "耳鼻喉科", "description": "耳鼻喉疾病"},
    ]
    created = {}
    for it in items:
        d = Department(**it); db.add(d); await db.flush()
        created[it["code"]] = d
    return created


async def seed_doctors(db: AsyncSession, users, depts):
    items = [
        {"user": "dr_zhang", "name": "张为民", "dept": "CAR", "title": "主任医师",
         "specialties": "冠心病/高血压/心衰", "years": 22, "rating": 4.9,
         "license_number": "1102560000123"},
        {"user": "dr_li", "name": "李芳", "dept": "CAR", "title": "副主任医师",
         "specialties": "心律失常/起搏器", "years": 14, "rating": 4.8,
         "license_number": "1102560000456"},
        {"user": "dr_wang", "name": "王建国", "dept": "CAR", "title": "主治医师",
         "specialties": "心衰/瓣膜病", "years": 9, "rating": 4.7,
         "license_number": "1102560000789"},
    ]
    created = {}
    for it in items:
        d = Doctor(
            user_id=users[it["user"]].id,
            doctor_name=it["name"],
            department_id=depts[it["dept"]].id,
            title=it["title"], specialties=it["specialties"],
            years_of_practice=it["years"], rating=it["rating"],
            license_number=it["license_number"],
        )
        db.add(d); await db.flush()
        created[it["user"]] = d
    return created


async def seed_patients(db: AsyncSession, users):
    items = [
        {"user": "patient_li", "name": "李秀芳", "gender": "女",
         "birth": date(1969, 8, 12), "phone": "13800001234",
         "allergy": ["青霉素"], "past": ["高血压8年", "高脂血症5年"]},
        {"user": "patient_wang", "name": "王志强", "gender": "男",
         "birth": date(1977, 3, 25), "phone": "13800005678",
         "allergy": [], "past": ["糖尿病3年"]},
        # 补充几个无用户的患者
        {"user": None, "name": "陈丽", "gender": "女",
         "birth": date(1963, 11, 8), "phone": "13800002222",
         "allergy": [], "past": ["房颤", "高血压"]},
        {"user": None, "name": "刘建国", "gender": "男",
         "birth": date(1970, 5, 15), "phone": "13800003333",
         "allergy": [], "past": ["冠脉支架术后1月"]},
        {"user": None, "name": "赵梅", "gender": "女",
         "birth": date(1958, 2, 28), "phone": "13800004444",
         "allergy": [], "past": ["心衰 NYHA II 级"]},
    ]
    created = {}
    for it in items:
        p = Patient(
            user_id=users[it["user"]].id if it["user"] else None,
            real_name=it["name"], gender=it["gender"],
            birth_date=it["birth"], phone=it["phone"],
            allergy_history=it["allergy"], past_history=it["past"],
        )
        db.add(p); await db.flush()
        created[it["name"]] = p
    return created


async def seed_appointments(db: AsyncSession, patients, doctors):
    today = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0, microsecond=0)
    items = [
        {"patient": "李秀芳", "doctor": "dr_zhang", "time_offset": 0,
         "type": "follow_up", "complaint": "胸痛 3 天,劳累后明显"},
        {"patient": "王志强", "doctor": "dr_zhang", "time_offset": 30,
         "type": "outpatient", "complaint": "胸闷气短"},
        {"patient": "陈丽", "doctor": "dr_zhang", "time_offset": 60,
         "type": "follow_up", "complaint": "房颤抗凝随访"},
        {"patient": "刘建国", "doctor": "dr_zhang", "time_offset": 90,
         "type": "follow_up", "complaint": "冠脉支架术后 1 月"},
        {"patient": "赵梅", "doctor": "dr_zhang", "time_offset": 120,
         "type": "follow_up", "complaint": "心衰随访"},
    ]
    for it in items:
        a = Appointment(
            patient_id=patients[it["patient"]].id,
            doctor_id=doctors[it["doctor"]].id,
            scheduled_at=today + timedelta(minutes=it["time_offset"]),
            visit_type=it["type"],
            chief_complaint=it["complaint"],
            status="scheduled",
        )
        db.add(a)


async def seed_drg_cases(db: AsyncSession):
    samples = [
        ("FB29", "经皮冠脉支架置入伴严重并发症", "I20.0", 52800, 48500, 4300, "green"),
        ("FB23", "急性心肌梗死介入治疗", "I21.0", 68000, 71200, -3200, "amber"),
        ("FW21", "原发性高血压治疗", "I10", 4500, 3900, 600, "green"),
        ("KH11", "2型糖尿病伴并发症", "E11.9", 8800, 9800, -1000, "amber"),
        ("ES31", "肺炎不伴严重并发症", "J18.9", 5600, 5100, 500, "green"),
        ("IB29", "髋关节置换术", "S72.0", 56000, 62500, -6500, "red"),
    ]
    for code, name, icd, std, actual, pl, risk in samples:
        c = DRGCase(
            case_number=f"DRG-{generate_id()[:10].upper()}",
            drg_code=code, drg_name=name, icd10=icd,
            primary_diagnosis=name,
            payment_standard=std, actual_cost=actual,
            predicted_cost=actual, profit_loss=pl, risk_level=risk,
            length_of_stay=7, insurance_type="医保",
            ai_suggestions=["✓ 编码规范" if pl > 0 else "建议优化用药结构与检查项"],
        )
        db.add(c)


async def seed_medical_records(db: AsyncSession, patients, doctors):
    """补播种 5 份完整 SOAP 病历, 让 demo 更丰满"""
    samples = [
        {
            "patient": "李秀芳", "doctor": "dr_zhang",
            "chief_complaint": "胸痛 3 天, 劳累后明显",
            "subjective": "患者3天前劳累后出现胸骨后压榨样疼痛, 伴左肩放射, 持续 5-10 分钟, 休息可缓解。无胸闷　1 次/日。",
            "objective": "BP 145/92mmHg, P 78次/分, T 36.6℃。心肺听诊未闻明显杂音。ECG: 窇性 ST 段压低 0.1mV。肌钙蛋白 I 0.08ng/mL(参考<0.04)。",
            "assessment": "主诊断: 不稳定型心绞痛 (I20.0)。鉴别诊断: 急性非 ST 段抬高型心肌梗死、主动脉夹层、气胸。",
            "plan": "1. 住院 CCU 观察　2. 双抗血小板(阿司匹林+氯吡格雷)+他汀　3. 联系冠脉 CTA/造影　4. 冠心病二级预防教育。",
            "icd10": ["I20.0", "I10"],
            "status": "signed", "quality_score": 96.5,
        },
        {
            "patient": "王志强", "doctor": "dr_zhang",
            "chief_complaint": "胸闷气短",
            "subjective": "近一周在活动后出现胸闷, 需休息 2-3 分钟缓解, 无胸痛, 无夜间阵发。",
            "objective": "BP 132/85mmHg, BMI 28.4。糖化血红蛋白 7.8%(偏高)。心电图大致正常。",
            "assessment": "2 型糖尿病伴心血管风险(E11.9)。需排除隐匿型冠心病。",
            "plan": "1. 调整降糖方案(二甲双胍+恩格列净)　2. 补充冠脉 CTA　3. 低盐低脂饮食 + 运动指导。",
            "icd10": ["E11.9"],
            "status": "signed", "quality_score": 92.0,
        },
        {
            "patient": "陈丽", "doctor": "dr_zhang",
            "chief_complaint": "房颊抗凝随访",
            "subjective": "持续性房颊 3 年, 服用达比加群 110mg 每日两次。无出血不适。",
            "objective": "INR 2.3。BNP 220pg/mL。ECG: 房颊律, 心室率 78 次/分。",
            "assessment": "持续性心房颊动(I48.1) 护理良好, CHA₂DS₂-VASc 3 分。",
            "plan": "1. 继续达比加群 110mg bid　2. 6 个月复查 BNP 及超声心动图　3. 预防跌倒教育。",
            "icd10": ["I48.1"],
            "status": "signed", "quality_score": 94.5,
        },
        {
            "patient": "刘建国", "doctor": "dr_zhang",
            "chief_complaint": "冠脉支架术后 1 月复诊",
            "subjective": "PCI 术后无胸痛发作, 活动耐量改善。双抗血小板 + 他汀 + β 阻常规。",
            "objective": "BP 122/78, P 64。LDL-C 1.6mmol/L(达标)。肌钙蛋白阴性。",
            "assessment": "冠心病 PCI 术后状态, 二级预防达标。",
            "plan": "继续原方案3 个月, 于 2026-09 复查。",
            "icd10": ["I25.1", "Z95.5"],
            "status": "signed", "quality_score": 95.0,
        },
        {
            "patient": "赵梅", "doctor": "dr_zhang",
            "chief_complaint": "心衰随访, 双下肢水肿",
            "subjective": "心衰 NYHA II 级, 近三天双下肢凹陷性水肿加重, 体重 ↗64.5→ 67kg。",
            "objective": "BP 110/72, P 92。BNP 580pg/mL(偏高)。肺部下叶闻少许湿君音。",
            "assessment": "慢性心力衰竭急性加重(I50.9)。",
            "plan": "1. 呈予呼塞米 20mg iv　2. 加量恩格列净25mg qd　3. 限盐<5g/d, 限水 1500ml/d　4. 每日称重。",
            "icd10": ["I50.9"],
            "status": "signed", "quality_score": 93.8,
        },
    ]
    created = []
    for s in samples:
        r = MedicalRecord(
            patient_id=patients[s["patient"]].id,
            doctor_id=doctors[s["doctor"]].id,
            chief_complaint=s["chief_complaint"],
            subjective=s["subjective"], objective=s["objective"],
            assessment=s["assessment"], plan=s["plan"],
            icd10_codes=s["icd10"], record_type="outpatient",
            status=s["status"], ai_assisted=True,
            quality_score=s["quality_score"], quality_issues=[],
            signed_at=datetime.now(timezone.utc).isoformat() if s["status"] == "signed" else None,
        )
        db.add(r); await db.flush(); created.append(r)
    return created


async def seed_prescriptions(db: AsyncSession, patients, doctors, records):
    """5 份示例处方, 覆盖心血管/糖尿病/衰竭多场景"""
    samples = [
        {
            "patient": "李秀芳", "diagnosis": "不稳定型心绞痛",
            "items": [
                {"name": "阿司匹林肠溶片", "spec": "100mg×30片", "dose": "100mg", "freq": "qd", "route": "口服", "qty": 30, "unit": "片", "price": 0.5},
                {"name": "氯吡格雷片", "spec": "75mg×7片", "dose": "75mg", "freq": "qd", "route": "口服", "qty": 28, "unit": "片", "price": 8.2},
                {"name": "瑞舒伐他汀铙片", "spec": "10mg×7片", "dose": "10mg", "freq": "qn", "route": "口服", "qty": 28, "unit": "片", "price": 6.0},
            ],
            "audit_score": 96, "warnings": ["双抗血小板联用, 建议加质子泵抑制剂胃粘膜保护"], "passed": True,
        },
        {
            "patient": "王志强", "diagnosis": "2 型糖尿病",
            "items": [
                {"name": "二甲双胍片", "spec": "0.5g×20片", "dose": "0.5g", "freq": "bid", "route": "口服", "qty": 60, "unit": "片", "price": 0.3},
                {"name": "恩格列净片", "spec": "10mg×7片", "dose": "10mg", "freq": "qd", "route": "口服", "qty": 28, "unit": "片", "price": 4.5},
            ],
            "audit_score": 98, "warnings": [], "passed": True,
        },
        {
            "patient": "陈丽", "diagnosis": "心房颊动抗凝",
            "items": [
                {"name": "达比加群肊胶囊", "spec": "110mg×10粒", "dose": "110mg", "freq": "bid", "route": "口服", "qty": 60, "unit": "粒", "price": 14.5},
            ],
            "audit_score": 94, "warnings": ["老年患者, 建议定期监测肾功能"], "passed": True,
        },
    ]
    for i, s in enumerate(samples):
        rx = Prescription(
            rx_number=f"RX-{generate_id()[:10].upper()}",
            patient_id=patients[s["patient"]].id,
            doctor_id=doctors["dr_zhang"].id,
            medical_record_id=records[i].id if i < len(records) else None,
            diagnosis=s["diagnosis"], instructions="遵医嘱服药, 不适随诊",
            total_amount=sum(it["qty"]*it["price"] for it in s["items"]),
            insurance_amount=sum(it["qty"]*it["price"] for it in s["items"])*0.8,
            self_pay_amount=sum(it["qty"]*it["price"] for it in s["items"])*0.2,
            status="dispensed", ai_assisted=True,
            audit_score=s["audit_score"], audit_warnings=s["warnings"], audit_passed=s["passed"],
        )
        db.add(rx); await db.flush()
        for it in s["items"]:
            db.add(PrescriptionItem(
                prescription_id=rx.id,
                drug_name=it["name"], spec=it["spec"],
                dose=it["dose"], frequency=it["freq"], route=it["route"],
                quantity=it["qty"], unit=it["unit"], unit_price=it["price"],
                duration_days=14, ai_tag="AI推荐",
            ))


async def seed_lab_reports(db: AsyncSession, patients, doctors):
    """5 份检验报告示例"""
    samples = [
        {
            "patient": "李秀芳", "type": "血脂四项",
            "date": "2026-06-10",
            "indicators": [
                {"name": "总胆固醇", "value": 5.8, "unit": "mmol/L", "range": "<5.18", "flag": "high"},
                {"name": "LDL-C", "value": 3.9, "unit": "mmol/L", "range": "<3.4", "flag": "high"},
                {"name": "HDL-C", "value": 1.2, "unit": "mmol/L", "range": "≥1.04", "flag": "normal"},
                {"name": "甘油三醇", "value": 1.8, "unit": "mmol/L", "range": "<1.7", "flag": "high"},
            ],
            "abnormal": 3,
            "ai": "血脂谱紧、低、甘三轻度偏高，结合冠心病史继续他汀强化, LDL-C 达标值 <1.8mmol/L。",
            "sug": ["调整他汀剂量", "3 个月后复查", "低脂饮食 + 运动"],
        },
        {
            "patient": "王志强", "type": "血常规 + HbA1c",
            "date": "2026-06-08",
            "indicators": [
                {"name": "糖化血红蛋白", "value": 7.8, "unit": "%", "range": "<7.0", "flag": "high"},
                {"name": "空腹血糖", "value": 8.2, "unit": "mmol/L", "range": "3.9-6.1", "flag": "high"},
                {"name": "白细胞", "value": 6.5, "unit": "×10^9/L", "range": "4-10", "flag": "normal"},
            ],
            "abnormal": 2,
            "ai": "糖化血红蛋白与空腹血糖偏高，血糖控制不达标。建议调整降糖方案。",
            "sug": ["加用 GLP-1 类药物", "加强饮食运动", "4 周后复查"],
        },
        {
            "patient": "陈丽", "type": "凝血功能",
            "date": "2026-06-09",
            "indicators": [
                {"name": "INR", "value": 2.3, "unit": "", "range": "2.0-3.0", "flag": "normal"},
                {"name": "PT", "value": 16.8, "unit": "s", "range": "11-15", "flag": "high"},
                {"name": "D-二聚体", "value": 0.32, "unit": "mg/L", "range": "<0.5", "flag": "normal"},
            ],
            "abnormal": 1,
            "ai": "INR 在目标范围内，护理良好。PT 偏高为抗凝药物预期效果。",
            "sug": ["继续原方案3 个月"],
        },
        {
            "patient": "刘建国", "type": "肌钙蛋白 + BNP",
            "date": "2026-06-11",
            "indicators": [
                {"name": "肌钙蛋白 I", "value": 0.02, "unit": "ng/mL", "range": "<0.04", "flag": "normal"},
                {"name": "BNP", "value": 85, "unit": "pg/mL", "range": "<100", "flag": "normal"},
            ],
            "abnormal": 0,
            "ai": "术后心肌状态稳定，心衰代偿。",
            "sug": ["原方案继续"],
        },
        {
            "patient": "赵梅", "type": "BNP 随访",
            "date": "2026-06-11",
            "indicators": [
                {"name": "BNP", "value": 580, "unit": "pg/mL", "range": "<100", "flag": "high"},
                {"name": "肭酐", "value": 92, "unit": "μmol/L", "range": "45-84", "flag": "high"},
                {"name": "血钾", "value": 4.2, "unit": "mmol/L", "range": "3.5-5.5", "flag": "normal"},
            ],
            "abnormal": 2,
            "ai": "BNP 明显偏高提示心衰加重，肭酐轻度上升需关注肾功能。",
            "sug": ["加利尿", "限水限盐", "3 天后复查"],
        },
    ]
    for s in samples:
        lab = LabReport(
            report_number=f"LAB-{generate_id()[:10].upper()}",
            patient_id=patients[s["patient"]].id,
            doctor_id=doctors["dr_zhang"].id,
            report_type=s["type"], report_date=s["date"],
            indicators=s["indicators"], abnormal_count=s["abnormal"],
            ai_interpretation=s["ai"], ai_suggestions=s["sug"],
        )
        db.add(lab)


async def seed_notifications(db: AsyncSession, users):
    """v3.6 新增: PRD M1 “消息通知” 迫切稿."""
    items = [
        # 患者 li (patient_li)
        ("patient_li", "appointment", "预约提醒", "您明日 14:30 有与张志明医生的心内科随访预约", "info", "/patient/index.html#appointments"),
        ("patient_li", "medication", "用药提醒", "该服用阿托伐他汀 40mg 咯, 今晚 22:00", "warn", "/patient/index.html#medication"),
        ("patient_li", "report", "报告到达", "您的 心电图 + 血脂四项 报告已出, 点击查看 AI 解读", "info", "/patient/index.html#reports"),
        ("patient_li", "ai_alert", "AI 健康评估", "根据您近期血压记录, 建议尽快复查", "warn", None),
        # 医生 dr_zhang
        ("dr_zhang", "appointment", "今日门诊", "今日您有5位预约患者, 首位 14:30 到诊", "info", "/doctor/workbench.html"),
        ("dr_zhang", "ai_alert", "AI 质控提醒", "您上周 3 份病历缺少家族史, AI 质控建议补充", "warn", "/doctor/quality.html"),
        # 管理员 admin
        ("admin", "system", "DRG 费用预警", "今日1例红色预警病案 (DRG IB29 高费用)", "critical", "/admin/drg.html"),
        ("admin", "system", "药品安全", "AI 处方审核在近 24h 拦截 2 份可能互作用处方", "warn", "/admin/quality.html"),
    ]
    for username, cat, title, content, sev, link in items:
        u = users.get(username)
        if not u:
            continue
        n = Notification(
            user_id=u.id, category=cat, title=title,
            content=content, severity=sev, link=link, is_read=False,
        )
        db.add(n)


async def seed_safety_events(db: AsyncSession, users, patients):
    """v3.6.2 — PRD §07 #139 (Must·V1.0). 播 4 条覆盖不同状态/严重程度的示例."""
    reporter_doctor = users.get("dr_zhang")
    reporter_pharm = users.get("pharm_wang") or users.get("admin")
    admin_user = users.get("admin")
    pat_li = patients.get("patient_li") if patients else None
    items = [
        SafetyEvent(
            event_type="medication_error", severity="ii",
            title="药品名称相近取错事件",
            description="护士误取“阿托伐他汀”为“辛伐他汀”，发取前被质控拦截，未造成伤害。",
            location="住院范1F-软包-302", occurred_at=datetime(2026, 6, 10, 9, 15),
            reporter_id=reporter_pharm.id if reporter_pharm else admin_user.id,
            related_patient_id=pat_li.id if pat_li else None,
            status="resolved", handler_id=admin_user.id if admin_user else None,
            root_cause="药品包装相似 + 人工核对环节缺失 RFID 检查",
            corrective_action="上线药柜 RFID 双重核对 + 高警示药品贴标",
            resolved_at=datetime(2026, 6, 11, 14, 30),
        ),
        SafetyEvent(
            event_type="fall", severity="iii",
            title="住院患者夜间起夜跌倒",
            description="75岁高血压患者凌晨2点独自下床如厕，腿软摔倒，右侧肩部挫伤，未骨折。",
            location="住院范4F-409", occurred_at=datetime(2026, 6, 9, 2, 10),
            reporter_id=reporter_doctor.id if reporter_doctor else admin_user.id,
            status="investigating", handler_id=admin_user.id if admin_user else None,
        ),
        SafetyEvent(
            event_type="misdiagnosis", severity="i",
            title="急诊胸痛患者初诊漏诊主动脉夾层",
            description="高血压男患胸痛初诊为不稳定型心绞痛，4 小时后 CT 证实为 Stanford A 型主动脉夾层。",
            location="急诊抢救室", occurred_at=datetime(2026, 6, 8, 23, 50),
            reporter_id=reporter_doctor.id if reporter_doctor else admin_user.id,
            status="reported",
        ),
        SafetyEvent(
            event_type="device_failure", severity="iv",
            title="输液泵报警频发",
            description="同一型号输液泵近 1 周出现 3 次压力报警误报，设备科已记录。",
            location="ICU", occurred_at=datetime(2026, 6, 7, 16, 0),
            reporter_id=reporter_doctor.id if reporter_doctor else admin_user.id,
            status="closed", handler_id=admin_user.id if admin_user else None,
            root_cause="压力传感器老化", corrective_action="全院分批更换传感器 + 件充重校准",
            resolved_at=datetime(2026, 6, 10, 10, 0),
        ),
    ]
    db.add_all(items)
    await db.flush()


async def seed_research_datasets(db: AsyncSession, users):
    """v3.6.2 — PRD §07 #165 (Must·V1.0). 播 2 个示例数据集."""
    researcher = users.get("prof_zhao") or users.get("admin")
    if not researcher:
        return
    schema1 = [
        {"name": "patient_id", "dtype": "int", "null_count": 0, "sample": "1"},
        {"name": "age", "dtype": "int", "null_count": 0, "sample": "58"},
        {"name": "sex", "dtype": "str", "null_count": 0, "sample": "M"},
        {"name": "sbp", "dtype": "int", "null_count": 2, "sample": "142"},
        {"name": "hba1c", "dtype": "float", "null_count": 3, "sample": "7.8"},
        {"name": "outcome", "dtype": "str", "null_count": 0, "sample": "improved"},
    ]
    preview1 = [
        {"patient_id": 1, "age": 58, "sex": "M", "sbp": 142, "hba1c": 7.8, "outcome": "improved"},
        {"patient_id": 2, "age": 64, "sex": "F", "sbp": 138, "hba1c": 7.2, "outcome": "stable"},
        {"patient_id": 3, "age": 71, "sex": "M", "sbp": 150, "hba1c": 8.5, "outcome": "worsened"},
    ]
    schema2 = [
        {"name": "case_id", "dtype": "str", "null_count": 0, "sample": "ACS-001"},
        {"name": "door_to_balloon_min", "dtype": "int", "null_count": 0, "sample": "68"},
        {"name": "in_hospital_mortality", "dtype": "bool", "null_count": 0, "sample": "False"},
    ]
    preview2 = [
        {"case_id": "ACS-001", "door_to_balloon_min": 68, "in_hospital_mortality": False},
        {"case_id": "ACS-002", "door_to_balloon_min": 95, "in_hospital_mortality": False},
    ]
    items = [
        ResearchDataset(
            owner_id=researcher.id,
            name="高血压随访队列示例",
            original_filename="hypertension_cohort.csv",
            file_format="csv", size_bytes=12345,
            rows=120, columns=6,
            schema_json=schema1, preview_json=preview1,
            notes="示例: 120 例高血压随访队列, 含 SBP / HbA1c / 转归",
        ),
        ResearchDataset(
            owner_id=researcher.id,
            name="ACS 门到球囊时间分析",
            original_filename="acs_dtb.xlsx",
            file_format="xlsx", size_bytes=23456,
            rows=45, columns=3,
            schema_json=schema2, preview_json=preview2,
            notes="示例: ACS 患者门到球囊时间 vs 院内死亡率",
        ),
    ]
    db.add_all(items)
    await db.flush()


async def seed_all(db: AsyncSession):
    users = await seed_users(db)
    depts = await seed_departments(db)
    doctors = await seed_doctors(db, users, depts)
    patients = await seed_patients(db, users)
    await seed_appointments(db, patients, doctors)
    await seed_drg_cases(db)
    records = await seed_medical_records(db, patients, doctors)
    await seed_prescriptions(db, patients, doctors, records)
    await seed_lab_reports(db, patients, doctors)
    await seed_notifications(db, users)  # v3.6
    await seed_safety_events(db, users, patients)       # v3.6.2
    await seed_research_datasets(db, users)             # v3.6.2


# 命令行执行入口
if __name__ == "__main__":
    from app.core.database import AsyncSessionLocal, init_db

    async def _main():
        await init_db()
        async with AsyncSessionLocal() as db:
            await seed_all(db)
            await db.commit()
        print("✓ 演示数据已播种完毕")

    asyncio.run(_main())
