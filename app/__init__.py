from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.api.raffle_routes import bp as raffle_bp
    app.register_blueprint(raffle_bp, url_prefix='/api/raffle')

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

    @app.route('/')
    def index():
        return "Welcome to the Raffle API"

    return app