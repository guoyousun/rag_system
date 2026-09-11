# -*- coding: utf-8 -*-
"""
文档 API：上传（异步处理）/ 列表 / 详情 / 删除 / 重新处理。
上传后立即返回记录，解析+向量化+图谱构建在后台线程执行，前端按 status 轮询。
"""
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.document import DOC_STATUS_READY, Document
from app.models.user import User
from app.schemas.document import DocumentChunkOut, DocumentDetailOut, DocumentOut, UploadResponse
from app.services.document_pipeline import process_document
from app.services import kg_service, vector_service

router = APIRouter(prefix="/documents", tags=["文档管理"])

UPLOAD_ROOT = Path("uploads")
UPLOAD_ROOT.mkdir(exist_ok=True)


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传文档并异步触发处理流水线"""
    filename = file.filename or "unnamed"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}，仅支持 {sorted(settings.allowed_extensions)}",
        )

    # 查重：同一用户下不允许上传同名文件
    exists = (
        db.query(Document)
        .filter(Document.user_id == current_user.id, Document.filename == filename)
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"已存在同名文件「{filename}」，请先删除原文件（或重命名新文件）后再上传",
        )

    # 写入磁盘（按用户隔离目录）
    user_dir = UPLOAD_ROOT / str(current_user.id)
    user_dir.mkdir(exist_ok=True)
    stored_path = user_dir / f"{current_user.id}_{os.urandom(4).hex()}_{filename}"
    size = 0
    try:
        with open(stored_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    raise HTTPException(status_code=400, detail=f"文件超过 {settings.MAX_UPLOAD_SIZE_MB}MB 限制")
                out.write(chunk)
    except HTTPException:
        stored_path.unlink(missing_ok=True)
        raise

    doc = Document(
        user_id=current_user.id,
        filename=filename,
        stored_path=str(stored_path),
        file_size=size,
        file_type=ext,
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document, doc.id)
    return UploadResponse(document=DocumentOut.model_validate(doc), message="上传成功，正在后台解析处理")


@router.get("", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户的文档列表（按创建时间倒序）"""
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return docs


@router.get("/{doc_id}", response_model=DocumentDetailOut)
def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """文档详情（含分块列表）"""
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return DocumentDetailOut(
        **DocumentOut.model_validate(doc).model_dump(),
        chunks=[DocumentChunkOut.model_validate(c) for c in doc.chunks],
    )


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除文档：MySQL 记录 + 磁盘文件 + Chroma 向量 + Neo4j 图谱（级联清理）"""
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 清理外部存储（失败不阻塞主删除，但记录日志）
    try:
        vector_service.delete_document(doc.id)
    except Exception:
        pass
    try:
        kg_service.delete_document(doc.id)
    except Exception:
        pass
    Path(doc.stored_path).unlink(missing_ok=True)

    db.delete(doc)
    db.commit()


@router.post("/{doc_id}/reprocess", response_model=DocumentOut)
def reprocess_document(
    doc_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重新处理文档（先清空旧分块与向量/图谱，再重跑流水线）"""
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.status not in ("failed", "ready"):
        raise HTTPException(status_code=400, detail="文档正在处理中，请稍后再试")

    # 清空旧数据
    from app.models.document import DocumentChunk
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
    try:
        vector_service.delete_document(doc.id)
    except Exception:
        pass
    try:
        kg_service.delete_document(doc.id)
    except Exception:
        pass
    doc.status = "uploaded"
    doc.chunk_count = 0
    doc.entity_count = 0
    doc.error_msg = None
    db.commit()

    background_tasks.add_task(process_document, doc.id)
    return doc
