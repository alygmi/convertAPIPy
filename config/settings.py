
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PAYMENT_API_BASE_URL: str
    PAYMENT_ADMIN_TOKEN: str

    internal_platform_api_base_url: str
    internal_platform_api_token: str
    super_admin_platfrom_api_url: str
    super_admin_platfrom_api_token: str

    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
