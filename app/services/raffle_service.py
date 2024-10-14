from app.models.raffle import Raffle, RaffleStatus
from app.models.ticket import Ticket
from app import db
from app.utils.random_generator import generate_winning_ticket
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class RaffleService:
    @staticmethod
    def create_raffle(name, description, prize_description, terms_and_conditions, start_time, end_time, ticket_price, number_of_tickets, max_tickets_per_user, general_terms_link):
        try:
            if end_time <= start_time:
                return None, "End time must be after start time"

            new_raffle = Raffle(
                name=name,
                description=description,
                prize_description=prize_description,
                terms_and_conditions=terms_and_conditions,
                start_time=start_time,
                end_time=end_time,
                ticket_price=ticket_price,
                number_of_tickets=number_of_tickets,
                max_tickets_per_user=max_tickets_per_user,
                general_terms_link=general_terms_link,
                status=RaffleStatus.DRAFT
            )
            db.session.add(new_raffle)
            db.session.commit()
            new_raffle.generate_tickets()
            return new_raffle, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_raffle(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if raffle:
                raffle.update_status()
            return raffle, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def list_raffles():
        try:
            raffles = Raffle.query.all()
            for raffle in raffles:
                raffle.update_status()
            return raffles, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def select_winner(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"

            raffle.update_status()
            if raffle.status != RaffleStatus.ENDED:
                return None, f"Cannot select winner. Raffle status is {raffle.status}"

            if raffle.result:
                return None, "Winner already selected"

            sold_tickets = raffle.tickets.filter(Ticket.user_id.isnot(None)).all()
            if not sold_tickets:
                raffle.result = "No winner. No tickets were sold."
                db.session.commit()
                return None, raffle.result

            winning_ticket_number = generate_winning_ticket(len(sold_tickets))
            winning_ticket = sold_tickets[winning_ticket_number - 1]
            raffle.result = f"Winner: User {winning_ticket.user_id}, Ticket {winning_ticket.ticket_id}"
            db.session.commit()
            return winning_ticket, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def set_raffle_inactive(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return False, "Raffle not found"
            if raffle.status in [RaffleStatus.ENDED, RaffleStatus.CANCELLED]:
                return False, f"Cannot set raffle to inactive. Current status: {raffle.status}"
            raffle.status = RaffleStatus.INACTIVE
            db.session.commit()
            return True, "Raffle set to inactive"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def get_user_raffle_history(user_id):
        try:
            user_tickets = Ticket.query.filter_by(user_id=user_id).all()
            raffle_history = []
            for ticket in user_tickets:
                raffle = ticket.raffle
                raffle_history.append({
                    'raffle_id': raffle.id,
                    'raffle_name': raffle.name,
                    'ticket_id': ticket.ticket_id,
                    'ticket_number': ticket.ticket_number,
                    'purchase_time': ticket.purchase_time.isoformat() if ticket.purchase_time else None,
                    'raffle_status': raffle.status,
                    'won': raffle.result and f"User {user_id}" in raffle.result
                })
            return raffle_history, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def activate_raffle(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return False, "Raffle not found"
            if raffle.status != RaffleStatus.INACTIVE:
                return False, f"Cannot activate raffle. Current status: {raffle.status}"
            
            now = datetime.utcnow()
            if now < raffle.start_time:
                raffle.status = RaffleStatus.COMING_SOON
            else:
                raffle.status = RaffleStatus.ACTIVE
            
            db.session.commit()
            return True, f"Raffle set to {raffle.status}"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def cancel_raffle(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return False, "Raffle not found"
            if raffle.status in [RaffleStatus.ENDED, RaffleStatus.CANCELLED]:
                return False, f"Cannot cancel raffle. Current status: {raffle.status}"
            raffle.status = RaffleStatus.CANCELLED
            db.session.commit()
            return True, "Raffle cancelled"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)