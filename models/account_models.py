from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import relationship
from database import Base
from .bank_models import Bank

class Account(Base):
    __tablename__ = "account"
    __table_args__ = {"schema": "convert"}

    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, nullable=False)
    account_no = Column(String, nullable=False)
    account_email = Column(String, nullable=False)

    account_bank_id = Column(Integer, ForeignKey("convert.banks.id"), nullable=False)
    bank = relationship(Bank, foreign_keys=[account_bank_id])

    

