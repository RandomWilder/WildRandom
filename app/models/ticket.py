from app import db
from datetime import datetime

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffle.id'), nullable=False)
    ticket_number = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    purchase_time = db.Column(db.DateTime, nullable=True)

    raffle = db.relationship('Raffle', back_populates='tickets')

    @property
    def ticket_id(self):
        if self.raffle_id is None or self.ticket_number is None:
            return None
        return int(f"{self.raffle_id}{self.ticket_number:03d}")