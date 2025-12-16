from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Bank Aggregator API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://postgres:password@postgres:5432/bank_aggregator"
    DATABASE_HOST: str = "postgres"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "bank_aggregator"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "password"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    SESSION_EXPIRE_HOURS: int = 24

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    OTP_CODE: str = "123456"
    OTP_EXPIRE_MINUTES: int = 10
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@bankapp.com"
    SMTP_FROM_NAME: str = "Bank Aggregator"
    SMTP_ENABLED: bool = False

    TEAM_CLIENT_ID: str = "team222"
    TEAM_CLIENT_SECRET: str = "Wl1F0L2aVHOPE20rM0DFeqvP9Qr2pgQT"

    VBANK_BASE_URL: str = "https://vbank.open.bankingapi.ru"
    ABANK_BASE_URL: str = "https://abank.open.bankingapi.ru"
    SBANK_BASE_URL: str = "https://sbank.open.bankingapi.ru"

    BANK_TOKEN_TTL: int = 82800
    CONSENT_REQUEST_TTL: int = 14400
    BANK_DATA_CACHE_TTL: int = 14400

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
