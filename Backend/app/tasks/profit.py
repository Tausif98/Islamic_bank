"""
Celery tasks for profit distribution.
These run in a separate worker process — NOT inside FastAPI.
They use asyncio.run() because Celery tasks are synchronous by default.

To run the worker:
  celery -A app.core.celery_app worker --loglevel=info
  celery -A app.core.celery_app beat --loglevel=info   # for scheduled tasks
"""
import asyncio
import logging
from datetime import datetime
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Bridge sync Celery → async code."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _distribute_profit_async():
    """
    Core logic:
    1. Find all active savings/investment accounts
    2. Calculate daily profit for each
    3. Create a PROFIT_DISTRIBUTION transaction
    4. Update balance
    5. Emit profit.distributed Kafka event
    """
    from app.db.mongodb import connect_to_mongo
    from app.models.account import Account
    from app.models.enums import AccountStatus, AccountType
    from app.db.repositories.account_repo import account_repo
    from app.db.repositories.transaction_repo import transaction_repo
    from app.models.enums import TransactionType
    from app.services.islamic import get_daily_profit_for_account
    from app.services import kafka_events
    import uuid

    await connect_to_mongo()

    profit_bearing_types = [AccountType.SAVINGS, AccountType.INVESTMENT, AccountType.MUSHARAKAH]
    accounts = await Account.find(
        Account.status == AccountStatus.ACTIVE,
        Account.account_type.in_(profit_bearing_types),  # type: ignore
    ).to_list()

    period = datetime.utcnow().strftime("%Y-%m-%d")
    distributed = 0

    for account in accounts:
        if not account.profit_rate or account.balance <= 0:
            continue

        profit = get_daily_profit_for_account(
            balance=account.balance,
            account_type=account.account_type,
            annual_rate=account.profit_rate,
        )

        if profit <= 0:
            continue

        # Create transaction record
        txn = await transaction_repo.create(
            account=account,
            transaction_type=TransactionType.PROFIT_DISTRIBUTION,
            amount=profit,
            reference_id=f"profit-{str(account.id)}-{period}",
            description=f"Daily Mudarabah profit distribution for {period}",
        )

        new_balance = account.balance + profit
        await account_repo.update_balance(account, new_balance)
        await transaction_repo.mark_completed(txn)
        await kafka_events.emit_profit_distributed(account, profit, period)

        distributed += 1
        logger.info(f"Profit distributed to {account.iban}: {profit} {account.currency}")

    logger.info(f"Daily profit distribution complete. Accounts processed: {distributed}")
    return distributed


@celery_app.task(name="app.tasks.profit.distribute_daily_profit", bind=True, max_retries=3)
def distribute_daily_profit(self):
    try:
        return _run_async(_distribute_profit_async())
    except Exception as exc:
        logger.error(f"Profit distribution failed: {exc}")
        raise self.retry(exc=exc, countdown=60)     # Retry after 60s


@celery_app.task(name="app.tasks.profit.distribute_monthly_investment_profit")
def distribute_monthly_investment_profit():
    """
    Monthly profit for INVESTMENT accounts — higher rate, credited monthly not daily.
    Reuses same logic but filters to INVESTMENT type only.
    """
    logger.info("Monthly investment profit distribution triggered.")
    return _run_async(_distribute_profit_async())