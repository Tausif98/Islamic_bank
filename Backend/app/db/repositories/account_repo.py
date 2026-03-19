import random
import string
from decimal import Decimal
from typing import Optional
from beanie import PydanticObjectId
from app.models.account import Account, AccountCreate
from app.models.customer import Customer
from app.models.enums import AccountType, AccountStatus


def _generate_iban(country_code: str = "PK") -> str:
    """
    Simplified IBAN generator for demo purposes.
    Real IBAN uses MOD-97 checksum: https://en.wikipedia.org/wiki/IBAN
    """
    bank_code = "ISLB"
    account_number = ''.join(random.choices(string.digits, k=16))
    return f"{country_code}{bank_code}{account_number}"


# Default profit rates per account type (annual, as Decimal)
PROFIT_RATES = {
    AccountType.SAVINGS: Decimal("0.05"),       # 5% annual Mudarabah profit
    AccountType.INVESTMENT: Decimal("0.08"),     # 8% annual for fixed-term investment
    AccountType.CURRENT: Decimal("0.00"),        # Current = Qard, no profit
    AccountType.MURABAHA: Decimal("0.00"),       # Murabaha uses fixed markup, not rate
    AccountType.MUSHARAKAH: Decimal("0.07"),     # 7% partnership profit share
}


class AccountRepository:

    async def create(self, customer: Customer, data: AccountCreate) -> Account:
        account = Account(
            customer=customer,
            iban=_generate_iban(),
            account_type=data.account_type,
            balance=data.initial_deposit,
            currency=data.currency,
            profit_rate=PROFIT_RATES.get(data.account_type),
        )
        await account.insert()
        return account

    async def get_by_id(self, account_id: str) -> Optional[Account]:
        return await Account.get(PydanticObjectId(account_id))

    async def get_by_iban(self, iban: str) -> Optional[Account]:
        return await Account.find_one(Account.iban == iban)

    async def get_customer_accounts(self, customer_id: str) -> list[Account]:
        """Fetch all accounts for a customer. Uses fetch_links=True to resolve the Link."""
        customer_ref = PydanticObjectId(customer_id)
        return await Account.find(
            Account.customer.id == customer_ref  # type: ignore
        ).to_list()

    async def update_balance(self, account: Account, new_balance: Decimal) -> Account:
        await account.set({Account.balance: new_balance})
        return account

    async def freeze(self, account: Account) -> Account:
        await account.set({Account.status: AccountStatus.FROZEN})
        return account

    async def close(self, account: Account) -> Account:
        await account.set({Account.status: AccountStatus.CLOSED})
        return account


account_repo = AccountRepository()