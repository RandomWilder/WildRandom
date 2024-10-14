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
    prize_description = db.Column(db.Text, nullable=False)
    terms_and_conditions = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    ticket_price = db.Column(db.Float, nullable=False)
    number_of_tickets = db.Column(db.Integer, nullable=False)
    max_tickets_per_user = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default=RaffleStatus.COMING_SOON)
    result = db.Column(db.Text)
    general_terms_link = db.Column(db.String(255), nullable=False)

    tickets = db.relationship('Ticket', back_populates='raffle', lazy='dynamic')

    def generate_tickets(self):
        for serial_number in range(1, self.number_of_tickets + 1):
            ticket = Ticket(raffle_id=self.id, ticket_number=serial_number)
            db.session.add(ticket)
        db.session.commit()

    def get_available_tickets(self):
        return self.tickets.filter_by(user_id=None).all()

    def get_available_ticket_count(self):
        return self.tickets.filter_by(user_id=None).count()

    def update_status(self):
        now = datetime.utcnow()
        if self.status == RaffleStatus.INACTIVE:
            return
        elif now < self.start_time:
            self.status = RaffleStatus.COMING_SOON
        elif self.start_time <= now < self.end_time:
            if self.get_available_ticket_count() == 0:
                self.status = RaffleStatus.SOLD_OUT
            else:
                self.status = RaffleStatus.ACTIVE
        else:
            self.status = RaffleStatus.ENDED
        db.session.commit()

    def to_dict(self):
        self.update_status()  # Ensure status is up-to-date
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'prize_description': self.prize_description,
            'terms_and_conditions': self.terms_and_conditions,
            'created_at': self.created_at.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'ticket_price': self.ticket_price,
            'number_of_tickets': self.number_of_tickets,
            'max_tickets_per_user': self.max_tickets_per_user,
            'available_tickets': self.get_available_ticket_count(),
            'status': self.status,
            'general_terms_link': self.general_terms_link
        }