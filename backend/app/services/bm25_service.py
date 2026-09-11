# -*- coding: utf-8 -*-
"""
BM25 关键词检索服务（第一种检索方式）。
- 语料：MySQL document_chunks 表（ready 文档全量加载）
- 分词：jieba（对工业领域术语做自定义词典支持）
- 算法：rank_bm25 (BM25Okapi)
- 增量策略：记录最近构建时间，与 documents 表最大 updated_at 对比，有变化才重建
"""
import threading
from datetime import datetime

import jieba
from rank_bm25 import BM25Okapi
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk

# 工业领域自定义词典（可扩展：把常用专业词加入，避免被错误切分）
_INDUSTRY_WORDS = [
    "数控机床", "工业软件", "知识图谱", "混合检索", "向量检索", "语义检索", "伺服电机",
    "PLC", "SCADA", "MES", "ERP", "CAD", "CAM", "CAE", "CAPP", "PDM", "PLM", "DCS", "CNC",
    "刀具磨损", "主轴转速", "进给速度", "切削深度", "加工精度", "热变形", "故障诊断",
    "工业机器人", "传感器", "数据采集", "边缘计算", "数字孪生",
]
for _w in _INDUSTRY_WORDS:
    jieba.add_word(_w)


class BM25IndexService:
    def __init__(self):
        self._lock = threading.Lock()
        self._chunk_ids: list[str] = []
        self._tokenized_corpus: list[list[str]] = []
        self._bm25: BM25Okapi | None = None
        self._built_at: datetime | None = None

    # ---------- 索引构建 ----------
    def ensure_index(self, db: Session):
        """对比数据库最新更新时间，必要时重建索引（线程安全）"""
        max_updated = db.query(func.max(Document.updated_at)).scalar()
        if max_updated is None:
            return
        with self._lock:
            if self._built_at is not None and max_updated <= self._built_at:
                return
            self._rebuild(db)
            self._built_at = datetime.now()

    def _rebuild(self, db: Session):
        chunks = (
            db.query(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(Document.status == "ready")
            .order_by(DocumentChunk.id)
            .all()
        )
        self._chunk_ids = [str(c.id) for c in chunks]
        self._tokenized_corpus = [self._tokenize(c.content) for c in chunks]
        self._bm25 = BM25Okapi(self._tokenized_corpus) if self._tokenized_corpus else None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """jieba 分词 + 过滤空白"""
        return [w for w in jieba.lcut(text) if w.strip()]

    # ---------- 检索 ----------
    def search(self, db: Session, query: str, top_k: int | None = None) -> list[tuple[str, float]]:
        """
        BM25 检索，返回 [(chunk_id_str, score)] 按得分降序。
        query 为空或索引为空时返回 []。
        """
        self.ensure_index(db)
        top_k = top_k or settings.BM25_TOP_K
        if not self._bm25:
            return []
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        scores = self._bm25.get_scores(query_tokens)
        # 按分数降序取 top_k
        ranked = sorted(
            zip(self._chunk_ids, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [(cid, float(score)) for cid, score in ranked[:top_k] if score > 0]


bm25_service = BM25IndexService()
