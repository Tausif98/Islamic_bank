"""
All Kafka event schemas live here. Every event has a standard envelope:
  - event_type: what happened
  - event_id: unique UUID for deduplication on consumer side
  - timestamp: when it happened
  - payload: the actual data

Consumers (analytics, notifications, audit) filter by event_type.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from app.core.kafka import publish_event
from app.core.config import settings
from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction


def _envelope(event_type: str, payload: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }


# ── Customer Events ───────────────────────────────────────────────────────────

async def emit_customer_created(customer: Customer):
    event = _envelope("customer.created", {
        "customer_id": str(customer.id),
        "full_name": customer.full_name,
        "email": customer.email,
        "phone": customer.phone,
        "status": customer.status.value,
    })
    await publish_event(settings.kafka_account_topic, event, key=str(customer.id))


async def emit_customer_status_changed(customer: Customer, old_status: str):
    event = _envelope("customer.status_changed", {
        "customer_id": str(customer.id),
        "old_status": old_status,
        "new_status": customer.status.value,
    })
    await publish_event(settings.kafka_account_topic, event, key=str(customer.id))


# ── Account Events ────────────────────────────────────────────────────────────

async def emit_account_opened(account: Account, customer_id: str):
    event = _envelope("account.opened", {
        "account_id": str(account.id),
        "customer_id": customer_id,
        "iban": account.iban,
        "account_type": account.account_type.value,
        "currency": account.currency,
        "profit_rate": str(account.profit_rate) if account.profit_rate else None,
    })
    await publish_event(settings.kafka_account_topic, event, key=account.iban)


async def emit_account_status_changed(account: Account, old_status: str):
    event = _envelope("account.status_changed", {
        "account_id": str(account.id),
        "iban": account.iban,
        "old_status": old_status,
        "new_status": account.status.value,
    })
    await publish_event(settings.kafka_account_topic, event, key=account.iban)


# ── Transaction Events ────────────────────────────────────────────────────────

async def emit_transaction_initiated(txn: Transaction, account: Account):
    event = _envelope("transaction.initiated", {
        "transaction_id": str(txn.id),
        "account_id": str(account.id),
        "iban": account.iban,
        "type": txn.transaction_type.value,
        "amount": str(txn.amount),
        "currency": txn.currency,
        "reference_id": txn.reference_id,
        "destination_iban": txn.destination_iban,
    })
    await publish_event(settings.kafka_transaction_topic, event, key=account.iban)


async def emit_transaction_completed(txn: Transaction, account: Account, new_balance: Decimal):
    event = _envelope("transaction.completed", {
        "transaction_id": str(txn.id),
        "account_id": str(account.id),
        "iban": account.iban,
        "type": txn.transaction_type.value,
        "amount": str(txn.amount),
        "currency": txn.currency,
        "new_balance": str(new_balance),
        "reference_id": txn.reference_id,
    })
    await publish_event(settings.kafka_transaction_topic, event, key=account.iban)


async def emit_transaction_failed(txn: Transaction, reason: str):
    event = _envelope("transaction.failed", {
        "transaction_id": str(txn.id),
        "reference_id": txn.reference_id,
        "reason": reason,
    })
    await publish_event(settings.kafka_transaction_topic, event)


# ── Fraud Events ──────────────────────────────────────────────────────────────

async def emit_fraud_alert(txn: Transaction, account: Account, reason: str, score: float):
    event = _envelope("fraud.alert", {
        "transaction_id": str(txn.id),
        "account_id": str(account.id),
        "iban": account.iban,
        "amount": str(txn.amount),
        "fraud_reason": reason,
        "fraud_score": score,
        "reference_id": txn.reference_id,
    })
    await publish_event(settings.kafka_fraud_topic, event, key=account.iban)


# ── Profit Events ─────────────────────────────────────────────────────────────

async def emit_profit_distributed(account: Account, profit_amount: Decimal, period: str):
    event = _envelope("profit.distributed", {
        "account_id": str(account.id),
        "iban": account.iban,
        "account_type": account.account_type.value,
        "profit_amount": str(profit_amount),
        "profit_rate": str(account.profit_rate),
        "period": period,           # e.g. "2025-01" for January 2025
        "new_balance": str(account.balance + profit_amount),
    })
    await publish_event(settings.kafka_profit_topic, event, key=account.iban)