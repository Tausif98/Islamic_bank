"""
Islamic Finance Calculation Engine

Key products:
1. Mudarabah (profit-sharing): Bank + customer share profits. No interest.
   Formula: Profit = Principal × Rate × (Days/365)
   
2. Murabaha (cost-plus): Bank buys asset at cost X, sells to customer at X + markup.
   Customer pays in installments. Markup is fixed, not interest (no compounding).
   
3. Musharakah (partnership): Both parties contribute capital and share profit/loss
   proportional to their ownership stake.
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from app.models.enums import AccountType


def calculate_mudarabah_profit(
    principal: Decimal,
    annual_rate: Decimal,
    days: int,
) -> Decimal:
    """
    Daily Mudarabah profit for savings/investment accounts.
    
    Example: 100,000 PKR at 5% annual for 30 days
    = 100,000 × 0.05 × (30/365) = 410.96 PKR
    """
    profit = principal * annual_rate * Decimal(days) / Decimal("365")
    return profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_murabaha_installment(
    cost_price: Decimal,
    markup_rate: Decimal,     # e.g. 0.12 = 12% markup on cost
    installments: int,
) -> dict:
    """
    Murabaha: Fixed-price installment plan.
    Total sale price = cost + fixed markup (calculated once, never compounds).
    
    Example: Car costs 1,000,000 PKR, 12% markup, 12 installments
    Total = 1,120,000 PKR | Monthly = 93,333.33 PKR
    """
    markup_amount = cost_price * markup_rate
    total_price = cost_price + markup_amount
    monthly = total_price / Decimal(installments)

    return {
        "cost_price": str(cost_price),
        "markup_rate": str(markup_rate),
        "markup_amount": str(markup_amount.quantize(Decimal("0.01"))),
        "total_sale_price": str(total_price.quantize(Decimal("0.01"))),
        "installments": installments,
        "monthly_installment": str(monthly.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
    }


def calculate_musharakah_profit(
    total_profit: Decimal,
    bank_share_ratio: Decimal,      # e.g. 0.40 = bank takes 40%
    customer_share_ratio: Decimal,  # e.g. 0.60 = customer takes 60%
) -> dict:
    """
    Partnership profit distribution.
    Ratios must sum to 1.0. Losses shared proportional to capital contribution.
    """
    if bank_share_ratio + customer_share_ratio != Decimal("1.0"):
        raise ValueError("Profit share ratios must sum to 1.0")

    bank_profit = (total_profit * bank_share_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    customer_profit = (total_profit * customer_share_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "total_profit": str(total_profit),
        "bank_share": str(bank_profit),
        "customer_share": str(customer_profit),
    }


def get_daily_profit_for_account(
    balance: Decimal,
    account_type: AccountType,
    annual_rate: Decimal,
) -> Decimal:
    """
    Convenience wrapper for Celery daily task.
    Returns profit amount to credit for 1 day.
    """
    if account_type not in (AccountType.SAVINGS, AccountType.INVESTMENT, AccountType.MUSHARAKAH):
        return Decimal("0.00")   # Current accounts = Qard, no profit

    return calculate_mudarabah_profit(balance, annual_rate, days=1)