from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from db import initialize_database
from extensions import jwt

from routes.auth import auth_bp
from routes.health import health_bp
from routes.emotion import emotion_bp
from routes.recommendations import recommendation_bp


def create_app():
    app = Flask(__name__)

    Config.validate()
    app.config.from_object(Config)

    jwt.init_app(app)

    # Allow the deployed Vercel frontend.
    allowed_origins = [
        "https://rhythm-emotion-aware-music-recommendation-platform-122kh4rk8.vercel.app",
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
            }
        },
    )

    initialize_database(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(emotion_bp)
    app.register_blueprint(recommendation_bp)

    @app.get("/")
    def root():
        return jsonify({
            "name": "RHYTHM API",
            "message": "RHYTHM backend is running.",
            "status": "ok",
        }), 200

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "API endpoint not found.",
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "message": "Internal server error.",
        }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
