from .database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric
from decimal import Decimal
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(10), nullable=False)  # "income" vagy "expense"
    created_at = Column(DateTime, default=func.now())

    # Relationship
    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    booking_date = Column(Date, nullable=True)
    transaction_type = Column(String(100), nullable=False)
    direction = Column(String(10), nullable=False)
    partner_name = Column(String(200), nullable=True)
    partner_account = Column(String(100), nullable=True)
    expense_category = Column(String(200), nullable=True)
    description = Column(String(500), nullable=True)
    account_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False, index=True)
    currency = Column(String(3), nullable=False, default="HUF")

    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=True, index=True
    )

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="transactions")
