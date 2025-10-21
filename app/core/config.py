"""
Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Socrata API
    SOCRATA_DOMAIN: str = "www.datos.gov.co"
    SOCRATA_DATASET_ID: str = "48fq-mxnm"
    SOCRATA_APP_TOKEN: str = ""
    SOCRATA_USERNAME: str = ""
    SOCRATA_PASSWORD: str = ""
    
    # FastAPI
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://streamlit:8501"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
