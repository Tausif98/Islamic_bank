"""
FastAPI Dependencies — injected via Depends() in route functions.

Pattern: route → Depends(get_current_customer) → JWT decode → DB lookup → Customer object
If any step fails, FastAPI returns the appropriate HTTP error automatically.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.db.repositories.customer_repo import customer_repo
from app.models.customer import Customer

# Tells FastAPI where the login endpoint is (for OpenAPI docs auth button)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/customers/login")


async def get_current_customer(token: str = Depends(oauth2_scheme)) -> Customer:
    """
    Injected into any route that needs an authenticated user.
    Decodes JWT → extracts customer_id → fetches from DB.
    """
    payload = decode_access_token(token)
    customer_id: str = payload.get("sub")

    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    customer = await customer_repo.get_by_id(customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer not found or inactive",
        )

    return customer


async def get_active_customer(
    customer: Customer = Depends(get_current_customer),
) -> Customer:
    """Extra check: customer must be KYC-verified (ACTIVE status)."""
    from app.models.enums import CustomerStatus
    if customer.status != CustomerStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account access denied. Status: {customer.status.value}",
        )
    return customer