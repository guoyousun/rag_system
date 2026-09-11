# -*- coding: utf-8 -*-
"""
向量检索服务（第二种检索方式）。
- 存储：Chroma 持久化集合 document_chunks
- 向量：千问 text-embedding-v3（OpenAI 兼容端点）
- id 约定：Chroma id = f"chunk-{db_chunk_id}"，metadata 携带 document_id / source
"""
from app.core.config import settings
from app.database.chroma_client import get_chunks_collection
from app.services.embedding_service import embed_texts


def _chroma_id(chunk_id: int) -> str:
    return f"chunk-{chunk_id}"


def add_chunks(document_id: int, chunks: list[dict], source: str):
    """
    批量向量化并写入 Chroma。
    chunks: [{"chunk_id": int, "content": str}]
    千问 embedding 兼容端点单次请求上限 20 条，因此按 20 条/批分批写入。
    """
    if not chunks:
        return 0
    BATCH = 20  # dashscope 兼容端点 input.contents 上限
    total = 0
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        texts = [c["content"] for c in batch]
        embeddings = embed_texts(texts)
        ids = [_chroma_id(c["chunk_id"]) for c in batch]
        metadatas = [
            {
                "document_id": str(document_id),
                "source": source,
                "chunk_id": str(c["chunk_id"]),
            }
            for c in batch
        ]
        get_chunks_collection().upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total += len(batch)
    return total


def search(query: str, top_k: int | None = None, document_ids: list[int] | None = None) -> list[tuple[str, float]]:
    """
    向量检索，返回 [(chunk_id_str, score)] 按相似度降序。
    document_ids 非空时按文档过滤（用于文档级检索调试）。
    """
    top_k = top_k or settings.VECTOR_TOP_K
    query_embedding = embed_texts([query])[0]
    where = None
    if document_ids:
        where = {"document_id": {"$in": [str(did) for did in document_ids]}}
    result = get_chunks_collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["metadatas", "distances"],
    )
    if not result["ids"] or not result["ids"][0]:
        return []
    ids = result["ids"][0]
    distances = result["distances"][0] if result.get("distances") else [1.0] * len(ids)
    # Chroma distance（cosine）越小越相似，转换为得分：score = 1 - distance
    return [(cid.removeprefix("chunk-"), float(1 - d)) for cid, d in zip(ids, distances)]


def delete_document(document_id: int):
    """删除某文档的全部向量"""
    col = get_chunks_collection()
    while True:
        result = col.get(where={"document_id": {"$eq": str(document_id)}}, limit=1000)
        ids = result.get("ids") or []
        if not ids:
            break
        col.delete(ids=ids)
