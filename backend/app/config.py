from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    openai_api_key: str
    secret_key: str
    database_url: str = "sqlite:///./email_assistant.db"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

