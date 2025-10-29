import os
from flask import Flask, jsonify
from flask_cors import CORS

from .firefly import FireflyConfigurationError, firefly_blueprint


def create_app() -> Flask:
    """Application factory for the Firefly III proxy service."""
    app = Flask(__name__, static_folder=os.path.join(app_root(), "frontend"), static_url_path="")
    app.config["JSON_AS_ASCII"] = False
    CORS(app)

    app.register_blueprint(firefly_blueprint, url_prefix="/api")

    @app.route("/")
    def index():
        return app.send_static_file("index.html")


    @app.errorhandler(FireflyConfigurationError)
    def handle_firefly_config_error(exc: FireflyConfigurationError):
        return (
            jsonify(
                {
                    "error": "configuration_error",
                    "message": str(exc),
                }
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception):
        app.logger.exception("Unhandled exception: %s", exc)
        return (
            jsonify(
                {
                    "error": "internal_error",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            ),
            500,
        )

    return app


def app_root() -> str:
    """Return the absolute path to the application root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
