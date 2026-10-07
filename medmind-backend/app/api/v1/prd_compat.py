"""PRD 08_API接口文档.md 全字面兼容路由

v3.6 新增: 把 PRD 中所有官方路径都精确对齐, 让客户/前端按 PRD 文档调用零差异。
通过转发到现有实现, 避免代码重复。
"""
from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.api.v1 import records as _records_mod
from app.api.v1 import ws as _ws_mod
from app.schemas.ai import SOAPGenerateRequest, SOAPDraft
from app.schemas.common import StandardResponse

router = APIRouter()


@router.post(
    "/ai/consultation/generate-note",
    response_model=StandardResponse[SOAPDraft],
    summary="PRD §5.1: AI 生成病历草稿 (PRD 字面路径)",
    tags=["PRD 兼容"],
)
async def prd_generate_note(
    body: SOAPGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """PRD 08 §5.1 定义的官方路径 — 转发到 /records/ai-draft 的同一实现。"""
    return await _records_mod.ai_draft(body, db, current)


# PRD §9 WebSocket 路径 -- 字面对齐
@router.websocket("/ws/asr/stream")
async def prd_ws_asr_stream(websocket: WebSocket, demo: int = 1):
    """PRD §9.1 WebSocket /ws/asr/stream — 转发到 /v1/ws/asr 同一实现。"""
    await _ws_mod.ws_asr(websocket, demo)


@router.websocket("/ws/ai/suggestions")
async def prd_ws_ai_suggestions(websocket: WebSocket):
    """PRD §9.2 WebSocket /ws/ai/suggestions — 转发到 /v1/ws/ai-suggest 同一实现。"""
    await _ws_mod.ws_ai_suggest(websocket)
