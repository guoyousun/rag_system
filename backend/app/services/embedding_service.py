# -*- coding: utf-8 -*-
"""
千问 Embedding 服务（OpenAI 库兼容端点）。
text-embedding-v3 支持指定输出维度，统一使用 .env 中 EMBEDDING_DIM 保证向量维度稳定。
"""
from openai import OpenAI

from app.core.config import settings

_embed_client: OpenAI | None = None


def get_embedding_client() -> OpenAI:
    global _embed_client
    if _embed_client is None:
        if not settings.QWEN_API_KEY or settings.QWEN_API_KEY.startswith("sk-your"):
            raise RuntimeError(
                "未配置千问 API Key：请在 backend/.env 中填写 QWEN_API_KEY "
                "(阿里云百炼控制台申请: https://bailian.console.aliyun.com/)"
            )
        _embed_client = OpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_EMBEDDING_BASE_URL,
            timeout=120,
            max_retries=2,
        )
    return _embed_client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量文本向量化，返回与输入等长的向量列表"""
    if not texts:
        return []
    BATCH_SIZE = 20
    client = get_embedding_client()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(
            model=settings.QWEN_EMBEDDING_MODEL,
            input=batch,
            dimensions=settings.EMBEDDING_DIM,
        )
        # resp.data 顺序与输入一致，按 index 排序确保安全
        ordered = sorted(resp.data, key=lambda item: item.index)
        all_embeddings.extend([item.embedding for item in ordered])

    return all_embeddings


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
