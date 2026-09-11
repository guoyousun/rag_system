# -*- coding: utf-8 -*-
"""
知识图谱检索服务（第三种检索方式）。
- 存储：Neo4j
- 图模式：
    (:Document {id, title})
    (:Chunk {id})                    分块证据节点
    (:Entity {name, type})           工业领域实体
    (chunk)-[:PART_OF]->(document)
    (chunk)-[:MENTIONED]->(entity)   chunk 提及实体
    (entity)-[:RELATED {relation}]->(entity)  实体间关系
- 检索流程：query → 实体链接（jieba 分词 + 实体名匹配）→ 一跳邻居扩展 → 关联 chunk 证据 → 按实体命中数排序
"""
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import jieba

from app.core.config import settings
from app.database.neo4j_client import run_query, run_write
from app.services.llm_service import extract_entities


def _norm(name: str) -> str:
    """实体名规范化：去空白、转小写（用于精确匹配）"""
    return re.sub(r"\s+", "", name or "").lower()


# ============================================================
# 写入
# ============================================================
_WINDOW_MAX_CHARS = 4000  # 实体抽取文本窗口大小（一次 LLM 调用覆盖的文本量）


def _build_windows(chunks: list[dict], max_chars: int = _WINDOW_MAX_CHARS) -> list[dict]:
    """
    将分块按累计字符数合并为抽取窗口，减少 LLM 调用次数。
    返回 [{"chunk_ids": [int,...], "text": str}]
    """
    windows: list[dict] = []
    cur_ids: list[int] = []
    cur_parts: list[str] = []
    cur_len = 0
    for c in chunks:
        content = c["content"]
        if cur_ids and cur_len + len(content) > max_chars:
            windows.append({"chunk_ids": cur_ids, "text": "\n".join(cur_parts)})
            cur_ids, cur_parts, cur_len = [], [], 0
        cur_ids.append(c["chunk_id"])
        cur_parts.append(content)
        cur_len += len(content)
    if cur_ids:
        windows.append({"chunk_ids": cur_ids, "text": "\n".join(cur_parts)})
    return windows


def build_graph_from_chunks(document_id: int, filename: str, chunks: list[dict]) -> int:
    """
    从文档分块构建知识图谱（窗口化批量抽取 + 多窗口并发 + 增量写入）。
    chunks: [{"chunk_id": int, "content": str}]

    策略（解决大文档逐 chunk 调 LLM 导致的数小时卡顿）：
      1. 每约 4000 字符合并为一个窗口，一次 LLM 调用抽取该窗口实体与关系；
      2. 多个窗口并发调用（默认 3 路），显著缩短长文档处理时间；
      3. 用实体名在 chunk 文本中出现与否，建立 chunk → 实体 MENTIONED 连接；
      4. 每个窗口抽取完立即增量写入 Neo4j，进度可见、失败可重试。
    返回累计抽取的实体总数。
    """
    if not chunks:
        return 0

    windows = _build_windows(chunks)
    doc_id = str(document_id)
    total_entities: set[str] = set()
    workers = min(3, len(windows))

    def _process_window(win: dict) -> tuple:
        """单窗口：抽取 + 回匹配（独立执行，天然线程安全）"""
        extracted = extract_entities(win["text"])
        win_entities: dict[str, tuple[str, str]] = {}
        for ent in extracted["entities"]:
            key = _norm(ent["name"])
            if key:
                win_entities[key] = (ent["name"], ent.get("type", "其他"))
        win_relations = [
            {
                "source": _norm(r["source"]),
                "target": _norm(r["target"]),
                "relation": r.get("relation", "关联"),
            }
            for r in extracted["relations"]
            if _norm(r["source"]) in win_entities and _norm(r["target"]) in win_entities
        ]
        # 实体名回匹配：实体出现在哪些 chunk（建立 MENTIONED 证据）
        chunk_mentions: dict[str, set] = {}
        norm_by_id = {c["chunk_id"]: _norm(c["content"]) for c in chunks if c["chunk_id"] in win["chunk_ids"]}
        for key in win_entities:
            for cid in win["chunk_ids"]:
                if key and key in norm_by_id.get(cid, ""):
                    chunk_mentions.setdefault(str(cid), set()).add(key)
        return win_entities, win_relations, chunk_mentions

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_process_window, win) for win in windows]
        for fut in as_completed(futures):
            win_entities, win_relations, chunk_mentions = fut.result()
            total_entities.update(win_entities.keys())
            # 增量写入（同名实体 MERGE 自动合并，跨窗口实体天然连通）
            _write_graph(doc_id, filename, win_entities, win_relations, chunk_mentions)

    return len(total_entities)


