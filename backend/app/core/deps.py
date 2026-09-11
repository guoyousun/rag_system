# -*- coding: utf-8 -*-
"""
FastAPI 依赖注入：
- get_db: SQLAlchemy 会话（请求级）
- get_redis: Redis 连接
- get_current_user: 从 Authorization 头解析并校验 JWT，返回当前用户
"""
from typing import Generator

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token, token_remain_ttl
from app.database.mysql import SessionLocal
from app.database.redis_client import get_redis_client
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIAL_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="登录状态无效或已过期，请重新登录",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    return get_redis_client()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
) -> User:
    if credentials is None:
        raise _CREDENTIAL_EXC
    try:
        payload = decode_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except pyjwt.PyJWTError:
        raise _CREDENTIAL_EXC

    jti = payload.get("jti")
    # 退出黑名单检查：已退出（logout）的 token 立即失效
    if jti and redis.exists(f"auth:blacklist:{jti}"):
        raise _CREDENTIAL_EXC

    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIAL_EXC
    # token 版本校验：修改密码 / 强制下线后旧 token 全部失效
    if payload.get("ver") != user.token_version:
        raise _CREDENTIAL_EXC
    return user


def optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """可选认证：未登录返回 None（用于部分公开接口）"""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except pyjwt.PyJWTError:
        return None
    try:
        return db.get(User, int(payload.get("sub", 0)))
    except Exception:
        return None
