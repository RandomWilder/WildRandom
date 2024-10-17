from app import db
from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum

class RaffleStatus(Enum):
    DRAFT = 'DRAFT'
    COMING_SOON = 'COMING_SOON'
    ACTIVE = 'ACTIVE'
    SOLD_OUT = 'SOLD_OUT'
    PAUSED = 'PAUSED'
    ENDED = 'ENDED'
    CANCELLED = 'CANCELLED'

class PrizeDistributionType(Enum):
    FULL = 'FULL'
    SPLIT = 'SPLIT'

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
    status = db.Column(SQLAlchemyEnum(RaffleStatus), default=RaffleStatus.DRAFT)
    result = db.Column(db.Text)
    general_terms_link = db.Column(db.String(255), nullable=False)
    number_of_draws = db.Column(db.Integer, nullable=False)
    prize_value = db.Column(db.Float, nullable=False)
    prize_distribution_type = db.Column(SQLAlchemyEnum(PrizeDistributionType), nullable=False)

    tickets = db.relationship('Ticket', back_populates='raffle', lazy='dynamic')

    def update_status(self):
        now = datetime.utcnow()
        if self.status in [RaffleStatus.ENDED, RaffleStatus.CANCELLED]:
            return
        elif self.status == RaffleStatus.DRAFT and now >= self.start_time:
            self.status = RaffleStatus.ACTIVE
        elif self.status == RaffleStatus.COMING_SOON and now >= self.start_time:
            self.status = RaffleStatus.ACTIVE
        elif self.status == RaffleStatus.ACTIVE:
            if now >= self.end_time:
                self.status = RaffleStatus.ENDED
            elif self.tickets.filter_by(user_id=None).count() == 0:
                self.status = RaffleStatus.SOLD_OUT
        elif self.status == RaffleStatus.SOLD_OUT and now >= self.end_time:
            self.status = RaffleStatus.ENDED
        db.session.commit()

    def to_dict(self):
        self.update_status()
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
            'status': self.status.value,
            'result': self.result,
            'general_terms_link': self.general_terms_link,
            'number_of_draws': self.number_of_draws,
            'prize_value': self.prize_value,
            'prize_distribution_type': self.prize_distribution_type.value,
            'available_tickets': self.tickets.filter_by(user_id=None).count()
        }
    
    def get_formatted_result(self):
        if not self.result:
            return None
        
        results = self.result.split("; ")
        formatted_results = []
        for result in results:
            if result == "No Winner":
                formatted_results.append({"outcome": "No Winner"})
            else:
                parts = result.split(", ")
                formatted_results.append({
                    "outcome": "Winner",
                    "user_id": int(parts[0].split(" ")[2]),
                    "ticket_id": parts[1].split(" ")[1],
                    "prize": float(parts[2].split(" ")[1])
                })
        return formatted_results