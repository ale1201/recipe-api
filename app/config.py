from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # In a production environment, these should be set via environment variables or a secure secrets manager, 
    # not hardcoded. I deleted the hardcoded values
    database_url: str
    secret_key: str 
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    cors_origins: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Here you can also specify different settings for development, testing, and production 
# environments by creating subclasses of Settings and overriding the necessary values.