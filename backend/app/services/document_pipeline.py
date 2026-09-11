# -*- coding: utf-8 -*-
"""
文档处理流水线（状态机驱动，独立 session 运行，可在后台线程执行）：
    uploaded → parsing → vectorizing → kg_building → ready
                       └───────────────→ failed（失败自动清理脏数据，可 reprocess 重跑）

流程：解析文件 → 清洗 → 分块 → 分块落 MySQL → 向量化入 Chroma → 实体抽取与图谱入 Neo4j
"""
from app.database.mysql import SessionLocal
from app.models.document import (
    DOC_STATUS_FAILED,
    DOC_STATUS_KG_BUILDING,
    DOC_STATUS_PARSING,
    DOC_STATUS_READY,
    DOC_STATUS_VECTORIZING,
    Document,
    DocumentChunk,
)
from app.services import kg_service, vector_service
from app.services.document_parser import clean_text, parse_document
from app.services.text_splitter import split_text
from app.core.config import settings


def process_document(document_id: int):
    """
    完整处理单个文档。独立打开数据库会话，保证后台线程安全。
    任何一步失败：文档标记 failed 并清理已产生的向量/图谱数据。
    """
    db = SessionLocal()
    doc = db.get(Document, document_id)
    if doc is None:
        db.close()
        return

    try:
        # 0. 清理旧数据（重试/重新处理场景）：旧分块、旧向量、旧图谱，保证干净重跑
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.commit()
        try:
            vector_service.delete_document(doc.id)
        except Exception:
            pass
        try:
            kg_service.delete_document(doc.id)
        except Exception:
            pass

        # 1. 解析
        doc.status = DOC_STATUS_PARSING
        db.commit()
        raw_text = parse_document(doc.stored_path, doc.file_type)
        text = clean_text(raw_text)

        # 2. 分块
        chunk_texts = split_text(text, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
        if not chunk_texts:
            raise ValueError("文档解析后无有效内容")

        # 3. 分块落 MySQL（拿到自增 id 供向量/图谱引用）
        doc.status = DOC_STATUS_VECTORIZING
        db.commit()
        chunk_rows = [
            DocumentChunk(document_id=doc.id, chunk_index=i, content=c)
            for i, c in enumerate(chunk_texts)
        ]
        db.add_all(chunk_rows)
        db.commit()
        chunks_meta = [
            {"chunk_id": row.id, "content": row.content}
            for row in chunk_rows
        ]
        doc.chunk_count = len(chunk_rows)

        # 4. 向量化入 Chroma（千问 embedding）
        vector_service.add_chunks(doc.id, chunks_meta, doc.filename)

        # 5. 实体抽取 + 图谱写入 Neo4j
        doc.status = DOC_STATUS_KG_BUILDING
        db.commit()
        entity_count = kg_service.build_graph_from_chunks(doc.id, doc.filename, chunks_meta)
        doc.entity_count = entity_count

        # 6. 完成
        doc.status = DOC_STATUS_READY
        doc.error_msg = None
        db.commit()
        # 知识库更新 → 清除热点问答缓存，避免旧答案被继续命中
        try:
            from app.database.redis_client import get_redis_client

            redis = get_redis_client()
            cursor = 0
            while True:
                cursor, keys = redis.scan(cursor, match="qa:hot:*", count=200)
                if keys:
                    redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass
    except Exception as exc:
        db.rollback()
        # 清理本次产生的脏数据（向量/图谱），保证 reprocess 干净重跑
        try:
            vector_service.delete_document(doc.id)
        except Exception:
            pass
        try:
            kg_service.delete_document(doc.id)
        except Exception:
            pass
        doc.status = DOC_STATUS_FAILED
        doc.error_msg = f"{type(exc).__name__}: {exc}"[:1000]
        db.commit()
    finally:
        db.close()
