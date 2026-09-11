# -*- coding: utf-8 -*-
"""
Neo4j 连接（工业垂直领域知识图谱）。
懒加载单例 driver，提供常用图操作封装。
"""
from neo4j import GraphDatabase

from app.core.config import settings

_driver = None


def get_driver():
    """获取 Neo4j driver（懒加载单例）"""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        # 启动即验证连通性
        _driver.verify_connectivity()
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def run_query(cypher: str, params: dict | None = None, **kwargs):
    """执行只读查询，返回记录列表"""
    with get_driver().session() as session:
        result = session.run(cypher, params or {})
        return [record.data() for record in result]


def run_write(cypher: str, params: dict | None = None, **kwargs):
    """执行写事务"""
    with get_driver().session() as session:
        session.execute_write(lambda tx: tx.run(cypher, params or {}).consume())
