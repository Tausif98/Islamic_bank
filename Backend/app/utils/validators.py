import re
from decimal import Decimal


def validate_iban(iban: str) -> bool:
    """Basic IBAN format validation (length + alphanumeric)."""
    iban = iban.replace(" ", "").upper()
    return bool(re.match(r"^[A-Z]{2}[A-Z0-9]{14,30}$", iban))


def validate_positive_amount(amount: Decimal) -> Decimal:
    if amount <= Decimal("0"):
        raise ValueError("Amount must be positive")
    if amount > Decimal("10000000"):   # 10M PKR single transaction cap
        raise ValueError("Amount exceeds single transaction limit")
    return amount


def validate_currency(currency: str) -> str:
    supported = {"PKR", "USD", "EUR", "GBP", "SAR", "AED"}
    if currency.upper() not in supported:
        raise ValueError(f"Unsupported currency: {currency}")
    return currency.upper()