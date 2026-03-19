from datetime import datetime
from decimal import Decimal
from typing import Optional
from beanie import PydanticObjectId
from app.models.transaction import Transaction, LedgerEntry
from app.models.account import Account
from app.models.enums import TransactionType, TransactionStatus


class TransactionRepository:

    async def create(
        self,
        account: Account,
        transaction_type: TransactionType,
        amount: Decimal,
        reference_id: str,
        description: Optional[str] = None,
        destination_iban: Optional[str] = None,
        ledger_entry: Optional[LedgerEntry] = None,
        metadata: dict = None,
    ) -> Transaction:
        txn = Transaction(
            account=account,
            transaction_type=transaction_type,
            amount=amount,
            currency=account.currency,
            reference_id=reference_id,
            description=description,
            destination_iban=destination_iban,
            ledger_entry=ledger_entry,
            metadata=metadata or {},
        )
        await txn.insert()
        return txn

    async def get_by_id(self, txn_id: str) -> Optional[Transaction]:
        return await Transaction.get(PydanticObjectId(txn_id))

    async def get_by_reference(self, reference_id: str) -> Optional[Transaction]:
        """Idempotency check — if reference_id exists, return existing transaction."""
        return await Transaction.find_one(Transaction.reference_id == reference_id)

    async def get_account_history(
        self, account_id: str, skip: int = 0, limit: int = 50
    ) -> list[Transaction]:
        account_ref = PydanticObjectId(account_id)
        return await Transaction.find(
            Transaction.account.id == account_ref  # type: ignore
        ).sort(-Transaction.created_at).skip(skip).limit(limit).to_list()

    async def mark_completed(self, txn: Transaction) -> Transaction:
        await txn.set({
            Transaction.status: TransactionStatus.COMPLETED,
            Transaction.completed_at: datetime.utcnow(),
        })
        return txn

    async def mark_failed(self, txn: Transaction, reason: str) -> Transaction:
        await txn.set({
            Transaction.status: TransactionStatus.FAILED,
            Transaction.metadata: {**txn.metadata, "failure_reason": reason},
        })
        return txn

    async def mark_flagged(self, txn: Transaction, fraud_reason: str) -> Transaction:
        await txn.set({
            Transaction.status: TransactionStatus.FLAGGED,
            Transaction.metadata: {**txn.metadata, "fraud_reason": fraud_reason},
        })
        return txn


transaction_repo = TransactionRepository()