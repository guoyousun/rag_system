# -*- coding: utf-8 -*-
"""
检索调试与图谱 API：
- POST /search       三路检索结果对比（用于验证三种检索方式、调参）
- GET  /graph       知识图谱概览数据（前端可视化）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.document import Document, DocumentChunk
from app.schemas.chat import GraphOverview, SearchDebugResponse, SearchHit
from app.services.bm25_service import bm25_service
from app.services.kg_service import get_graph_overview
from app.services.kg_service import search as kg_search
from app.services.vector_service import search as vector_search
from app.services.fusion_service import rrf_fuse

router = APIRouter(tags=["检索调试"])


def _chunk_details(db: Session, hits: list[tuple[str, float]]) -> list[SearchHit]:
    """把 (chunk_id_str, score) 列表补全为详情"""
    if not hits:
        return []
    ids = [int(cid) for cid, _ in hits]
    rows = (
        db.query(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(DocumentChunk.id.in_(ids))
        .all()
    )
    detail_map = {row[0].id: row for row in rows}
    result = []
    for cid, score in hits:
        if int(cid) in detail_map:
            chunk, doc = detail_map[int(cid)]
            result.append(SearchHit(
                chunk_id=chunk.id,
                document_id=doc.id,
                filename=doc.filename,
                content=chunk.content[:200],
                score=round(score, 4),
            ))
    return result


@router.post("/search", response_model=SearchDebugResponse)
def debug_search(
    body: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """三路检索对比调试：{query, top_k?} → 返回 BM25/向量/KG/融合 四组命中"""
    query = (body.get("query") or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query 不能为空")
    top_k = int(body.get("top_k") or 5)

    bm25_hits = []
    vector_hits = []
    kg_hits = []
    try:
        bm25_hits = bm25_service.search(db, query, top_k)
    except Exception:
        pass
    try:
        vector_hits = vector_search(query, top_k)
    except Exception:
        pass
    try:
        kg_hits = kg_search(query, top_k)
    except Exception:
        pass

    fused = rrf_fuse(
        [bm25_hits, vector_hits, kg_hits],
        weights=[settings.FUSION_WEIGHT_BM25, settings.FUSION_WEIGHT_VECTOR, settings.FUSION_WEIGHT_KG],
    )[:top_k]

    return SearchDebugResponse(
        query=query,
        bm25_hits=_chunk_details(db, bm25_hits),
        vector_hits=_chunk_details(db, vector_hits),
        kg_hits=_chunk_details(db, kg_hits),
        fused_hits=_chunk_details(db, fused),
    )


@router.get("/graph", response_model=GraphOverview)
def graph_overview(
    limit: int = Query(default=60, ge=1, le=300),
    current_user=Depends(get_current_user),
):
    """知识图谱概览（前端 ECharts 力导向图）"""
    try:
        return get_graph_overview(limit)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"图谱服务不可用: {exc}")
