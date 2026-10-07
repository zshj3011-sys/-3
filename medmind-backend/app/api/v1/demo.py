"""演示端点 - 用于前端 demo 快速 mock 数据 (无需登录)"""
from fastapi import APIRouter
from app.schemas.common import StandardResponse

router = APIRouter()


@router.get("/wechat-screens", response_model=StandardResponse[dict],
            summary="患者端微信小程序演示数据")
async def wechat_demo():
    return StandardResponse(data={
        "patient": {"name": "李秀芳", "gender": "女", "age": 56,
                    "tags": ["高血压", "高脂血症"], "adherence_rate": 0.93},
        "today_meds": [
            {"name": "阿托伐他汀钙片", "dose": "20mg", "time": "22:00", "status": "taken"},
            {"name": "硝苯地平控释片", "dose": "30mg", "time": "08:00",
             "status": "due_in_minutes", "minutes": 14},
            {"name": "阿司匹林肠溶片", "dose": "100mg", "time": "12:00", "status": "pending"},
        ],
        "indicators": [
            {"name": "收缩压", "value": 138, "unit": "mmHg", "flag": "high"},
            {"name": "空腹血糖", "value": 5.8, "unit": "mmol/L", "flag": "normal"},
            {"name": "LDL-C", "value": 4.2, "unit": "mmol/L", "flag": "high"},
        ],
    })


@router.get("/doctor-schedule", response_model=StandardResponse[list], summary="医生今日排班")
async def doctor_schedule():
    return StandardResponse(data=[
        {"time": "14:30", "patient": "李秀芳", "gender": "女", "age": 56,
         "type": "复诊", "tag": "高血压、高脂血症", "now": True},
        {"time": "15:00", "patient": "王志强", "gender": "男", "age": 48,
         "type": "初诊", "tag": "胸闷气短"},
        {"time": "15:30", "patient": "陈丽", "gender": "女", "age": 62,
         "type": "复诊", "tag": "房颤,抗凝随访"},
        {"time": "16:00", "patient": "刘建国", "gender": "男", "age": 55,
         "type": "复诊", "tag": "冠脉支架术后1月"},
        {"time": "16:30", "patient": "赵梅", "gender": "女", "age": 67,
         "type": "复诊", "tag": "心衰 NYHA II 级"},
    ])
