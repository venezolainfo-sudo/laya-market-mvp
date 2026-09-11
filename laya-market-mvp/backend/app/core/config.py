from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "LAYA Market API"
    env: str = "development"
    database_url: str = "postgresql+psycopg://laya:laya_dev@localhost:5433/laya_market"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 1440
    cors_origins: str = "http://localhost:5174,http://localhost:5175,http://localhost:8081"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def cors_list(self): return [x.strip() for x in self.cors_origins.split(',') if x.strip()]
settings=Settings()
