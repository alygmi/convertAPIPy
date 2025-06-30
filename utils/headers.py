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
