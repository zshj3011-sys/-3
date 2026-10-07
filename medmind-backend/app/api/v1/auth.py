"""认证相关 API"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, RegisterRequest, UserPublic
from app.schemas.common import StandardResponse

router = APIRouter()


@router.post("/register", response_model=StandardResponse[UserPublic], summary="用户注册")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 检查重名
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "用户名已存在")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        email=body.email,
        phone=body.phone,
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.flush()
    return StandardResponse(data=UserPublic.model_validate(user))


@router.post("/login", response_model=StandardResponse[TokenResponse], summary="用户登录")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.username == body.username))
    user = res.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        # 写审计
        db.add(AuditLog(username=body.username, action="login", result="failure",
                        error_message="invalid_credentials"))
        raise HTTPException(401, "用户名或密码错误")
    if not user.is_active:
        raise HTTPException(403, "账号已停用")
    # MFA 校验 (如启用)
    if user.mfa_enabled:
        if not body.mfa_code:
            raise HTTPException(403, "需要 MFA 验证码")
        # TOTP 验证逻辑略 (依赖 pyotp)
    user.last_login_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    db.add(AuditLog(user_id=user.id, username=user.username, action="login", result="success"))

    token = create_access_token(user.id, extra={"role": user.role, "username": user.username})
    refresh = create_refresh_token(user.id)
    return StandardResponse(data=TokenResponse(
        access_token=token,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    ))


@router.post("/refresh", response_model=StandardResponse[TokenResponse], summary="刷新 Token")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "无效或已过期的 refresh_token")
    user = await db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "用户不存在或停用")
    token = create_access_token(user.id, extra={"role": user.role, "username": user.username})
    refresh = create_refresh_token(user.id)
    return StandardResponse(data=TokenResponse(
        access_token=token, refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    ))


@router.post("/logout", response_model=StandardResponse[dict], summary="登出")
async def logout(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db.add(AuditLog(user_id=current.id, username=current.username, action="logout", result="success"))
    return StandardResponse(data={"ok": True})


@router.get("/me", response_model=StandardResponse[UserPublic], summary="获取当前用户")
async def me(current: User = Depends(get_current_user)):
    return StandardResponse(data=UserPublic.model_validate(current))
