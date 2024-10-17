from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import logging
import sys
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
celery = Celery(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize Celery
    celery.conf.update(app.config)

    # Configure logging
    if not app.debug and not app.testing:
        # Use StreamHandler instead of RotatingFileHandler to avoid permission issues
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Wild Random startup')

    # Register blueprints
    from app.api.raffle_routes import bp as raffle_bp
    app.register_blueprint(raffle_bp, url_prefix='/api/raffle')

    from app.api.user_routes import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')

    # Register error handlers
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    @app.route('/')
    def index():
        return "Welcome to Wild Random Platform"

    return app

# Import models at the end to avoid circular imports
from app.models import raffle, ticket, user