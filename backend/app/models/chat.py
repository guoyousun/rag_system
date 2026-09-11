# -*- coding: utf-8 -*-
"""
会话与消息模型：
- Conversation 一次问答会话
- ChatMessage   会话内消息（user/assistant），assistant 消息附带检索来源与检索统计
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.mysql import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="新对话", comment="会话标题（取首问前 20 字）")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.id")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(16), nullable=False, comment="user / assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    sources_json = Column(Text, nullable=True, comment="引用来源 JSON（assistant 消息）")
    retrieval_stats_json = Column(Text, nullable=True, comment="三路检索统计 JSON（assistant 消息）")
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
