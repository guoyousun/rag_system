# -*- coding: utf-8 -*-
"""会话 / 问答 / 检索调试 Schema"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", max_length=255)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000, description="用户问题")


class SourceRef(BaseModel):
    """单条引用来源"""
    chunk_id: int
    document_id: int
    filename: str
    content: str
    score: float = 0.0
    retrieval_type: str = "fusion"  # bm25 / vector / kg / fusion


class RetrievalStats(BaseModel):
    """三路检索命中统计"""
    bm25: int = 0
    vector: int = 0
    kg: int = 0
    fusion: int = 0
    cache_hit: bool = False


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ChatAnswerResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    sources: list[SourceRef] = []
    retrieval_stats: RetrievalStats = RetrievalStats()


class SearchHit(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    content: str
    score: float


class SearchDebugResponse(BaseModel):
    query: str
    bm25_hits: list[SearchHit] = []
    vector_hits: list[SearchHit] = []
    kg_hits: list[SearchHit] = []
    fused_hits: list[SearchHit] = []


class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    category: int = 0  # 0 实体 1 文档


class GraphLink(BaseModel):
    source: str
    target: str
    relation: str


class GraphOverview(BaseModel):
    nodes: list[GraphNode]
    links: list[GraphLink]
