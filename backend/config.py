from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""

    # HuggingFace
    hf_auth_token: str = ""

    # Sarvam AI (for Indian language STT)
    sarvam_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/db/vernanda.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Whisper
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"

    # LLM
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 4096

    # Storage
    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"

    # Limits
    max_file_size_mb: int = 200
    max_duration_minutes: int = 90

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Confidence threshold for STT fallback
    whisper_confidence_threshold: float = 0.3

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def processed_path(self) -> Path:
        p = Path(self.processed_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
