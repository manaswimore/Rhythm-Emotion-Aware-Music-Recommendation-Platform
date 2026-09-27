from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from db import initialize_database

from routes.auth import auth_bp
from routes.health import health_bp
from routes.emotion import emotion_bp
from routes.recommendations import recommendation_bp


def create_app():
    Config.validate()

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES

    JWTManager(app)

    initialize_database(app)

    allowed_origins = [
        "https://rhythm-emotion-aware-music-recommendation-platform.vercel.app",
        "http://localhost:5173",
    ]

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": False,
                "automatic_options": True,
                "vary_header": True,
            }
        },
    )

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Max-Age"] = "600"
            response.headers["Vary"] = "Origin"
        return response

    @app.route("/api/emotion/detect", methods=["OPTIONS"])
    def emotion_detect_options():
        response = app.response_class(status=204)
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Max-Age"] = "600"
            response.headers["Vary"] = "Origin"
        return response

    @app.errorhandler(413)
    def payload_too_large(_error):
        return jsonify({
            "success": False,
            "message": "Captured image is too large. Please try again.",
        }), 413

    @app.get("/")
    def index():
        return jsonify({
            "service": "RHYTHM API",
            "status": "running",
        })

    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(emotion_bp)
    app.register_blueprint(recommendation_bp)

    return app


app = create_app()
