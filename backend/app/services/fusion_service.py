# -*- coding: utf-8 -*-
"""
混合检索融合服务：RRF（Reciprocal Rank Fusion）。
三路检索各自返回有序 chunk_id 列表，RRF 融合后得到最终召回。
权重可在 .env 中调整（FUSION_WEIGHT_BM25 / VECTOR / KG）。
"""
from collections import defaultdict

from app.core.config import settings


def rrf_fuse(
    ranked_lists: list[list[tuple[str, float]]],
    weights: list[float] | None = None,
    k: int | None = None,
) -> list[tuple[str, float]]:
    """
    RRF 融合。
    ranked_lists: 各检索路的有序列表，元素为 (chunk_id_str, raw_score)
    weights: 与 ranked_lists 等长的路权重，默认全 1.0
    返回 [(chunk_id_str, rrf_score)] 按融合分降序。
    """
    k = k or settings.RRF_K
    if weights is None:
        weights = [1.0] * len(ranked_lists)
    assert len(weights) == len(ranked_lists), "weights 长度必须与检索路数一致"

    scores: dict[str, float] = defaultdict(float)
    for rank_list, weight in zip(ranked_lists, weights):
        for rank, (item_id, _) in enumerate(rank_list):
            scores[item_id] += weight / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
