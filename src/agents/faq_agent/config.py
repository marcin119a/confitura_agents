"""Agent configuration — from a .env file or environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from a .env file in the working directory.

    Environment variables take precedence over the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""  # OPENAI_API_KEY variable
    model_name: str = "gpt-4o-mini"  # MODEL_NAME variable
    realtime_model_name: str = "gpt-realtime"  # REALTIME_MODEL_NAME variable
    realtime_voice: str = "alloy"  # REALTIME_VOICE variable
