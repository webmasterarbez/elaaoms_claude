from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "FastAPI Service"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"
    ngrok_authtoken: str = ""
    elevenlabs_post_call_hmac_key: str = ""
    elevenlabs_post_call_payload_path: str = "./payloads"
    openmemory_api_url: str = "http://localhost:8080"
    openmemory_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
