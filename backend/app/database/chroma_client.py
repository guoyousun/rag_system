# -*- coding: utf-8 -*-
"""
Chroma 向量数据库连接（持久化到本地目录）。
集合：document_chunks —— 每个 chunk 一条记录，metadata 携带 document_id / source。
"""
import chromadb

from app.core.config import settings

CHUNKS_COLLECTION = "document_chunks"

_client = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    return _client


def get_chunks_collection():
    """文档分块向量集合（余弦相似度）"""
    return get_chroma_client().get_or_create_collection(
        name=CHUNKS_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def close_chroma():
    global _client
    if _client is not None:
        _client.clear_system_cache()
        _client = None
