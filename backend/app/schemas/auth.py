# -*- coding: utf-8 -*-
"""认证相关 Schema"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, description="用户名，3-32 位")
    password: str = Field(min_length=6, max_length=64, description="密码，6-64 位")


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(description="原密码")
    new_password: str = Field(min_length=6, max_length=64, description="新密码，6-64 位")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
