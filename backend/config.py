import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "Rhythm")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    FRONTEND_URL = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    )

    @classmethod
    def validate(cls):
        missing = []

        if not cls.MONGO_URI:
            missing.append("MONGO_URI")

        if not cls.JWT_SECRET_KEY:
            missing.append("JWT_SECRET_KEY")

        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        if len(cls.JWT_SECRET_KEY) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY must be at least 32 characters long."
            )