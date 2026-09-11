# -*- coding: utf-8 -*-
"""
会话与问答 API：会话 CRUD + 消息发送 + 流式 SSE。
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.chat import ChatMessage, Conversation
from app.models.user import User
from app.schemas.chat import ChatAnswerResponse, ChatMessageOut, ConversationCreate, ConversationOut, MessageCreate
from app.services.llm_service import chat_stream
from app.services.rag_service import answer_question

router = APIRouter(prefix="/chats", tags=["智能问答"])


# ============================================================
# 会话管理
# ============================================================
@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = Conversation(user_id=current_user.id, title=body.title or "新对话")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return convs


@router.get("/{conv_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == current_user.id).first()
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv.messages


@router.delete("/{conv_id}", status_code=204)
def delete_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == current_user.id).first()
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(conv)
    db.commit()


# ============================================================
# 问答（普通模式）
# ============================================================
@router.post("/{conv_id}/messages", response_model=ChatAnswerResponse)
def send_message(
    conv_id: int,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发送问题，执行多模式检索 + 千问生成，返回答案与引用来源"""
    try:
        result = answer_question(db, current_user.id, conv_id, body.content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"大模型服务暂不可用：{exc}")
    return ChatAnswerResponse(
        conversation_id=conv_id,
        message_id=result["message_id"],
        answer=result["answer"],
        sources=result["sources"],
        retrieval_stats=result["retrieval_stats"],
    )


# ============================================================
# 问答（流式 SSE 模式）
# ============================================================
@router.post("/{conv_id}/messages/stream")
async def send_message_stream(
    conv_id: int,
    body: MessageCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    SSE 流式问答：先返回检索元数据事件，再逐段推送答案文本。
    前端可用 fetch + ReadableStream 消费，事件格式：data: {json}\n\n
    """
    from app.database.mysql import SessionLocal

    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == current_user.id).first()
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    def event_stream():
        # 独立 session：流式生成期间持有连接
        sdb = SessionLocal()
        try:
            try:
                result = answer_question(sdb, current_user.id, conv_id, body.content)
            except RuntimeError as exc:
                yield f"data: {json.dumps({'event': 'error', 'detail': f'大模型服务暂不可用：{exc}'}, ensure_ascii=False)}\n\n"
                return
            # 元数据事件（检索统计 + 来源）
            yield f"data: {json.dumps({'event': 'meta', 'retrieval_stats': result['retrieval_stats'], 'sources': result['sources']}, ensure_ascii=False)}\n\n"
            # 分段推送答案（模拟增量，可按句切分）
            answer = result["answer"]
            step = 8
            for i in range(0, len(answer), step):
                yield f"data: {json.dumps({'event': 'delta', 'content': answer[i:i+step]}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'message_id': result['message_id']}, ensure_ascii=False)}\n\n"
        finally:
            sdb.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
