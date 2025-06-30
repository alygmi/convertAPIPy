# app/repositories/bank_repository.py
import httpx
from config.settings import settings
from utils.headers import build_payment_api_headers
from sqlalchemy.orm import Session
from models.bank_models import Bank

def get_bank_by_code(db: Session, bank_code: str) -> Bank | None:
    return db.query(Bank).filter(Bank.bank_code == bank_code).first()
# or

# app/repositories/bank_repository.py

# def list_banks_from_api(application_id: str):
#     url = f"{settings.PAYMENT_API_BASE_URL}/payout/bank/list"
#     headers = build_payment_api_headers(application_id)
#     response = httpx.get(url, headers=headers)
#     return response
