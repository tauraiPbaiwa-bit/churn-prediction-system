"""
Centralized application configuration.
Loads values from environment variables / .env file so no secrets are hardcoded.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "churn_prediction_db")

    app_secret_key: str = os.getenv("APP_SECRET_KEY", "dev_secret_change_me")
    env: str = os.getenv("ENV", "development")

    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", 25))

    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    model_dir: str = os.getenv("MODEL_DIR", "saved_models")
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.model_dir, exist_ok=True)
os.makedirs(settings.upload_dir, exist_ok=True)
