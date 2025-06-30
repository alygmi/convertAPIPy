# app/services/bank_service.py
from repository.bank_repository import get_bank_by_code

def list_banks(db, bank_code):
    return get_bank_by_code(db, bank_code)
