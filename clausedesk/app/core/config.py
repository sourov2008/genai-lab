"""Application settings loaded from the environment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class ModelPricing(BaseModel):
    """USD price per 1M input and output tokens for one model."""

    input_per_1m: float = 0.0
    output_per_1m: float = 0.0


class Settings(BaseSettings):
    """Runtime configuration. Env names use Field aliases."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "ClauseDesk"
    app_env: str = Field(default="local", alias="APP_ENV")
    debug: bool = True

    database_url: str = Field(
        default="postgresql+asyncpg://clausedesk:clausedesk@localhost:5432/clausedesk",
        alias="DATABASE_URL",
    )

# TODO: Refactor hardcoded default values into centralized constants.

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODEL")
    embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    llm_timeout_s: float = 30.0
    prompt_version: str = Field(default="v1", alias="PROMPT_VERSION")

    # Values: temp=0.0 (deterministic), max_tokens=1024 (prevents JSON truncation). See docs/sweep_comparison_table.md for metrics.
    extraction_temperature: float = 0.0
    extraction_max_tokens: int = 1024
    explanation_temperature: float = 0.3

    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    n8n_webhook_url: str = Field(default="", alias="N8N_WEBHOOK_URL")
    n8n_webhook_secret: str = Field(default="", alias="N8N_WEBHOOK_SECRET")

    model_pricing: dict[str, ModelPricing] = {
        "gpt-4o-mini": ModelPricing(input_per_1m=0.15, output_per_1m=0.60),
        "openai/gpt-oss-120b": ModelPricing(input_per_1m=0.0, output_per_1m=0.0),
    }

    # Observability
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance.

    Returns:
        Settings loaded from the environment and `.env` file.
    """
    return Settings()
