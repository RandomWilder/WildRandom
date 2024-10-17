from app import db
from datetime import datetime

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffle.id'), nullable=False)
    ticket_number = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    purchase_time = db.Column(db.DateTime, nullable=True)

    raffle = db.relationship('Raffle', back_populates='tickets')
    user = db.relationship('User', back_populates='tickets')

    @property
    def ticket_id(self):
        return f"{self.raffle_id}-{self.ticket_number:04d}"

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'raffle_id': self.raffle_id,
            'ticket_number': self.ticket_number,
            'user_id': self.user_id,
            'purchase_time': self.purchase_time.isoformat() if self.purchase_time else None
        }

    @staticmethod
    def generate_tickets(raffle_id, number_of_tickets):
        tickets = []
        for i in range(1, number_of_tickets + 1):
            ticket = Ticket(raffle_id=raffle_id, ticket_number=i)
            tickets.append(ticket)
        db.session.bulk_save_objects(tickets)
        db.session.commit()