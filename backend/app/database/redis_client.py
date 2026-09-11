# -*- coding: utf-8 -*-
"""
Redis 连接（热点缓存 / JWT 黑名单 / 异步任务状态）。
懒加载单例：首次调用时建立连接。
"""
import redis

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,   # 自动把 bytes 解码为 str
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        _client.ping()  # 启动即验证连通性，失败尽早暴露
    return _client


def close_redis():
    global _client
    if _client is not None:
        _client.close()
        _client = None
