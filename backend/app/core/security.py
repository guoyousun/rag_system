# -*- coding: utf-8 -*-
"""
安全工具：密码哈希（bcrypt）与 JWT 签发/校验。
token 中携带 jti（唯一ID，用于退出黑名单）与 ver（token 版本，用于改密后全局失效）。
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    """密码加盐哈希"""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码（容错：哈希格式非法时返回 False）"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, username: str, token_version: int) -> dict:
    """
    签发 JWT，返回结构化结果：
    {"access_token": str, "token_type": "bearer", "expires_in": int, "jti": str}
    """
    jti = uuid.uuid4().hex
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "ver": token_version,
        "jti": jti,
        "iat": datetime.now(timezone.utc),
        "exp": expire_at,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "jti": jti,
    }


def decode_token(token: str) -> dict:
    """
    解码并校验 JWT。
    失败抛出 jwt.PyJWTError 子类，由调用方统一转 401。
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def token_remain_ttl(payload: dict) -> int:
    """计算 token 剩余有效期（秒），用于黑名单 TTL"""
    exp = payload.get("exp")
    if not exp:
        return 0
    exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
    return max(0, int((exp_dt - datetime.now(timezone.utc)).total_seconds()))
