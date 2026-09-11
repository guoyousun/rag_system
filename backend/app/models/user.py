# -*- coding: utf-8 -*-
"""用户模型"""
from sqlalchemy import Column, DateTime, Integer, String, func

from app.database.mysql import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(128), nullable=False, comment="bcrypt 密码哈希")
    token_version = Column(Integer, nullable=False, default=0, comment="token 版本号，改密/强制下线时自增使旧 token 失效")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"
