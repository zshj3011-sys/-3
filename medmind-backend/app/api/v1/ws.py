"""WebSocket 接口 - 实时 ASR 语音转写 + AI 建议实时推送"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

router = APIRouter()


# 演示用医患对话脚本 - 真实语音 ASR 由 Whisper/Azure 等替换
_DEMO_DIALOG = [
    {"role": "doctor", "text": "您好,请坐。今天哪里不舒服?"},
    {"role": "patient", "text": "医生,我这胸口疼,断断续续三天了。"},
    {"role": "doctor", "text": "疼痛是什么样子的?闷痛还是刺痛?"},
    {"role": "patient", "text": "感觉是压着一块大石头,有时候还会放射到左肩。"},
    {"role": "doctor", "text": "什么时候疼得比较厉害?"},
    {"role": "patient", "text": "活动的时候特别明显,休息一会儿能缓解。出过几次汗。"},
    {"role": "doctor", "text": "您之前有高血压、糖尿病吗?吃什么药?"},
    {"role": "patient", "text": "高血压 8 年了,在吃硝苯地平。血脂也偏高,医生让我吃他汀。"},
    {"role": "doctor", "text": "吸烟吗?家里有心脏病史吗?"},
    {"role": "patient", "text": "吸烟 20 年,一天 10 支。父亲 60 岁心梗去世的。"},
]


@router.websocket("/v1/ws/asr")
async def ws_asr(websocket: WebSocket, demo: int = Query(1)):
    """实时语音转写 WS

    协议:
      - 客户端发送音频 chunk (二进制) 或文本指令
      - 服务端返回 {type:"partial"|"final", role, text}
      - demo=1 时不需音频, 按时序自动播放演示脚本
    """
    await websocket.accept()
    try:
        if demo:
            for line in _DEMO_DIALOG:
                # 模拟"边说边出字"
                acc = ""
                for ch in line["text"]:
                    acc += ch
                    if len(acc) % 3 == 0:
                        await websocket.send_json({
                            "type": "partial", "role": line["role"], "text": acc,
                        })
                        await asyncio.sleep(0.05)
                await websocket.send_json({
                    "type": "final", "role": line["role"], "text": line["text"],
                })
                await asyncio.sleep(0.8)
            await websocket.send_json({"type": "done"})
        else:
            # 真实模式: 接收音频, 调用 ASR 服务 (此处占位)
            while True:
                msg = await websocket.receive()
                if "bytes" in msg:
                    # TODO: 调用 Whisper/Azure ASR
                    await websocket.send_json({"type": "partial", "text": "[ASR placeholder]"})
                elif msg.get("type") == "websocket.disconnect":
                    break
    except WebSocketDisconnect:
        return


@router.websocket("/v1/ws/ai-suggest")
async def ws_ai_suggest(websocket: WebSocket):
    """AI 建议实时推送 - 跟随诊间助手对话动态出建议"""
    await websocket.accept()
    suggestions = [
        {"category": "diagnosis", "title": "可能诊断", "confidence": 0.86,
         "content": "不稳定型心绞痛 (UA) - ICD I20.0"},
        {"category": "test", "title": "建议检查",
         "content": "心电图 / 肌钙蛋白 / 心肌酶谱 / 胸部 X 光"},
        {"category": "medication", "title": "建议用药",
         "content": "阿司匹林 100mg qd + 氯吡格雷 75mg qd + 阿托伐他汀 40mg qn"},
        {"category": "guideline", "title": "依据指南",
         "content": "2026 ESC 慢性冠脉综合征指南 + 中国 ACS 共识 2024"},
    ]
    try:
        for s in suggestions:
            await asyncio.sleep(2.5)
            await websocket.send_json({"type": "suggestion", **s})
        await websocket.send_json({"type": "done"})
        # 保持连接
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
