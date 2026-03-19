from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db.repositories.customer_repo import customer_repo
from app.models.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.models.enums import CustomerStatus
from app.core.security import verify_password, create_access_token
from app.api.dependencies import get_current_customer, get_active_customer
from app.models.customer import Customer
from app.services import kafka_events

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/register", response_model=CustomerResponse, status_code=201)
async def register_customer(data: CustomerCreate):
    """
    Register new customer. Status starts as KYC_PENDING.
    A compliance officer would manually activate via /activate endpoint.
    """
    # Check uniqueness before insert (Beanie's unique index also guards this)
    if await customer_repo.get_by_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    customer = await customer_repo.create(data)
    await kafka_events.emit_customer_created(customer)

    return CustomerResponse(
        id=str(customer.id),
        full_name=customer.full_name,
        email=customer.email,
        phone=customer.phone,
        national_id=customer.national_id,
        status=customer.status,
        is_active=customer.is_active,
        created_at=customer.created_at,
    )


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Standard OAuth2 password flow. Returns JWT bearer token.
    username field = email (OAuth2 spec uses 'username' field name)
    """
    customer = await customer_repo.get_by_email(form_data.username)
    if not customer or not verify_password(form_data.password, customer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not customer.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(customer.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=CustomerResponse)
async def get_my_profile(current_customer: Customer = Depends(get_current_customer)):
    return CustomerResponse(
        id=str(current_customer.id),
        full_name=current_customer.full_name,
        email=current_customer.email,
        phone=current_customer.phone,
        national_id=current_customer.national_id,
        status=current_customer.status,
        is_active=current_customer.is_active,
        created_at=current_customer.created_at,
    )


@router.patch("/me", response_model=CustomerResponse)
async def update_my_profile(
    data: CustomerUpdate,
    current_customer: Customer = Depends(get_current_customer),
):
    updated = await customer_repo.update(current_customer, data)
    return CustomerResponse(
        id=str(updated.id),
        full_name=updated.full_name,
        email=updated.email,
        phone=updated.phone,
        national_id=updated.national_id,
        status=updated.status,
        is_active=updated.is_active,
        created_at=updated.created_at,
    )


# ── Admin endpoints (in real app: add admin role check) ──────────────────────

@router.post("/{customer_id}/activate", response_model=CustomerResponse)
async def activate_customer(customer_id: str):
    """KYC approval — activates a KYC_PENDING customer."""
    customer = await customer_repo.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    old_status = customer.status.value
    updated = await customer_repo.activate(customer)
    await kafka_events.emit_customer_status_changed(updated, old_status)

    return CustomerResponse(
        id=str(updated.id),
        full_name=updated.full_name,
        email=updated.email,
        phone=updated.phone,
        national_id=updated.national_id,
        status=updated.status,
        is_active=updated.is_active,
        created_at=updated.created_at,
    )