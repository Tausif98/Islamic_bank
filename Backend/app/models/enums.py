from enum import Enum


class AccountType(str, Enum):
    """
    Islamic banking products:
    - CURRENT: Qard (interest-free loan to bank, no profit sharing)
    - SAVINGS: Mudarabah (profit-sharing savings account)
    - INVESTMENT: Mudarabah investment with fixed term
    - MURABAHA: Cost-plus financing (bank buys asset, sells to customer at markup)
    - MUSHARAKAH: Joint venture / partnership financing
    """
    CURRENT = "current"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    MURABAHA = "murabaha"
    MUSHARAKAH = "musharakah"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PROFIT_DISTRIBUTION = "profit_distribution"
    FEE = "fee"
    MURABAHA_PAYMENT = "murabaha_payment"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    FLAGGED = "flagged"          # Fraud flagged, needs review


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    KYC_PENDING = "kyc_pending"  # Know Your Customer verification pending


class AccountStatus(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class KafkaTopics(str, Enum):
    ACCOUNT_EVENTS = "account-events"
    TRANSACTION_EVENTS = "transaction-events"
    PROFIT_EVENTS = "profit-events"
    FRAUD_ALERTS = "fraud-alerts"
    NOTIFICATION_EVENTS = "notification-events"