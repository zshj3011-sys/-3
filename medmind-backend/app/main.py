"""MedMind Nexus 后端入口"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import api_router
from app.schemas.common import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子"""
    logger.info(f"🚀 MedMind Nexus API 启动 · env={settings.APP_ENV} · LLM={settings.LLM_PROVIDER}")
    # 初始化数据库
    await init_db()
    # 检查是否需要播种数据
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(func.count(User.id)))).scalar() or 0
        if total == 0:
            logger.info("数据库为空, 自动播种演示数据...")
            from scripts.seed import seed_all
            await seed_all(db)
            await db.commit()
            logger.info("✓ 演示数据播种完毕")
    yield
    logger.info("👋 MedMind Nexus API 关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="""
MedMind Nexus 医智中枢后端 API。
- 认证: JWT (POST /v1/auth/login)
- AI: 预问诊 / SOAP 病历 / 诊断辅助 / 处方审核 / DRG / 报告解读
- 科研: 文献检索 / 标书生成 / 论文润色
- 管理端: 运营驾驶舱 / DRG 控费 / 质控
- WebSocket: 实时语音转写 / AI 建议推送
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# 全局异常 -> 统一响应
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(code=exc.status_code, message=str(exc.detail)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(code=422, message="请求参数校验失败", detail=exc.errors()).model_dump(),
    )


# 健康检查
@app.get("/health", summary="健康检查", tags=["系统"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0",
            "llm_provider": settings.LLM_PROVIDER, "demo_mode": settings.DEMO_MODE}


@app.get("/", summary="根路径", tags=["系统"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "frontend": "/web",
        "openapi": "/openapi.json",
    }


# 静态前端 - 把 MedMindNexus 文件夹挂在 /web
_FRONTEND_DIR = os.environ.get(
    "FRONTEND_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "MedMindNexus")
)
_FRONTEND_DIR = os.path.abspath(_FRONTEND_DIR)
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/web", StaticFiles(directory=_FRONTEND_DIR, html=True), name="web")
    logger.info(f"📂 前端挂载: /web -> {_FRONTEND_DIR}")
else:
    logger.warning(f"⚠️  前端目录不存在: {_FRONTEND_DIR}")
