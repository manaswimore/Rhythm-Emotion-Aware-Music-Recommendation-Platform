from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash

from db import get_db
from models.user_model import (
    create_user,
    find_user_by_email,
    find_user_by_id,
    serialize_user,
)
from utils.validators import (
    validate_login_data,
    validate_register_data,
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)

    error = validate_register_data(data)

    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    db = get_db()

    existing_user = find_user_by_email(
        db,
        email
    )

    if existing_user:
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    try:
        user = create_user(
            db=db,
            name=name,
            email=email,
            password=password
        )

    except DuplicateKeyError:
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    access_token = create_access_token(
        identity=str(user["_id"])
    )

    return jsonify({
        "success": True,
        "message": "Account created successfully.",
        "token": access_token,
        "user": serialize_user(user)
    }), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)

    error = validate_login_data(data)

    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 400

    email = data["email"].strip().lower()
    password = data["password"]

    db = get_db()

    user = find_user_by_email(
        db,
        email
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    password_valid = check_password_hash(
        user["password_hash"],
        password
    )

    if not password_valid:
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    access_token = create_access_token(
        identity=str(user["_id"])
    )

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": access_token,
        "user": serialize_user(user)
    }), 200


@auth_bp.get("/me")
@jwt_required()
def current_user():
    user_id = get_jwt_identity()

    db = get_db()

    user = find_user_by_id(
        db,
        user_id
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    return jsonify({
        "success": True,
        "user": serialize_user(user)
    }), 200