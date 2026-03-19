from typing import Optional
from beanie import PydanticObjectId
from app.models.customer import Customer, CustomerCreate, CustomerUpdate
from app.models.enums import CustomerStatus
from app.core.security import hash_password


class CustomerRepository:
    """
    All MongoDB operations for customers live here.
    Services call this — never touch Beanie models directly in routes.
    This separation lets you swap MongoDB for PostgreSQL without touching business logic.
    """

    async def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            national_id=data.national_id,
            hashed_password=hash_password(data.password),
            address=data.address,
            status=CustomerStatus.KYC_PENDING,
        )
        await customer.insert()
        return customer

    async def get_by_id(self, customer_id: str) -> Optional[Customer]:
        return await Customer.get(PydanticObjectId(customer_id))

    async def get_by_email(self, email: str) -> Optional[Customer]:
        return await Customer.find_one(Customer.email == email)

    async def get_by_national_id(self, national_id: str) -> Optional[Customer]:
        return await Customer.find_one(Customer.national_id == national_id)

    async def update(self, customer: Customer, data: CustomerUpdate) -> Customer:
        update_data = data.model_dump(exclude_none=True)
        if update_data:
            await customer.set(update_data)
        return customer

    async def activate(self, customer: Customer) -> Customer:
        await customer.set({Customer.status: CustomerStatus.ACTIVE})
        return customer

    async def suspend(self, customer: Customer) -> Customer:
        await customer.set({
            Customer.status: CustomerStatus.SUSPENDED,
            Customer.is_active: False,
        })
        return customer

    async def list_all(self, skip: int = 0, limit: int = 50) -> list[Customer]:
        return await Customer.find_all().skip(skip).limit(limit).to_list()


# Singleton instance — import this in services
customer_repo = CustomerRepository()