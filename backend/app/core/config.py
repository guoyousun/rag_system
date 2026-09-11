# -*- coding: utf-8 -*-
"""
全局配置中心：统一从 .env 读取所有环境变量。
所有模块（存储连接、检索服务、LLM 服务）都应从这里取配置，禁止散落硬编码。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ---------- 应用 ----------
    APP_NAME: str = "多模式协同智能问答系统"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # ---------- JWT ----------
    SECRET_KEY: str = "dev-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ---------- MySQL ----------
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "multi_mode_qa"
    DATABASE_URL: str = ""  # 若填写则优先使用（跳过拼接）

    # ---------- Redis ----------
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # ---------- Neo4j ----------
    NEO4J_URI: str = "bolt://127.0.0.1:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j123456"

    # ---------- Chroma ----------
    CHROMA_PATH: str = "./data/chroma"

    # ---------- 千问大模型（OpenAI 兼容端点）----------
    QWEN_API_KEY: str = ""
    QWEN_LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_LLM_MODEL: str = "qwen3.7-flash"
    QWEN_EMBEDDING_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_EMBEDDING_MODEL: str = "qwen3.7-text-embedding"
    EMBEDDING_DIM: int = 1024
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048

    # ---------- 检索参数 ----------
    BM25_TOP_K: int = 10
    VECTOR_TOP_K: int = 10
    KG_TOP_K: int = 10
    FUSION_TOP_K: int = 6
    RRF_K: int = 60
    FUSION_WEIGHT_BM25: float = 1.0
    FUSION_WEIGHT_VECTOR: float = 1.0
    FUSION_WEIGHT_KG: float = 1.0

    # ---------- 文档处理 ----------
    MAX_UPLOAD_SIZE_MB: int = 50
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    ALLOWED_EXTENSIONS: str = ".txt,.md,.pdf,.docx"

    # ---------- 缓存 ----------
    REDIS_CACHE_TTL: int = 3600

    # ---------- CORS ----------
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---------- 派生属性 ----------
    @property
    def sqlalchemy_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    @property
    def allowed_extensions(self) -> set:
        return {ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()}

    @property
    def cors_origin_list(self) -> list:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
