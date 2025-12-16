"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Google Gemini API
    gemini_api_key: str
    
    # Groq STT API
    groq_api_key: str = ""  # Optional, fallback to Gemini if empty
    
    # Application Settings
    upload_dir: str = "./uploads"
    frame_interval: int = 5  # Extract 1 frame every N seconds
    max_video_length: int = 900  # 15 minutes in seconds
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def get_upload_path(self) -> Path:
        """Get upload directory as Path object, create if doesn't exist"""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton instance
settings = Settings()
