from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./network_analysis.db"
    jwt_secret_key: str = "local-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    demo_email: str = "analyst@fictional.test"
    demo_password: str = "demo-pass-01"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
