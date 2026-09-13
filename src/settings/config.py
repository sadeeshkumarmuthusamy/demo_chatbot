"""
Application configuration loaded from the .env file at the project root.
"""
from pathlib import Path

import truststore
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Use the OS certificate store (instead of the certifi bundle) for SSL
# verification. This is required on machines behind a corporate TLS-inspecting
# proxy (e.g. Zscaler) whose root CA is trusted by Windows but not by certifi.
truststore.inject_into_ssl()

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


class Config(BaseSettings):
    """Settings sourced from environment variables / the .env file."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    GROQ_API_KEY: str
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"


config = Config()
