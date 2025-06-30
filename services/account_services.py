# app/services/account_service.py
from fastapi import HTTPException
from models.bank_models import Bank
from repository import account_repository
from repository.bank_repository import get_bank_by_code
from schemas.account_schemas import AccountCreate
from sqlalchemy.orm import Session


def account_list(application_id: str):
    return account_repository.get_account_list(application_id)


def account_get(application_id: str, body: dict):
    return account_repository.get_account(application_id, body)

# app/services/account_service.py


def account_create(db: Session, application_id: str, data: AccountCreate):
    bank = db.query(Bank).filter(Bank.bank_code == data.account_bank).first()
    if not bank:
        raise HTTPException(status_code=400, detail=f"Bank '{data.account_bank}' not found")

    account_data_dict = data.dict()
    account_data_dict["account_bank_id"] = bank.id
    del account_data_dict["account_bank"]

    return account_repository.create_account(db, account_data_dict)