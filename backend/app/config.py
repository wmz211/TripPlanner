from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dashscope_api_key: str
    amap_api_key: str = ""
    amap_web_key: str = ""
    unsplash_access_key: str = ""

    llm_model: str = "qwen3.6-plus"
    llm_fast_model: str = "qwen3.6-flash"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
