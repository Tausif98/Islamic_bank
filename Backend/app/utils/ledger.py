"""
Double-Entry Bookkeeping
Every transaction has EXACTLY two sides:
  - Debit: money leaves this account  
  - Credit: money enters this account

This is the foundation of accounting. Every PKR that leaves one account
enters another — the books always balance.

Special accounts:
  "VAULT" = the bank's cash vault (internal ledger account)
  "PROFIT_POOL" = pool for Mudarabah profit distributions
"""
from decimal import Decimal
from app.models.transaction import LedgerEntry


def build_ledger_entry(
    debit_account_id: str,
    credit_account_id: str,
    amount: Decimal,
) -> LedgerEntry:
    """
    Deposit:   VAULT → Customer Account    (bank gives money to customer)
    Withdraw:  Customer Account → VAULT    (customer returns money to bank)
    Transfer:  Account A → Account B       (internal move)
    Profit:    PROFIT_POOL → Customer Account
    """
    if amount <= Decimal("0"):
        raise ValueError("Ledger entry amount must be positive")

    return LedgerEntry(
        debit_account_id=debit_account_id,
        credit_account_id=credit_account_id,
        amount=amount,
    )