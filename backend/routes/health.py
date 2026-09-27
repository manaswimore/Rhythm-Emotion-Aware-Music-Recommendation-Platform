from flask import Blueprint, jsonify

from db import get_db


health_bp = Blueprint(
    "health",
    __name__,
    url_prefix="/api"
)


@health_bp.get("/health")
def health_check():
    try:
        db = get_db()

        db.command("ping")

        return jsonify({
            "status": "ok",
            "service": "rhythm-api",
            "database": "connected"
        }), 200

    except Exception as exc:
        return jsonify({
            "status": "error",
            "service": "rhythm-api",
            "database": "unavailable",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }), 503