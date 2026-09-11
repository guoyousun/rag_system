# -*- coding: utf-8 -*-
"""
文档模型：
- Document       文档元数据（处理状态机: uploaded→parsing→vectorizing→kg_building→ready / failed）
- DocumentChunk  文档分块（BM25 索引与引用来源的数据源）
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.mysql import Base

# 文档处理状态机
DOC_STATUS_UPLOADED = "uploaded"       # 已上传，待处理
DOC_STATUS_PARSING = "parsing"         # 解析中
DOC_STATUS_VECTORIZING = "vectorizing"  # 分块+向量化中
DOC_STATUS_KG_BUILDING = "kg_building"  # 知识图谱构建中
DOC_STATUS_READY = "ready"             # 处理完成，可被检索
DOC_STATUS_FAILED = "failed"           # 处理失败


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="所属用户")
    filename = Column(String(255), nullable=False, comment="原始文件名")
    stored_path = Column(String(512), nullable=False, comment="服务器存储路径")
    file_size = Column(Integer, nullable=False, default=0, comment="文件大小(字节)")
    file_type = Column(String(16), nullable=False, comment="扩展名 .pdf/.docx/.txt/.md")
    status = Column(String(32), nullable=False, default=DOC_STATUS_UPLOADED, index=True, comment="处理状态")
    chunk_count = Column(Integer, nullable=False, default=0, comment="分块数")
    entity_count = Column(Integer, nullable=False, default=0, comment="抽取实体数")
    error_msg = Column(Text, nullable=True, comment="处理失败原因")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, default=0, comment="块序号")
    content = Column(Text, nullable=False, comment="分块文本（BM25 检索语料）")
    created_at = Column(DateTime, server_default=func.now())

    document = relationship("Document", back_populates="chunks")

    __table_args__ = ({"mysql_charset": "utf8mb4"})
