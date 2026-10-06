from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "My API"
    DATABASE_URL: str = "sqlite:///./test.db"
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GOOGLE_CLIENT_ID: str | None = None
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "models/gemini-1.5-pro"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
