# config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Google Cloud Credentials
    GOOGLE_TYPE: str = "service_account"
    GOOGLE_PROJECT_ID: str
    GOOGLE_PRIVATE_KEY_ID: str
    GOOGLE_PRIVATE_KEY: str
    GOOGLE_CLIENT_EMAIL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_X509_CERT_URL: str
    GOOGLE_UNIVERSE_DOMAIN: str = "googleapis.com"
    
    class Config:
        # This allows Pydantic to read from a .env file if you have one
        env_file = ".env"
        extra = 'allow'

# Create a single settings instance to be used across the application
settings = Settings()