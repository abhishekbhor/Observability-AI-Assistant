from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Observability AI Assistant"
    app_version: str = "1.0.0"
    default_lookback_minutes: int = Field(default=120, alias="OBS_DEFAULT_LOOKBACK_MINUTES")
    embedding_dim: int = Field(default=64, alias="OBS_EMBEDDING_DIM")
    llm_mode: str = Field(default="heuristic", alias="OBS_LLM_MODE")
    enable_gpu: bool = Field(default=False, alias="OBS_ENABLE_GPU")
    gpu_workers: int = Field(default=1, alias="OBS_GPU_WORKERS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
