from fastapi import APIRouter, Depends, HTTPException
from app.db.repositories.account_repo import account_repo
from app.db.repositories.transaction_repo import transaction_repo
from app.models.transaction import (
    DepositRequest, WithdrawalRequest, TransferRequest, TransactionResponse
)
from app.models.customer import Customer
from app.api.dependencies import get_active_customer
from app.services.transaction import transaction_service

router = APIRouter(prefix="/accounts/{account_id}/transactions", tags=["Transactions"])


async def _verify_account_ownership(account_id: str, customer: Customer):
    """Reusable guard: ensures the account belongs to the requesting customer."""
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await account.fetch_link(account.customer)
    if str(account.customer.id) != str(customer.id):    # type: ignore
        raise HTTPException(status_code=403, detail="Access denied")
    return account


@router.post("/deposit", response_model=TransactionResponse, status_code=201)
async def deposit(
    account_id: str,
    req: DepositRequest,
    current_customer: Customer = Depends(get_active_customer),
):
    await _verify_account_ownership(account_id, current_customer)
    txn = await transaction_service.deposit(account_id, req)
    return _to_response(txn)


@router.post("/withdraw", response_model=TransactionResponse, status_code=201)
async def withdraw(
    account_id: str,
    req: WithdrawalRequest,
    current_customer: Customer = Depends(get_active_customer),
):
    await _verify_account_ownership(account_id, current_customer)
    txn = await transaction_service.withdraw(account_id, req)
    return _to_response(txn)


@router.post("/transfer", response_model=TransactionResponse, status_code=201)
async def transfer(
    account_id: str,
    req: TransferRequest,
    current_customer: Customer = Depends(get_active_customer),
):
    await _verify_account_ownership(account_id, current_customer)
    txn = await transaction_service.transfer(account_id, req)
    return _to_response(txn)


@router.get("/", response_model=list[TransactionResponse])
async def transaction_history(
    account_id: str,
    skip: int = 0,
    limit: int = 50,
    current_customer: Customer = Depends(get_active_customer),
):
    await _verify_account_ownership(account_id, current_customer)
    transactions = await transaction_repo.get_account_history(account_id, skip, limit)
    return [_to_response(t) for t in transactions]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    account_id: str,
    transaction_id: str,
    current_customer: Customer = Depends(get_active_customer),
):
    await _verify_account_ownership(account_id, current_customer)
    txn = await transaction_repo.get_by_id(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_response(txn)


def _to_response(txn) -> TransactionResponse:
    return TransactionResponse(
        id=str(txn.id),
        transaction_type=txn.transaction_type,
        amount=txn.amount,
        currency=txn.currency,
        status=txn.status,
        reference_id=txn.reference_id,
        description=txn.description,
        created_at=txn.created_at,
        completed_at=txn.completed_at,
    )