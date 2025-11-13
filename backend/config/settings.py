from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "FastAPI Service"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"
    ngrok_authtoken: str = ""
    elevenlabs_post_call_hmac_key: str = ""
    elevenlabs_post_call_payload_path: str = "./data/payloads"
    webhook_url: str = "http://localhost:8000/webhook/post-call"

    # ElevenLabs API
    elevenlabs_api_key: str = ""
    elevenlabs_api_url: str = "https://api.elevenlabs.io/v1"

    # OpenMemory
    openmemory_api_url: str = "http://localhost:8080"
    openmemory_api_key: str = ""

    # LLM Configuration
    llm_provider: str = "openai"  # openai, anthropic, groq
    llm_api_key: str = ""
    llm_model: str = "gpt-4-turbo"

    # Memory Configuration
    agent_profile_ttl_hours: int = 24
    memory_relevance_threshold: float = 0.7
    high_importance_threshold: int = 8

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
