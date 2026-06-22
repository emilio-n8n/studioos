from pydantic_settings import BaseSettings


OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go/v1"

OPENCODE_GO_MODELS = {
    "deepseek-v4-flash": {"type": "openai", "label": "DeepSeek V4 Flash"},
    "deepseek-v4-pro": {"type": "openai", "label": "DeepSeek V4 Pro"},
    "glm-5.2": {"type": "openai", "label": "GLM-5.2"},
    "glm-5.1": {"type": "openai", "label": "GLM-5.1"},
    "kimi-k2.7-code": {"type": "openai", "label": "Kimi K2.7 Code"},
    "kimi-k2.6": {"type": "openai", "label": "Kimi K2.6"},
    "mimo-v2.5": {"type": "openai", "label": "MiMo-V2.5"},
    "mimo-v2.5-pro": {"type": "openai", "label": "MiMo-V2.5-Pro"},
    "minimax-m3": {"type": "anthropic", "label": "MiniMax M3"},
    "minimax-m2.7": {"type": "anthropic", "label": "MiniMax M2.7"},
    "qwen3.7-max": {"type": "anthropic", "label": "Qwen3.7 Max"},
    "qwen3.7-plus": {"type": "anthropic", "label": "Qwen3.7 Plus"},
    "qwen3.6-plus": {"type": "anthropic", "label": "Qwen3.6 Plus"},
}


def get_opencode_go_models() -> list[dict]:
    return [{"id": k, **v} for k, v in OPENCODE_GO_MODELS.items()]


class Settings(BaseSettings):
    database_url: str = "sqlite:///./studioos.db"
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    debug: bool = False
    output_dir: str = "output"
    environment: str = "development"
    acp_server_urls: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
