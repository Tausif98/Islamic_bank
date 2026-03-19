
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app creation, router inclusion
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── security.py          # JWT utils, password hashing
│   │   ├── kafka.py             # Kafka producer singleton
│   │   ├── redis.py             # Redis client (for pub/sub, caching)
│   │   └── celery_app.py        # Celery instance
│   ├── models/
│   │   ├── __init__.py
│   │   ├── customer.py          # Pydantic models + MongoDB ODM (Motor)
│   │   ├── account.py
│   │   ├── transaction.py
│   │   └── enums.py             # Shared enums (AccountType, TransactionStatus)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── mongodb.py            # MongoDB client setup
│   │   └── repositories/         # Data access layer
│   │       ├── customer_repo.py
│   │       ├── account_repo.py
│   │       └── transaction_repo.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py       # Common dependencies (get_current_user, get_db)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── customers.py      # Customer endpoints
│   │   │   ├── accounts.py       # Account endpoints
│   │   │   ├── transactions.py   # Deposit, withdrawal, history
│   │   │   └── websocket.py      # WebSocket handler
│   ├── services/
│   │   ├── __init__.py
│   │   ├── islamic.py            # Islamic product calculations (Mudarabah profit, etc.)
│   │   ├── transaction.py        # Business logic for transactions
│   │   ├── fraud.py              # Simple rule engine for fraud detection
│   │   └── kafka_events.py       # Helper functions to send events
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── profit.py             # Celery tasks for profit calculation
│   └── utils/
│       ├── __init__.py
│       ├── ledger.py             # Double‑entry bookkeeping
│       └── validators.py         # Custom validators (e.g., IBAN)
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures (MongoDB, Kafka)
│   ├── test_customers.py
│   ├── test_accounts.py
│   └── test_transactions.py
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml            # (already above)
└── README.md



# Islamic Bank API

A production-ready Islamic banking backend built with **FastAPI**, **MongoDB (Beanie/Motor)**, **Kafka**, **Redis**, and **Celery**.

## Architecture

```
Client → FastAPI (REST + WebSocket)
           ├── MongoDB (Atlas/local) — persistent data (customers, accounts, transactions)
           ├── Kafka — event streaming (audit, analytics, notifications)
           ├── Redis — WebSocket pub/sub + caching
           └── Celery + Redis — background jobs (daily profit distribution)
```

## Islamic Products Supported

| Product | Type | Profit |
|---------|------|--------|
| Current Account | Qard (interest-free) | None |
| Savings Account | Mudarabah | 5% annual (daily accrual) |
| Investment Account | Mudarabah fixed-term | 8% annual (monthly) |
| Murabaha Financing | Cost-plus sale | Fixed markup |
| Musharakah | Joint venture | 7% annual, split by ratio |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set MONGODB_URL to your Atlas URI

# 2. Start infrastructure + app
docker compose up -d

# 3. API is live at:
#    http://localhost:8000/docs   ← Swagger UI
#    http://localhost:8081        ← MongoDB Express
```

## API Endpoints

```
POST   /api/v1/customers/register          Register new customer
POST   /api/v1/customers/login             Get JWT token
GET    /api/v1/customers/me                My profile
PATCH  /api/v1/customers/me                Update profile
POST   /api/v1/customers/{id}/activate     KYC approval (admin)

POST   /api/v1/accounts/                   Open account
GET    /api/v1/accounts/                   List my accounts
GET    /api/v1/accounts/{id}               Account details
POST   /api/v1/accounts/{id}/freeze        Freeze account
GET    /api/v1/accounts/murabaha/calculator  Murabaha calc

POST   /api/v1/accounts/{id}/transactions/deposit     Deposit
POST   /api/v1/accounts/{id}/transactions/withdraw    Withdraw
POST   /api/v1/accounts/{id}/transactions/transfer    Transfer
GET    /api/v1/accounts/{id}/transactions/            History

WS     /ws/{account_id}?token=<JWT>        Real-time balance updates
```

## Kafka Topics

| Topic | Events |
|-------|--------|
| `account-events` | customer.created, account.opened, status changes |
| `transaction-events` | transaction.initiated, completed, failed |
| `profit-events` | profit.distributed |
| `fraud-alerts` | fraud.alert |

## Run Tests

```bash
pip install -r requirements.txt
pytest -v
```

## Run Celery Workers (development)

```bash
# Worker
celery -A app.core.celery_app worker --loglevel=info

# Beat scheduler (periodic tasks)
celery -A app.core.celery_app beat --loglevel=info
```









docker logs islamic_bank_api --follow
