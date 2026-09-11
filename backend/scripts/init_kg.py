# -*- coding: utf-8 -*-
"""
初始化脚本：创建 Neo4j 唯一约束与索引。
用法（backend 目录下）:
    python scripts/init_kg.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.neo4j_client import get_driver  # noqa: E402

CONSTRAINTS = [
    "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
]


def main():
    driver = get_driver()
    with driver.session() as session:
        for cypher in CONSTRAINTS:
            session.run(cypher).consume()
            print(f"OK: {cypher}")
    print("Neo4j 约束/索引初始化完成")
    driver.close()


if __name__ == "__main__":
    main()
