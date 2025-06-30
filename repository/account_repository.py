# app/repositories/account_repository.py
import httpx
from config.settings import settings
from utils.headers import build_payment_api_headers # asumsikan kamu punya ini
from sqlalchemy.orm import Session
from models.account_models import Account


def get_account_list(application_id: str):
    url = f"{settings.PAYMENT_API_BASE_URL}/payout/account/list"
    headers = {
        "Vending-Application-Id": application_id
    }
    response = httpx.get(url, headers=headers, timeout=90)
    return response


def get_account(application_id: str, body: dict):
    url = f"{settings.PAYMENT_API_BASE_URL}/payout/account/get"
    headers = {
        "Vending-Application-Id": application_id
    }
    response = httpx.post(url, json=body, headers=headers, timeout=90)
    return response


# app/repositories/account_repository.py

# def create_account(application_id: str, body: dict):
#     url = f"{settings.PAYMENT_API_BASE_URL}/payout/account/create"
#     headers = build_payment_api_headers(application_id)
#     response = httpx.post(url, json=body, headers=headers, timeout=90)
#     return response


# or

def create_account(db: Session, account_data: dict) -> Account:
    account = Account(**account_data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
