# -*- coding: utf-8 -*-
"""
MySQL 连接（业务持久化）：
用户、文档元数据、文档分块、会话与消息。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,      # 取连接前探活，避免 MySQL 断连后报错
    pool_recycle=3600,       # 每小时回收连接
    pool_size=10,
    max_overflow=20,
    echo=False,              # 生产/开发默认关闭 SQL 日志，避免日志阻塞
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()
