from app import create_app, db
from app.models.raffle import Raffle
from app.models.ticket import Ticket
from datetime import datetime, timedelta

def reset_database():
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create some sample data
        sample_raffle = Raffle(
            name="Test Raffle",
            description="This is a test raffle",
            prize_description="A fantastic prize",
            terms_and_conditions="Standard terms apply",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            ticket_price=10.0,
            number_of_tickets=100,
            max_tickets_per_user=5,
            general_terms_link="https://example.com/terms"
        )
        db.session.add(sample_raffle)
        db.session.commit()
        
        sample_raffle.generate_tickets()
        
        print("Database reset complete. Sample raffle created.")

if __name__ == "__main__":
    reset_database()