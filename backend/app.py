from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from db import initialize_database

from routes.auth import auth_bp
from routes.health import health_bp
from routes.emotion import emotion_bp
from routes.recommendations import recommendation_bp


ALLOWED_ORIGINS = [
    "https://rhythm-emotion-aware-music-recommendation-platform.vercel.app",
    "http://localhost:5173",
]


def create_app():
    Config.validate()

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES

    JWTManager(app)

    initialize_database(app)

    CORS(
        app,
        resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        supports_credentials=False,
        automatic_options=True,
        vary_header=True,
    )

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
