from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_file: str
    nats_url: str
    nats_subject: str
    batch_size: int = 100
    poll_interval: float = 1.0
    max_pending: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
