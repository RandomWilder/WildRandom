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
                return None, f"Cannot purchase tickets. Raffle status is {raffle.status.value}"

            available_tickets = raffle.tickets.filter_by(user_id=None).all()
            if len(available_tickets) < num_tickets:
                return None, f"Not enough tickets available. Only {len(available_tickets)} left."

            user_tickets = Ticket.query.filter_by(raffle_id=raffle_id, user_id=user_id).count()
            if user_tickets + num_tickets > raffle.max_tickets_per_user:
                return None, f"Cannot purchase more than {raffle.max_tickets_per_user} tickets per user."

            purchased_tickets = random.sample(available_tickets, num_tickets)

            for ticket in purchased_tickets:
                ticket.user_id = user_id
                ticket.purchase_time = datetime.utcnow()

            if len(raffle.tickets.filter_by(user_id=None).all()) == 0:
                raffle.status = RaffleStatus.SOLD_OUT

            db.session.commit()
            return purchased_tickets, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_tickets_for_raffle(raffle_id):
        try:
            return Ticket.query.filter_by(raffle_id=raffle_id).all(), None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_user_tickets(user_id, raffle_id=None):
        try:
            query = Ticket.query.filter_by(user_id=user_id)
            if raffle_id:
                query = query.filter_by(raffle_id=raffle_id)
            return query.all(), None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_ticket_by_id(ticket_id):
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return None, "Ticket not found"
            return ticket, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def refund_ticket(ticket_id):
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return False, "Ticket not found"

            raffle = ticket.raffle
            if raffle.status not in [RaffleStatus.ACTIVE, RaffleStatus.PAUSED, RaffleStatus.SOLD_OUT]:
                return False, f"Cannot refund ticket. Raffle status is {raffle.status.value}"

            ticket.user_id = None
            ticket.purchase_time = None

            if raffle.status == RaffleStatus.SOLD_OUT:
                raffle.status = RaffleStatus.ACTIVE

            db.session.commit()
            return True, "Ticket refunded successfully"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def get_purchased_tickets_for_raffle(raffle_id, page=1, per_page=50):
        try:
            tickets = Ticket.query.filter_by(raffle_id=raffle_id).filter(Ticket.user_id.isnot(None)).paginate(page=page, per_page=per_page, error_out=False)
            return tickets.items, tickets.total, None
        except SQLAlchemyError as e:
            return None, 0, str(e)