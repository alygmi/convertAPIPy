# app/models/account.py
from pydantic import BaseModel


class AccountCreate(BaseModel):
    account_name: str
    account_no: str
    account_bank: str
    account_email: str
