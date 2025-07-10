
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False)
    PAYMENT_API_BASE_URL: str
    PAYMENT_ADMIN_TOKEN: str

    # internal_platform_api_base_url: str
    # internal_platform_api_token: str
    # super_admin_platform_api_url: str
    # super_admin_platform_api_token: str
    INTERNAL_PLATFORM_API_BASE_URL: str
    INTERNAL_PLATFORM_API_TOKEN: str
    SUPER_ADMIN_PLATFORM_API_URL: str
    SUPER_ADMIN_PLATFORM_API_TOKEN: str

    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
