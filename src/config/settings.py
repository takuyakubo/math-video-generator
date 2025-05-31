from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "Math Video Generator"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://user:password@localhost/mathvideo"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # File Storage
    upload_dir: str = "./data/uploads"
    output_dir: str = "./data/outputs"
    temp_dir: str = "./data/temp"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # TTS Configuration
    azure_speech_key: Optional[str] = None
    azure_speech_region: Optional[str] = None
    google_tts_credentials: Optional[str] = None
    
    # Processing
    max_workers: int = 4
    processing_timeout: int = 3600  # 1 hour
    
    # LaTeX
    latex_timeout: int = 300
    pdflatex_path: str = "pdflatex"
    
    # FFmpeg
    ffmpeg_path: str = "ffmpeg"
    
    class Config:
        env_file = ".env"

settings = Settings()