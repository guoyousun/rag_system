# -*- coding: utf-8 -*-
"""
初始化脚本：创建 MySQL 全部数据表。
用法（backend 目录下）:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

# 保证从 backend 目录运行时可 import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.mysql import Base, engine  # noqa: E402
from app.models import chat, document, user  # noqa: F401,E402  确保模型注册


def main():
    print("正在创建数据表 ...")
    Base.metadata.create_all(bind=engine)
    print("完成。表清单:")
    from sqlalchemy import inspect
    for table in inspect(engine).get_table_names():
        print(f"  - {table}")


if __name__ == "__main__":
    main()
