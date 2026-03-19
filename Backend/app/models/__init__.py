from app.models.customer import Customer, CustomerCreate, CustomerUpdate, CustomerResponse
from app.models.account import Account, AccountCreate, AccountResponse
from app.models.transaction import Transaction, DepositRequest, WithdrawalRequest, TransferRequest, TransactionResponse
from app.models.enums import (
    AccountType, TransactionType, TransactionStatus,
    CustomerStatus, AccountStatus, KafkaTopics
)

# All Beanie Document models — used in init_beanie()
BEANIE_MODELS = [Customer, Account, Transaction]

__all__ = [
    "Customer", "CustomerCreate", "CustomerUpdate", "CustomerResponse",
    "Account", "AccountCreate", "AccountResponse",
    "Transaction", "DepositRequest", "WithdrawalRequest", "TransferRequest", "TransactionResponse",
    "AccountType", "TransactionType", "TransactionStatus",
    "CustomerStatus", "AccountStatus", "KafkaTopics",
    "BEANIE_MODELS",
]