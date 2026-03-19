import logging
# from pymongo.asynchronous.mongo_client import AsyncMongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from beanie import init_beanie
from app.core.config import settings
from app.models import BEANIE_MODELS

logger = logging.getLogger(__name__)

# Module-level client — Motor uses asyncio internally, safe to share
# _client: AsyncMongoClient | None = None
_client: AsyncIOMotorClient | None = None


async def connect_to_mongo():
    """
    Called on FastAPI startup event.
    Motor creates a connection pool automatically (default: 100 connections).
    init_beanie: registers all Document models, creates indexes defined on fields.
    """
    global _client
    _client = AsyncIOMotorClient(
        settings.mongodb_url,
        tls=True,                     # Required for Atlas
        tlsAllowInvalidCertificates=False,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000,
        retryWrites=True,              # Recommended for production
        retryReads=True,
    )
    logger.info(f"Targeting database: '{settings.mongodb_db_name}'")


    # Verify connection before declaring success
    # await _client.admin.command("ping")
    try:
        await _client.admin.command("ping")
        logger.info("MongoDB ping succeeded")
    except Exception as e:
        logger.error(f"MongoDB ping failed: {str(e)}", exc_info=True)
        raise

    await init_beanie(
        database=_client[settings.mongodb_db_name],
        document_models=BEANIE_MODELS,
    )
    logger.info(f"Connected to MongoDB: {settings.mongodb_db_name}")


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_database():
    """Direct DB access for raw queries outside Beanie (e.g., aggregations)."""
    if _client is None:
        raise RuntimeError("MongoDB not connected.")
    return _client[settings.mongodb_db_name]