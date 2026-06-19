from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./studioos.db"
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    debug: bool = False
    output_dir: str = "output"
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
