from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from services.emotion_detection import detect_emotion


emotion_bp = Blueprint(
    "emotion",
    __name__,
    url_prefix="/api/emotion",
)


@emotion_bp.post("/detect")
@jwt_required()
def detect():

    data = request.get_json(
        silent=True
    )

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required.",
        }), 400

    image = data.get("image")

    if not image:
        return jsonify({
            "success": False,
            "message": "Image is required.",
        }), 400

    try:

        result = detect_emotion(image)

        return jsonify({
            "success": True,
            "emotion": result["emotion"],
            "confidence": result["confidence"],
        }), 200

    except ValueError as exc:

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 422

    except Exception:

        return jsonify({
            "success": False,
            "message": "Emotion detection failed.",
        }), 500