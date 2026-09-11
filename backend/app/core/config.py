from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "LAYA Market API"
    env: str = "development"
    database_url: str = "postgresql+psycopg://postgres@127.0.0.1:5432/laya_market"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 1440
    cors_origins: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def cors_list(self): return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
    @property
    def cloudinary_ready(self): return bool(self.cloudinary_cloud_name and self.cloudinary_api_key and self.cloudinary_api_secret)
settings = Settings()
