# -*- coding: utf-8 -*-
"""
FastAPI 应用入口。
启动方式（backend 目录下）：
    uvicorn app.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, chats, documents, search
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("multi-mode-qa")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("%s 启动中...", settings.APP_NAME)
    logger.info("LLM 模型: %s | Embedding 模型: %s", settings.QWEN_LLM_MODEL, settings.QWEN_EMBEDDING_MODEL)
    logger.info("API 文档: http://127.0.0.1:8000/docs")
    # 恢复中断的文档处理任务：上次进程退出时可能遗留 parsing/vectorizing/kg_building
    # 状态，重置为 failed，避免永久卡住（可在前端点击"重试"重新处理）
    try:
        from app.database.mysql import SessionLocal
        from app.models.document import DOC_STATUS_FAILED, Document
        db = SessionLocal()
        stuck = (
            db.query(Document)
            .filter(Document.status.in_(["parsing", "vectorizing", "kg_building"]))
            .all()
        )
        for doc in stuck:
            doc.status = DOC_STATUS_FAILED
            doc.error_msg = "服务重启导致处理中断，请点击「重试」重新处理"
        db.commit()
        if stuck:
            logger.info("已重置 %d 个中断的文档处理任务为 failed", len(stuck))
        db.close()
    except Exception as exc:  # 基础设施未就绪时不阻断启动
        logger.warning("文档状态恢复跳过: %s", exc)
    logger.info("=" * 60)
    yield
    # 关闭连接
    from app.database.redis_client import close_redis
    from app.database.neo4j_client import close_driver
    from app.database.chroma_client import close_chroma
    close_redis()
    close_driver()
    close_chroma()
    logger.info("应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="BM25 + 向量 + 知识图谱 三路混合检索的工业软件平台智能问答系统",
    lifespan=lifespan,
)

# CORS（前端开发服务器）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(chats.router, prefix=settings.API_PREFIX)
app.include_router(search.router, prefix=settings.API_PREFIX)


@app.get("/api/v1/health")
def health():
    """健康检查：报告各存储/服务连通状态"""
    status = {"app": "ok", "llm_configured": bool(settings.QWEN_API_KEY and not settings.QWEN_API_KEY.startswith("sk-your"))}

    try:
        from sqlalchemy import text as sql_text
        from app.database.mysql import SessionLocal
        db = SessionLocal()
        db.execute(sql_text("SELECT 1"))
        db.close()
        status["mysql"] = "ok"
    except Exception as exc:
        status["mysql"] = f"error: {exc}"

    try:
        from app.database.redis_client import get_redis_client
        get_redis_client().ping()
        status["redis"] = "ok"
    except Exception as exc:
        status["redis"] = f"error: {exc}"

    try:
        from app.database.neo4j_client import get_driver
        get_driver().verify_connectivity()
        status["neo4j"] = "ok"
    except Exception as exc:
        status["neo4j"] = f"error: {exc}"

    try:
        from app.database.chroma_client import get_chroma_client
        get_chroma_client().heartbeat()
        status["chroma"] = "ok"
    except Exception as exc:
        status["chroma"] = f"error: {exc}"

    return status


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底异常：避免堆栈直接暴露给前端"""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"服务器内部错误: {type(exc).__name__}"})
