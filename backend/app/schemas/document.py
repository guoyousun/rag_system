# -*- coding: utf-8 -*-
"""文档相关 Schema"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_size: int
    file_type: str
    status: str
    chunk_count: int
    entity_count: int
    error_msg: str | None
    created_at: datetime


class DocumentChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chunk_index: int
    content: str


class DocumentDetailOut(DocumentOut):
    chunks: list[DocumentChunkOut] = []


class UploadResponse(BaseModel):
    document: DocumentOut
    message: str
