"""应用全局配置 - 从环境变量加载"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 应用
    APP_NAME: str = "MedMind Nexus API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/v1"
    CORS_ORIGINS: str = "*"

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./medmind.db"

    # 安全
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM
    LLM_PROVIDER: str = "mock"  # mock | openai | deepseek | qwen | zhipu
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT: int = 60

    MEDICAL_LLM_API_KEY: str = ""
    MEDICAL_LLM_API_BASE: str = ""
    MEDICAL_LLM_MODEL: str = ""

    # 上传
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024

    # 演示模式
    DEMO_MODE: bool = True

    # Redis / 向量库
    REDIS_URL: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
