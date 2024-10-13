from app import db
from datetime import datetime
from .ticket import Ticket

class RaffleStatus:
    COMING_SOON = 'coming_soon'
    ACTIVE = 'active'
    SOLD_OUT = 'sold_out'
    ENDED = 'ended'
    INACTIVE = 'inactive'

class Raffle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    ticket_price = db.Column(db.Float, nullable=False)
    number_of_tickets = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default=RaffleStatus.COMING_SOON)
    result = db.Column(db.Text)

    tickets = db.relationship('Ticket', back_populates='raffle', lazy='dynamic')

    def generate_tickets(self):
        for serial_number in range(1, self.number_of_tickets + 1):
            ticket = Ticket(raffle_id=self.id, ticket_serial_number=serial_number)
            db.session.add(ticket)
        db.session.commit()

    def get_available_tickets(self):
        return self.tickets.filter_by(user_id=None).all()

    def update_status(self):
        now = datetime.utcnow()
        if self.status == RaffleStatus.INACTIVE:
            return
        elif now < self.start_time:
            self.status = RaffleStatus.COMING_SOON
        elif self.start_time <= now < self.end_time:
            if not self.get_available_tickets():
                self.status = RaffleStatus.SOLD_OUT
            else:
                self.status = RaffleStatus.ACTIVE
        else:
            self.status = RaffleStatus.ENDED
        db.session.commit()