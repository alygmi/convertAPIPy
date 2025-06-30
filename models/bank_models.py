from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from database import Base


class Bank(Base):
    __tablename__ = "banks"
    __table_args__ = {"schema": "convert"}

    id = Column(Integer, primary_key=True)
    bank_code = Column(String, nullable=False, unique=True)
    bank_name = Column(String, nullable=False)
