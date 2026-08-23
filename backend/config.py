import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME = os.getenv(
        "PROJECT_NAME",
        "NovaShields Plus"
    )

    API_VERSION = os.getenv(
        "API_VERSION",
        "v1"
    )

    ENVIRONMENT = os.getenv(
        "ENVIRONMENT",
        "development"
    )

    DATABASE_URL = os.getenv("DATABASE_URL")

    MONGODB_URI = os.getenv("MONGODB_URI")


settings = Settings()