from fastapi import APIRouter, Depends, HTTPException
from app.db.repositories.account_repo import account_repo
from app.models.account import AccountCreate, AccountResponse
from app.models.customer import Customer
from app.api.dependencies import get_active_customer
from app.services import kafka_events
from app.services.islamic import calculate_murabaha_installment
from decimal import Decimal

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse, status_code=201)
async def open_account(
    data: AccountCreate,
    current_customer: Customer = Depends(get_active_customer),
):
    """Open a new Islamic banking account for the authenticated customer."""
    account = await account_repo.create(current_customer, data)
    await kafka_events.emit_account_opened(account, str(current_customer.id))

    return AccountResponse(
        id=str(account.id),
        iban=account.iban,
        account_type=account.account_type,
        balance=account.balance,
        currency=account.currency,
        status=account.status,
        profit_rate=account.profit_rate,
        created_at=account.created_at,
    )


@router.get("/", response_model=list[AccountResponse])
async def list_my_accounts(current_customer: Customer = Depends(get_active_customer)):
    accounts = await account_repo.get_customer_accounts(str(current_customer.id))
    return [
        AccountResponse(
            id=str(a.id),
            iban=a.iban,
            account_type=a.account_type,
            balance=a.balance,
            currency=a.currency,
            status=a.status,
            profit_rate=a.profit_rate,
            created_at=a.created_at,
        )
        for a in accounts
    ]


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_customer: Customer = Depends(get_active_customer),
):
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Security: customers can only view their own accounts
    # fetch_links resolves the Link[Customer] reference
    await account.fetch_link(account.customer)
    if str(account.customer.id) != str(current_customer.id):    # type: ignore
        raise HTTPException(status_code=403, detail="Access denied")

    return AccountResponse(
        id=str(account.id),
        iban=account.iban,
        account_type=account.account_type,
        balance=account.balance,
        currency=account.currency,
        status=account.status,
        profit_rate=account.profit_rate,
        created_at=account.created_at,
    )


@router.post("/{account_id}/freeze")
async def freeze_account(
    account_id: str,
    current_customer: Customer = Depends(get_active_customer),
):
    """Self-service freeze (e.g., lost card). Admin can also freeze for compliance."""
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    old_status = account.status.value
    updated = await account_repo.freeze(account)
    await kafka_events.emit_account_status_changed(updated, old_status)
    return {"message": f"Account {account.iban} frozen successfully"}


@router.get("/murabaha/calculator")
async def murabaha_calculator(
    cost_price: Decimal,
    markup_rate: Decimal,
    installments: int,
    _: Customer = Depends(get_active_customer),
):
    """
    Murabaha financing calculator.
    Example: GET /accounts/murabaha/calculator?cost_price=1000000&markup_rate=0.12&installments=12
    """
    return calculate_murabaha_installment(cost_price, markup_rate, installments)