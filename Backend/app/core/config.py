from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env that aren't defined
    )
    app_name: str = Field(default="Islamic Bank API",alias="APP_NAME")
    debug: bool = Field(default=False,alias="DEBUG")
    mongodb_url: str = Field(
        default="mongodb://admin:secret@localhost:27017",
        alias="MONGODB_URL",
        description="MongoDB connection string"
    ) 
    mongodb_db_name: str = Field(
        default="islamic_bank",
        alias="MONGODB_DB_NAME"
    )
    #JWT
    secret_key: str = Field(
        default="change_this_in_production",
        alias="SECRET_KEY",
        description="Secret key for JWT token generation"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=1  # Must be at least 1 minute
    )
    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_account_topic: str = Field(
        default="account-events",
        alias="KAFKA_ACCOUNT_TOPIC"
    )
    kafka_transaction_topic: str = Field(
        default="transaction-events",
        alias="KAFKA_TRANSACTION_TOPIC"
    )
    kafka_profit_topic: str = Field(
        default="profit-events",
        alias="KAFKA_PROFIT_TOPIC"
    )
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )
    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        alias="CELERY_RESULT_BACKEND"
    )
settings = Settings()
