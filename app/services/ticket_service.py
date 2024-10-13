from app.models.ticket import Ticket
from app.models.raffle import Raffle, RaffleStatus
from app import db
from sqlalchemy.exc import SQLAlchemyError
import random
from datetime import datetime

class TicketService:
    @staticmethod
    def purchase_tickets(raffle_id, user_id, num_tickets):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            
            raffle.update_status()
            if raffle.status != RaffleStatus.ACTIVE:
                return None, f"Cannot purchase tickets. Raffle status is {raffle.status}"

            available_tickets = raffle.get_available_tickets()
            if len(available_tickets) < num_tickets:
                return None, f"Not enough tickets available. Only {len(available_tickets)} left."

            purchased_tickets = random.sample(available_tickets, num_tickets)

            for ticket in purchased_tickets:
                ticket.user_id = user_id
                ticket.purchase_time = datetime.utcnow()

            if len(raffle.get_available_tickets()) == 0:
                raffle.status = RaffleStatus.SOLD_OUT

            db.session.commit()
            return purchased_tickets, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_tickets_for_raffle(raffle_id):
        return Ticket.query.filter_by(raffle_id=raffle_id).all()