from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import CustomerStatus


class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str


class Customer(Document):
    """
    Beanie Document = MongoDB collection called 'customers'.
    Indexed() = creates a MongoDB index → faster lookups.
    """
    full_name: str
    email: Indexed(EmailStr, unique=True)       # type: ignore  # unique index
    phone: Indexed(str, unique=True)             # type: ignore
    national_id: Indexed(str, unique=True)       # type: ignore  # CNIC/Passport
    hashed_password: str
    address: Optional[Address] = None
    status: CustomerStatus = CustomerStatus.KYC_PENDING
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "customers"          # MongoDB collection name
        use_revision = True         # Optimistic locking (prevents race conditions on updates)

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Ahmed Al-Rashid",
                "email": "ahmed@example.com",
                "phone": "+92-300-1234567",
                "national_id": "42101-1234567-1",
                "address": {
                    "street": "123 Main St",
                    "city": "Karachi",
                    "country": "Pakistan",
                    "postal_code": "75500"
                }
            }
        }


# ── Pydantic schemas (request/response shapes, NOT stored in DB) ──────────────

class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    national_id: str
    password: str
    address: Optional[Address] = None


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Address] = None


class CustomerResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    national_id: str
    status: CustomerStatus
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True