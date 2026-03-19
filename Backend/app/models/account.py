from datetime import datetime
from decimal import Decimal
from typing import Optional
from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field
from app.models.enums import AccountType, AccountStatus
from app.models.customer import Customer


class Account(Document):
    """
    Each account belongs to one customer (Link = MongoDB DBRef).
    iban: Indexed unique — IBAN is the primary lookup key for transfers.
    profit_rate: For Mudarabah/savings accounts — annual profit rate (e.g. 0.05 = 5%)
    """
    customer: Link[Customer]                        # FK-like reference to Customer doc
    iban: Indexed(str, unique=True)                 # type: ignore
    account_type: AccountType
    balance: Decimal = Decimal("0.00")
    currency: str = "PKR"
    status: AccountStatus = AccountStatus.ACTIVE
    profit_rate: Optional[Decimal] = None           # Mudarabah profit rate
    murabaha_markup: Optional[Decimal] = None       # Murabaha markup percentage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "accounts"
        use_revision = True

    class Config:
        json_schema_extra = {
            "example": {
                "account_type": "savings",
                "currency": "PKR"
            }
        }


# ── Schemas ───────────────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    account_type: AccountType
    currency: str = "PKR"
    initial_deposit: Decimal = Decimal("0.00")


class AccountResponse(BaseModel):
    id: str
    iban: str
    account_type: AccountType
    balance: Decimal
    currency: str
    status: AccountStatus
    profit_rate: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True