def _write_graph(document_id, filename, entities: dict, relations: list, chunk_mentions: dict):
    """一次事务写入全部图数据"""
    doc_id = str(document_id)

    def _tx(tx):
        tx.run("MERGE (d:Document {id: $id}) SET d.title = $title", id=doc_id, title=filename)
        for key, (name, etype) in entities.items():
            tx.run(
                "MERGE (e:Entity {name: $name}) SET e.name_norm = $norm, e.type = $type",
                name=name, norm=key, type=etype,
            )
        for chunk_id, entity_keys in chunk_mentions.items():
            tx.run("MERGE (c:Chunk {id: $id})", id=chunk_id)
            tx.run(
                "MATCH (c:Chunk {id: $id}) MERGE (d:Document {id: $doc}) "
                "MERGE (c)-[:PART_OF]->(d)",
                id=chunk_id, doc=doc_id,
            )
            for key in entity_keys:
                tx.run(
                    "MATCH (c:Chunk {id: $id}) MATCH (e:Entity {name_norm: $norm}) "
                    "MERGE (c)-[:MENTIONED]->(e)",
                    id=chunk_id, norm=key,
                )
        for rel in relations:
            tx.run(
                "MATCH (s:Entity {name_norm: $s}) MATCH (t:Entity {name_norm: $t}) "
                "MERGE (s)-[r:RELATED {relation: $relation}]->(t)",
                s=rel["source"], t=rel["target"], relation=rel["relation"],
            )

    with __import__("app.database.neo4j_client", fromlist=["get_driver"]).get_driver().session() as session:
        session.execute_write(_tx)


# ============================================================
# 检索
# ============================================================
def search(query: str, top_k: int | None = None) -> list[tuple[str, float]]:
    """
    KG 检索：实体链接 → 邻居扩展 → 证据 chunk 召回。
    返回 [(chunk_id_str, score)]，score 为关联实体命中数。
    """
    top_k = top_k or settings.KG_TOP_K
    linked = _link_entities(query)
    if not linked:
        return []

    # 一跳邻居扩展（提升召回：问"加工精度"可关联到提及该实体的邻居实体的 chunk）
    expanded = set(linked)
    try:
        result = run_query(
            "MATCH (e:Entity)-[r:RELATED]-(e2:Entity) "
            "WHERE e.name_norm IN $names RETURN DISTINCT e2.name_norm AS name LIMIT 50",
            {"names": list(linked)},
        )
        expanded.update(r["name"] for r in result)
    except Exception:
        pass

    # 命中实体 → 证据 chunk
    try:
        rows = run_query(
            "MATCH (c:Chunk)-[:MENTIONED]->(e:Entity) "
            "WHERE e.name_norm IN $names "
            "RETURN c.id AS chunk_id, count(e) AS hits",
            {"names": list(expanded)},
        )
    except Exception:
        return []

    counter: Counter = Counter()
    for row in rows:
        counter[row["chunk_id"]] += row["hits"] or 1
    return [(cid, float(score)) for cid, score in counter.most_common(top_k)]


def _link_entities(query: str) -> set[str]:
    """实体链接：query 分词/整句与图中实体名匹配"""
    try:
        names_rows = run_query("MATCH (e:Entity) RETURN e.name_norm AS name LIMIT 5000")
    except Exception:
        return set()
    all_names = {row["name"] for row in names_rows}
    if not all_names:
        return set()

    tokens = set(jieba.lcut(query))
    tokens.add(_norm(query))
    linked = {n for n in all_names if n and (n in tokens or n in _norm(query))}
    return linked


def get_entity_count() -> int:
    try:
        rows = run_query("MATCH (e:Entity) RETURN count(e) AS cnt")
        return rows[0]["cnt"] if rows else 0
    except Exception:
        return 0


def delete_document(document_id: int):
    """删除文档节点及其 chunk 证据，并清理孤立实体"""
    doc_id = str(document_id)
    run_write(
        "MATCH (d:Document {id: $id}) OPTIONAL MATCH (c:Chunk)-[:PART_OF]->(d) "
        "DETACH DELETE c, d",
        {"id": doc_id},
    )
    # 清理无任何关系的孤立实体
    run_write("MATCH (e:Entity) WHERE NOT (e)--() DELETE e")


# ============================================================
# 图谱可视化数据
# ============================================================
def get_graph_overview(limit: int = 60) -> dict:
    """
    返回图谱子图供前端可视化：
    {"nodes": [{"id","name","type","category"}], "links": [{"source","target","relation"}]}

    注意：neo4j driver 的 record.data() 会把节点转为 dict 且不保留 labels，
    因此用 Cypher 的 labels()/coalesce() 显式返回标签与名称信息。
    """
    rows = run_query(
        "MATCH (n) WHERE (n:Entity OR n:Document) "
        "WITH n LIMIT $limit "
        "OPTIONAL MATCH (n)-[r]->(m) WHERE (m:Entity OR m:Document) "
        "RETURN "
        "labels(n) AS n_labels, coalesce(n.id, n.name) AS n_id, coalesce(n.name, n.title) AS n_name, "
        "labels(m) AS m_labels, coalesce(m.id, m.name) AS m_id, coalesce(m.name, m.title) AS m_name, "
        "type(r) AS r_type, r.relation AS r_relation",
        {"limit": limit},
    )
    nodes: dict[str, dict] = {}
    links: list[dict] = []
    for row in rows:
        n_labels = row.get("n_labels") or []
        n_id = str(row.get("n_id") or "")
        if n_id and n_id not in nodes:
            label = "Document" if "Document" in n_labels else "Entity"
            nodes[n_id] = {
                "id": n_id,
                "name": row.get("n_name") or n_id,
                "type": label,
                "category": 1 if label == "Document" else 0,
            }
        m_id = row.get("m_id")
        if m_id:
            links.append({
                "source": n_id,
                "target": str(m_id),
                "relation": row.get("r_relation") or row.get("r_type") or "",
            })
    return {"nodes": list(nodes.values()), "links": links}
