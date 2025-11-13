from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "FastAPI Service"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"
    ngrok_authtoken: str = ""
    elevenlabs_post_call_hmac_key: str = ""
    elevenlabs_post_call_payload_path: str = "./data/payloads"
    webhook_url: str = "http://localhost:8000/webhook/post-call"

    @field_validator("elevenlabs_post_call_hmac_key")
    @classmethod
    def validate_hmac_secret(cls, v: str) -> str:
        """
        Validate HMAC secret meets minimum security requirements.
        
        Requires minimum 32 bytes (256 bits) for HMAC-SHA256 security.
        
        Args:
            v: HMAC secret value
        
        Returns:
            Validated HMAC secret
        
        Raises:
            ValueError: If secret is too short
        """
        if v and len(v.encode('utf-8')) < 32:
            raise ValueError(
                "HMAC secret must be at least 32 bytes (256 bits) for security. "
                f"Current length: {len(v.encode('utf-8'))} bytes"
            )
        return v

    # ElevenLabs API
    elevenlabs_api_key: str = ""
    elevenlabs_api_url: str = "https://api.elevenlabs.io/v1"

    # OpenMemory
    openmemory_api_url: str = "http://localhost:8080"
    openmemory_api_key: str = ""

    # LLM Configuration
    llm_provider: str = "openai"  # openai, anthropic, or auto (auto selects based on availability)
    llm_api_key: str = ""
    llm_model: str = "gpt-4-turbo"
    llm_timeout_seconds: int = 30  # Timeout for LLM API calls

    # Memory Configuration
    agent_profile_ttl_hours: int = 24
    memory_relevance_threshold: float = 0.7
    high_importance_threshold: int = 8
    memory_similarity_threshold: float = 0.85  # For deduplication (cosine similarity)
    
    # Chunking Configuration
    llm_max_tokens_per_chunk: int = 10000  # Max tokens per chunk for LLM processing
    llm_chunk_overlap_tokens: int = 200  # Overlap between chunks to prevent context loss
    
    # Storage Retry Configuration
    memory_storage_retry_attempts: int = 3  # Retry attempts for storage operations
    memory_storage_retry_delay_seconds: int = 1  # Initial retry delay (exponential backoff)
    memory_validation_enabled: bool = True  # Enable post-storage validation

    class Config:
        # Look for .env file in project root (two levels up from backend/config/)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
