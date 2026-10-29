# src/config.py
from functools import lru_cache
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelPricing(BaseModel):
    input_per_1m: float = 0.0
    output_per_1m: float = 0.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "gemini"  # "gemini" | "groq"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    llm_timeout_s: float = 30.0

    model_pricing: dict[str, ModelPricing] = {
        "gemini-3.8-flash": ModelPricing(input_per_1m=0.0, output_per_1m=0.0),
        "openai/gpt-oss-120b": ModelPricing(input_per_1m=0.0, output_per_1m=0.0), # <-- নতুন মডেল
    }
    
@lru_cache
def get_settings() -> Settings:
    return Settings()
