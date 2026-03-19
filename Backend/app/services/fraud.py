"""
Rule-based fraud detection. Each rule returns a (triggered: bool, score: float, reason: str).
Total score >= threshold → flag as fraud.

In production, replace/augment with ML model scoring via an internal API call.
"""
from decimal import Decimal
from dataclasses import dataclass
from app.models.account import Account
from app.models.transaction import Transaction


@dataclass
class FraudResult:
    is_fraud: bool
    score: float        # 0.0 - 1.0
    reason: str


# ── Individual Rules ──────────────────────────────────────────────────────────

def _rule_large_amount(amount: Decimal, balance: Decimal) -> tuple[bool, float, str]:
    """Withdrawing more than 80% of balance in one shot."""
    if balance > 0 and (amount / balance) > Decimal("0.80"):
        return True, 0.4, "Large single withdrawal (>80% of balance)"
    return False, 0.0, ""


def _rule_amount_threshold(amount: Decimal) -> tuple[bool, float, str]:
    """Transactions above 500,000 PKR trigger review."""
    if amount > Decimal("500000"):
        return True, 0.3, "High-value transaction above threshold"
    return False, 0.0, ""


def _rule_zero_balance_withdrawal(amount: Decimal, balance: Decimal) -> tuple[bool, float, str]:
    """Attempting to withdraw from near-zero balance."""
    if balance < Decimal("100") and amount > Decimal("0"):
        return True, 0.5, "Withdrawal from near-zero balance account"
    return False, 0.0, ""


def _rule_round_number(amount: Decimal) -> tuple[bool, float, str]:
    """
    Fraudsters often test with exact round numbers (1000, 5000, 10000).
    Low weight — just a signal, not conclusive.
    """
    if amount % Decimal("1000") == 0 and amount >= Decimal("10000"):
        return True, 0.1, "Suspiciously round transaction amount"
    return False, 0.0, ""


# ── Main Engine ───────────────────────────────────────────────────────────────

FRAUD_THRESHOLD = 0.5   # Total score >= 0.5 → flag


def check_fraud(account: Account, transaction: Transaction) -> FraudResult:
    """
    Run all rules and aggregate scores.
    Returns FraudResult with combined score and first triggered reason.
    """
    rules = [
        _rule_large_amount(transaction.amount, account.balance),
        _rule_amount_threshold(transaction.amount),
        _rule_zero_balance_withdrawal(transaction.amount, account.balance),
        _rule_round_number(transaction.amount),
    ]

    total_score = 0.0
    reasons = []

    for triggered, score, reason in rules:
        if triggered:
            total_score += score
            reasons.append(reason)

    is_fraud = total_score >= FRAUD_THRESHOLD
    combined_reason = "; ".join(reasons) if reasons else "clean"

    return FraudResult(
        is_fraud=is_fraud,
        score=round(min(total_score, 1.0), 4),
        reason=combined_reason,
    )