import os
from dotenv import load_dotenv
from typing import List

# Load .env once at import time
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "medical_chatbot_backend")
    CORS_ALLOW_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    # Optional model paths or keys (mock for demo)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "mock-embedder")
    VECTOR_DIM: int = int(os.getenv("VECTOR_DIM", "384"))
    # For demo/testing use in-memory store
    USE_PERSISTENT_STORE: bool = os.getenv("USE_PERSISTENT_STORE", "false").lower() == "true"


settings = Settings()
