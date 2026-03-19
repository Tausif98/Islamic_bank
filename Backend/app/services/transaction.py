"""
Transaction Service — the heart of the banking logic.

Flow for any transaction:
1. Idempotency check (duplicate reference_id? return existing)
2. Create transaction record as PENDING
3. Emit 'transaction.initiated' to Kafka
4. Fraud check
5. Balance validation
6. Update balance (atomic-ish via Beanie revision locking)
7. Create ledger entry
8. Mark transaction COMPLETED
9. Emit 'transaction.completed' to Kafka
10. Push real-time update to Redis for WebSocket
"""
from decimal import Decimal
from fastapi import HTTPException, status
from app.db.repositories.account_repo import account_repo
from app.db.repositories.transaction_repo import transaction_repo
from app.models.transaction import Transaction, DepositRequest, WithdrawalRequest, TransferRequest, LedgerEntry
from app.models.enums import TransactionType, TransactionStatus, AccountStatus
from app.services.fraud import check_fraud
from app.services import kafka_events
from app.core.redis import publish_to_channel
from app.utils.ledger import build_ledger_entry


class TransactionService:

    async def deposit(self, account_id: str, req: DepositRequest) -> Transaction:
        account = await account_repo.get_by_id(account_id)
        if not account or account.status != AccountStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Account not found or inactive")

        # Idempotency: same reference_id = same transaction, don't double-credit
        existing = await transaction_repo.get_by_reference(req.reference_id)
        if existing:
            return existing

        txn = await transaction_repo.create(
            account=account,
            transaction_type=TransactionType.DEPOSIT,
            amount=req.amount,
            reference_id=req.reference_id,
            description=req.description,
        )
        await kafka_events.emit_transaction_initiated(txn, account)

        # Deposits don't need fraud check — only outflows
        new_balance = account.balance + req.amount
        ledger = build_ledger_entry(
            debit_account_id="VAULT",       # Money comes from vault
            credit_account_id=str(account.id),
            amount=req.amount,
        )

        await account_repo.update_balance(account, new_balance)
        await transaction_repo.mark_completed(txn)

        # Attach ledger to transaction
        await txn.set({Transaction.ledger_entry: ledger})
        await kafka_events.emit_transaction_completed(txn, account, new_balance)

        # Real-time notification via Redis → WebSocket handler
        await publish_to_channel(
            f"account:{account_id}",
            {"type": "balance_update", "balance": str(new_balance), "transaction_id": str(txn.id)}
        )

        return txn

    async def withdraw(self, account_id: str, req: WithdrawalRequest) -> Transaction:
        account = await account_repo.get_by_id(account_id)
        if not account or account.status != AccountStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Account not found or inactive")

        existing = await transaction_repo.get_by_reference(req.reference_id)
        if existing:
            return existing

        if account.balance < req.amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Insufficient balance"
            )

        txn = await transaction_repo.create(
            account=account,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=req.amount,
            reference_id=req.reference_id,
            description=req.description,
        )
        await kafka_events.emit_transaction_initiated(txn, account)

        # Fraud check BEFORE balance deduction
        fraud_result = check_fraud(account, txn)
        if fraud_result.is_fraud:
            await transaction_repo.mark_flagged(txn, fraud_result.reason)
            await kafka_events.emit_fraud_alert(txn, account, fraud_result.reason, fraud_result.score)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Transaction flagged for review: {fraud_result.reason}"
            )

        new_balance = account.balance - req.amount
        ledger = build_ledger_entry(
            debit_account_id=str(account.id),
            credit_account_id="VAULT",
            amount=req.amount,
        )

        await account_repo.update_balance(account, new_balance)
        await transaction_repo.mark_completed(txn)
        await txn.set({Transaction.ledger_entry: ledger})

        # Store fraud score in metadata even if not fraud
        await txn.set({Transaction.metadata: {"fraud_score": fraud_result.score}})

        await kafka_events.emit_transaction_completed(txn, account, new_balance)
        await publish_to_channel(
            f"account:{account_id}",
            {"type": "balance_update", "balance": str(new_balance), "transaction_id": str(txn.id)}
        )

        return txn

    async def transfer(self, source_account_id: str, req: TransferRequest) -> Transaction:
        source = await account_repo.get_by_id(source_account_id)
        if not source or source.status != AccountStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Source account not found or inactive")

        destination = await account_repo.get_by_iban(req.destination_iban)
        if not destination or destination.status != AccountStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Destination account not found or inactive")

        if source.balance < req.amount:
            raise HTTPException(status_code=422, detail="Insufficient balance")

        existing = await transaction_repo.get_by_reference(req.reference_id)
        if existing:
            return existing

        # Create ONE transaction record on the source account side
        txn = await transaction_repo.create(
            account=source,
            transaction_type=TransactionType.TRANSFER,
            amount=req.amount,
            reference_id=req.reference_id,
            description=req.description,
            destination_iban=req.destination_iban,
        )
        await kafka_events.emit_transaction_initiated(txn, source)

        fraud_result = check_fraud(source, txn)
        if fraud_result.is_fraud:
            await transaction_repo.mark_flagged(txn, fraud_result.reason)
            await kafka_events.emit_fraud_alert(txn, source, fraud_result.reason, fraud_result.score)
            raise HTTPException(status_code=403, detail=f"Transaction flagged: {fraud_result.reason}")

        new_source_balance = source.balance - req.amount
        new_dest_balance = destination.balance + req.amount
        ledger = build_ledger_entry(
            debit_account_id=str(source.id),
            credit_account_id=str(destination.id),
            amount=req.amount,
        )

        # Both balance updates should ideally be in a MongoDB transaction
        # Motor supports multi-document transactions on replica sets
        await account_repo.update_balance(source, new_source_balance)
        await account_repo.update_balance(destination, new_dest_balance)
        await transaction_repo.mark_completed(txn)
        await txn.set({Transaction.ledger_entry: ledger})

        await kafka_events.emit_transaction_completed(txn, source, new_source_balance)

        # Notify both accounts
        await publish_to_channel(
            f"account:{source_account_id}",
            {"type": "balance_update", "balance": str(new_source_balance)}
        )
        await publish_to_channel(
            f"account:{str(destination.id)}",
            {"type": "balance_update", "balance": str(new_dest_balance)}
        )

        return txn


transaction_service = TransactionService()