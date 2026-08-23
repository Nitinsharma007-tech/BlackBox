from pymongo import MongoClient
from backend.config import settings


if settings.MONGODB_URI:
    mongo_client = MongoClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
    )
else:
    mongo_client = None


def get_mongo_client():
    """
    Returns the MongoDB client.
    """
    if mongo_client is None:
        raise RuntimeError(
            "MONGODB_URI is not configured in the .env file."
        )

    return mongo_client


def get_database():
    """
    Returns the NovaShields MongoDB database.
    """
    client = get_mongo_client()

    # Uses the database specified in the MongoDB URI.
    # If none is specified, change this later to an explicit name.
    database = client.get_default_database()

    return database


def test_mongodb_connection():
    """
    Tests whether MongoDB is reachable.
    """
    if mongo_client is None:
        return {
            "status": "not_configured",
            "message": "MONGODB_URI is not configured.",
        }

    try:
        mongo_client.admin.command("ping")

        return {
            "status": "connected",
            "message": "MongoDB connection successful.",
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }