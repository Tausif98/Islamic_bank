from datetime import datetime
from decimal import Decimal
from typing import Optional
from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field
from app.models.enums import TransactionType, TransactionStatus
from app.models.account import Account


class LedgerEntry(BaseModel):
    """
    Double-entry bookkeeping: every transaction has debit + credit sides.
    debit_account: money goes OUT of this account
    credit_account: money comes INTO this account
    """
    debit_account_id: str
    credit_account_id: str
    amount: Decimal


class Transaction(Document):
    """
    Core transaction record. Immutable once written (status changes only).
    reference_id: client-supplied idempotency key (prevents duplicate transactions)
    """
    account: Link[Account]
    transaction_type: TransactionType
    amount: Decimal
    currency: str = "PKR"
    status: TransactionStatus = TransactionStatus.PENDING
    reference_id: Indexed(str, unique=True)         # type: ignore  # idempotency
    description: Optional[str] = None
    ledger_entry: Optional[LedgerEntry] = None
    destination_iban: Optional[str] = None          # For transfers
    metadata: dict = Field(default_factory=dict)    # Flexible: store fraud score, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "transactions"
        use_revision = True


# ── Schemas ───────────────────────────────────────────────────────────────────

class DepositRequest(BaseModel):
    amount: Decimal
    description: Optional[str] = None
    reference_id: str                               # Client must send unique ref


class WithdrawalRequest(BaseModel):
    amount: Decimal
    description: Optional[str] = None
    reference_id: str


class TransferRequest(BaseModel):
    destination_iban: str
    amount: Decimal
    description: Optional[str] = None
    reference_id: str


class TransactionResponse(BaseModel):
    id: str
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    status: TransactionStatus
    reference_id: str
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True