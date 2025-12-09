"""
Configuration settings for the application.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://maintenance:maintenance123@localhost:5432/maintenance_db"
    )
    
    # Elasticsearch
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    elasticsearch_index: str = "telemetry-*"
    
    # Rule Engine
    rule_engine_interval: int = int(os.getenv("RULE_ENGINE_INTERVAL", "120"))  # seconds
    
    # Application
    app_name: str = "Maintenance 4.0 API"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"


settings = Settings()
