from datetime import datetime, timezone

from bson import ObjectId
from werkzeug.security import generate_password_hash


def create_user(
    db,
    name: str,
    email: str,
    password: str
):
    now = datetime.now(timezone.utc)

    user = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": generate_password_hash(password),
        "favorite_artists": [],
        "favorite_songs": [],
        "favorite_genres": [],
        "created_at": now,
        "updated_at": now,
    }

    result = db.users.insert_one(user)

    user["_id"] = result.inserted_id

    return user


def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "favorite_artists": user.get(
            "favorite_artists",
            []
        ),
        "favorite_songs": user.get(
            "favorite_songs",
            []
        ),
        "favorite_genres": user.get(
            "favorite_genres",
            []
        ),
        "created_at": user.get(
            "created_at"
        ).isoformat()
        if user.get("created_at")
        else None,
    }


def find_user_by_email(db, email: str):
    return db.users.find_one({
        "email": email.strip().lower()
    })


def find_user_by_id(db, user_id: str):
    if not ObjectId.is_valid(user_id):
        return None

    return db.users.find_one({
        "_id": ObjectId(user_id)
    })