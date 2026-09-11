# -*- coding: utf-8 -*-
"""
认证 API：注册 / 登录 / 退出 / 修改密码 / 当前用户信息。
- 退出：JWT jti 写入 Redis 黑名单（TTL = token 剩余有效期）
- 修改密码：token_version 自增，使已签发的所有旧 token 失效
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.deps import bearer_scheme, get_current_user, get_db, get_redis
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    token_remain_ttl,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserInfo,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    username = body.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(username=username, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="注册失败，用户名可能已被占用")
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """登录，签发 JWT"""
    user = db.query(User).filter(User.username == body.username.strip()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenResponse(**create_access_token(user.id, user.username, user.token_version))


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    """退出登录：当前 token 加入黑名单，到期前不可再用"""
    payload = decode_token(credentials.credentials)
    ttl = token_remain_ttl(payload)
    if ttl > 0:
        redis.setex(f"auth:blacklist:{payload['jti']}", ttl, "1")
    return MessageResponse(message="已退出登录")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码：校验原密码 → 更新哈希 → token_version 自增使全部旧 token 失效"""
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = hash_password(body.new_password)
    current_user.token_version += 1
    db.commit()
    return MessageResponse(message="密码修改成功，请重新登录")


@router.get("/me", response_model=UserInfo)
def me(current_user: User = Depends(get_current_user)):
    """当前登录用户信息"""
    return current_user
