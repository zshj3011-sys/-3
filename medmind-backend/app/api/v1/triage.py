"""AI 预问诊 API - 患者端核心"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.security import generate_id
from app.models.ai_conversation import AIConversation, AIMessage
from app.models.user import User
from app.services.agents import TriageAgent
from app.schemas.ai import TriageStartRequest, TriageMessageRequest, TriageResponse, AIMessageOut, TriageSummary
from app.schemas.common import StandardResponse

router = APIRouter()
_agent = TriageAgent()


@router.post("/start", response_model=StandardResponse[TriageResponse], summary="启动预问诊会话")
async def start_triage(
    body: TriageStartRequest,
    db: AsyncSession = Depends(get_db),
    current: User | None = Depends(get_current_user_optional),
):
    session_id = generate_id()
    conv = AIConversation(
        session_id=session_id,
        user_id=current.id if current else None,
        patient_id=body.patient_id,
        scenario="pre_triage",
        agent_name="triage",
    )
    db.add(conv)
    await db.flush()

    # 第一条 AI 消息: 问主诉
    if body.chief_complaint:
        # 用户已经报了主诉, 跳过第一问
        db.add(AIMessage(conversation_id=conv.id, role="user", content=body.chief_complaint))
        history = [{"role": "user", "content": body.chief_complaint}]
        step = 1
    else:
        history = []
        step = 0

    data = await _agent.next_message(history, step)
    msg = AIMessage(
        conversation_id=conv.id,
        role="assistant",
        content=data.get("content", "请描述您的症状"),
        quick_replies=data.get("quick_replies", []),
    )
    db.add(msg)

    return StandardResponse(data=TriageResponse(
        session_id=session_id,
        ai_message=AIMessageOut(
            role="assistant",
            content=msg.content,
            quick_replies=msg.quick_replies,
        ),
        step=step,
        completed=False,
    ))


async def _send_message_impl(body: TriageMessageRequest, db: AsyncSession):
    res = await db.execute(select(AIConversation).where(AIConversation.session_id == body.session_id))
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(404, "会话不存在")
    if conv.status != "active":
        raise HTTPException(400, "会话已结束")

    # 用户消息入库
    db.add(AIMessage(conversation_id=conv.id, role="user", content=body.message))
    await db.flush()

    # 加载历史
    msgs = (await db.execute(
        select(AIMessage).where(AIMessage.conversation_id == conv.id).order_by(AIMessage.id)
    )).scalars().all()
    history = [{"role": m.role, "content": m.content} for m in msgs]
    # 算 step: 用户消息数
    user_count = sum(1 for m in msgs if m.role == "user")
    step = user_count

    data = await _agent.next_message(history, step)

    completed = bool(data.get("completed"))
    summary = None
    if completed:
        # 完成 -> 写 SOAP 到 conversation
        soap = data.get("soap") or {}
        conv.status = "completed"
        conv.summary = f"{data.get('chief_complaint','')} -> {data.get('suggested_department','')}"
        conv.soap_summary = soap
        conv.triage_level = data.get("triage_level")
        conv.confidence = data.get("confidence", 0.0)
        summary = data

        ai_content = data.get("content", "✅ 预问诊摘要已生成")
    else:
        ai_content = data.get("content", "")

    msg = AIMessage(
        conversation_id=conv.id, role="assistant",
        content=ai_content,
        quick_replies=data.get("quick_replies", []),
    )
    db.add(msg)
    await db.flush()

    return StandardResponse(data=TriageResponse(
        session_id=conv.session_id,
        ai_message=AIMessageOut(role="assistant", content=msg.content, quick_replies=msg.quick_replies),
        step=step,
        completed=completed,
        summary=summary,
    ))


@router.post("/message", response_model=StandardResponse[TriageResponse], summary="发送消息(多轮·兼容方式)")
async def send_message(body: TriageMessageRequest, db: AsyncSession = Depends(get_db)):
    """兼容方式: session_id 在 body 中。保留与原有前端兼容。"""
    return await _send_message_impl(body, db)


@router.post("/{session_id}/message", response_model=StandardResponse[TriageResponse], summary="发送消息(PRD路径参数式)")
async def send_message_with_path_id(
    session_id: str,
    body: TriageMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """PRD 4.2 要求的形式: session_id 作为路径参数。
    
    与 POST /message 同效, body 中的 session_id 可选 — 优先使用路径参数。
    """
    body.session_id = session_id
    return await _send_message_impl(body, db)


@router.get("/{session_id}/summary", response_model=StandardResponse[TriageSummary], summary="获取摘要")
async def get_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AIConversation).where(AIConversation.session_id == session_id))
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(404, "会话不存在")
    soap = conv.soap_summary or {}
    return StandardResponse(data=TriageSummary(
        session_id=session_id,
        soap=soap,
        chief_complaint=(conv.summary or "").split(" -> ")[0] if conv.summary else "",
        suggested_department=(conv.summary or "").split(" -> ")[-1] if " -> " in (conv.summary or "") else None,
        triage_level=conv.triage_level or "green",
        confidence=conv.confidence or 0.0,
        suggested_doctors=[],
    ))
