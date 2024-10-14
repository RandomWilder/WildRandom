from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models.raffle import Raffle
from app.models.ticket import Ticket

app = create_app()
migrate = Migrate(app, db)

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created.")

def db_migrate():
    with app.app_context():
        # Run migrations
        upgrade()
        print("Database migrations applied.")

if __name__ == "__main__":
    init_db()
    db_migrate()