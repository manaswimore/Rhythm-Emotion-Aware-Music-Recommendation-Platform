from pymongo import MongoClient
from pymongo.server_api import ServerApi

from config import Config


def create_mongo_client():
    mongo_uri = Config.MONGO_URI

    if mongo_uri.startswith("mongodb+srv://"):
        return MongoClient(
            mongo_uri,
            server_api=ServerApi(
                version="1",
                strict=True,
                deprecation_errors=True
            ),
            serverSelectionTimeoutMS=5000,
        )

    return MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,
    )


def initialize_database(app):
    client = create_mongo_client()

    # Verify connection during startup.
    client.admin.command("ping")

    database = client[Config.MONGO_DB]

    app.extensions["mongo_client"] = client
    app.extensions["mongo_db"] = database

    # Users must have unique emails.
    database.users.create_index(
        "email",
        unique=True
    )

    return database


def get_db():
    from flask import current_app

    return current_app.extensions["mongo_db"]