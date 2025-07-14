# app/utils/headers.py
from config.settings import settings


def build_payment_api_headers(application_id: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Iotera-Payment-Application-Id": application_id,
        "Iotera-Payment-Admin-Token": settings.PAYMENT_ADMIN_TOKEN
    }
    print(headers)
    return headers


def build_vending_headers() -> dict[str, str]:
    return {
        "Vending-Application-Id": "1000000021",
        "Content-Type": "application/json"
    }


def get_application_id() -> str:
    return "1000000021"
