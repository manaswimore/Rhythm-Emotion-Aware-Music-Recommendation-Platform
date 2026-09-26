from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from db import initialize_database
from extensions import jwt

from routes.auth import auth_bp
from routes.health import health_bp
from routes.emotion import emotion_bp
from routes.recommendations import recommendation_bp


# ==========================================================
# APPLICATION FACTORY
# ==========================================================

def create_app():
    """
    Create and configure the RHYTHM Flask application.
    """

    app = Flask(__name__)

    # ======================================================
    # CONFIGURATION
    # ======================================================

    Config.validate()

    app.config.from_object(Config)

    # ======================================================
    # JWT CONFIGURATION
    # ======================================================

    jwt.init_app(app)

    # ======================================================
    # CORS CONFIGURATION
    # ======================================================

    allowed_origins = [
        origin.strip()
        for origin in Config.FRONTEND_URL.split(",")
        if origin.strip()
    ]

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins
            }
        }
    )

    # ======================================================
    # DATABASE
    # ======================================================

    initialize_database(app)

    # ======================================================
    # REGISTER API BLUEPRINTS
    # ======================================================

    app.register_blueprint(
        health_bp
    )

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        emotion_bp
    )

    app.register_blueprint(
        recommendation_bp
    )

    # ======================================================
    # ROOT ENDPOINT
    # ======================================================

    @app.get("/")
    def root():
        return jsonify({
            "name": "RHYTHM API",
            "message": "RHYTHM backend is running.",
            "status": "ok"
        }), 200

    # ======================================================
    # 404 ERROR HANDLER
    # ======================================================

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "API endpoint not found."
        }), 404

    # ======================================================
    # 500 ERROR HANDLER
    # ======================================================

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500

    return app


# ==========================================================
# CREATE FLASK APPLICATION
# ==========================================================

app = create_app()


# ==========================================================
# LOCAL DEVELOPMENT SERVER
# ==========================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )