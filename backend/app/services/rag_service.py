# -*- coding: utf-8 -*-
"""
RAG 问答编排：多模式协同检索 + 千问生成。
流程：
  1. Redis 热点缓存命中检查（query 维度，TTL 可配）
  2. 三路并行检索（BM25 / 向量 / 知识图谱），单路失败降级不影响整体
  3. RRF 加权融合，取 top-N 分块
  4. 组装带上下文的 prompt，调用千问（OpenAI 兼容端点）
  5. 落库会话消息 + 写缓存
"""
import hashlib
import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.redis_client import get_redis_client
from app.models.chat import ChatMessage, Conversation
from app.models.document import Document, DocumentChunk
from app.services import fusion_service
from app.services.bm25_service import bm25_service
from app.services.kg_service import search as kg_search
from app.services.llm_service import chat
from app.services.vector_service import search as vector_search

_SYSTEM_PROMPT = (
    "你是工业软件平台的多模式协同智能问答助手。"
    "请严格依据给定的参考资料回答用户问题，做到：\n"
    "1. 答案准确、专业，优先引用资料中的具体数据、参数与结论；\n"
    "2. 资料不足以回答时，明确说明\"现有资料未覆盖该问题\"，不要编造；\n"
    "3. 回答使用简体中文，条理清晰，涉及多个要点时分点说明；\n"
    "4. 不透露检索过程的内部实现细节。"
)

_HISTORY_LIMIT = 6  # 携带最近 N 条历史消息


def answer_question(db: Session, user_id: int, conversation_id: int, question: str) -> dict:
    """
    执行一次完整问答，返回:
    {"answer": str, "sources": [...], "retrieval_stats": {...}, "message_id": int}
    """
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise ValueError("会话不存在或无权访问")

    # ---------- 1. 热点缓存 ----------
    redis = get_redis_client()
    cache_key = f"qa:hot:{hashlib.md5(question.encode('utf-8')).hexdigest()}"
    cached = None
    try:
        raw = redis.get(cache_key)
        if raw:
            cached = json.loads(raw)
    except Exception:
        pass  # Redis 不可用时跳过缓存，不影响主流程

    # ---------- 2. 三路检索（单路失败降级）----------
    bm25_hits: list[tuple[str, float]] = []
    vector_hits: list[tuple[str, float]] = []
    kg_hits: list[tuple[str, float]] = []

    try:
        bm25_hits = bm25_service.search(db, question)
    except Exception:
        pass
    try:
        vector_hits = vector_search(question)
    except Exception:
        pass
    try:
        kg_hits = kg_search(question)
    except Exception:
        pass

    # ---------- 3. RRF 融合 ----------
    fused = fusion_service.rrf_fuse(
        [bm25_hits, vector_hits, kg_hits],
        weights=[
            settings.FUSION_WEIGHT_BM25,
            settings.FUSION_WEIGHT_VECTOR,
            settings.FUSION_WEIGHT_KG,
        ],
    )
    top_fused = fused[: settings.FUSION_TOP_K]

    # ---------- 4. 取分块详情 ----------
    chunk_id_set = {int(cid) for cid, _ in top_fused}
    chunks: dict[int, tuple[DocumentChunk, Document]] = {}
    if chunk_id_set:
        rows = (
            db.query(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(DocumentChunk.id.in_(chunk_id_set))
            .all()
        )
        chunks = {str(row[0].id): (row[0], row[1]) for row in rows}

    sources = []
    for cid, score in top_fused:
        if cid in chunks:
            chunk, doc = chunks[cid]
            sources.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "filename": doc.filename,
                "content": chunk.content,
                "score": round(score, 4),
                "retrieval_type": "fusion",
            })

    retrieval_stats = {
        "bm25": len(bm25_hits),
        "vector": len(vector_hits),
        "kg": len(kg_hits),
        "fusion": len(top_fused),
        "cache_hit": cached is not None,
    }

    # ---------- 5. 生成答案 ----------
    if cached is not None:
        answer = cached["answer"]
        sources = cached.get("sources", sources)
    else:
        answer = _generate_answer(db, conversation_id, question, sources)

    # ---------- 6. 落库 + 写缓存 ----------
    user_msg = ChatMessage(conversation_id=conversation_id, role="user", content=question)
    assistant_msg = ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        sources_json=json.dumps(sources, ensure_ascii=False),
        retrieval_stats_json=json.dumps(retrieval_stats, ensure_ascii=False),
    )
    db.add_all([user_msg, assistant_msg])
    # 会话标题：取首问前 20 字
    if conversation.title == "新对话":
        conversation.title = question[:20]
    db.commit()
    db.refresh(assistant_msg)

    if cached is None:
        try:
            redis.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps({"answer": answer, "sources": sources}, ensure_ascii=False),
            )
        except Exception:
            pass

    return {
        "answer": answer,
        "sources": sources,
        "retrieval_stats": retrieval_stats,
        "message_id": assistant_msg.id,
    }


def _generate_answer(db: Session, conversation_id: int, question: str, sources: list[dict]) -> str:
    """组装 prompt 并调用千问"""
    context_parts = []
    for i, src in enumerate(sources, 1):
        context_parts.append(f"[资料{i}] 《{src['filename']}》\n{src['content'][:800]}")
    context = "\n\n".join(context_parts) if context_parts else "（未检索到相关参考资料）"

    # 历史消息（保留最近 N 条）
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.id.desc())
        .limit(_HISTORY_LIMIT)
        .all()
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(history_rows)
    ]

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"【参考资料】\n{context}\n\n【问题】\n{question}\n\n请结合参考资料回答。",
    })
    return chat(messages)
