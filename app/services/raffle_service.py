from app.models.raffle import Raffle, RaffleStatus
from app.models.ticket import Ticket
from app import db
import random
from datetime import datetime

class RaffleService:
    @staticmethod
    def create_raffle(name, description, start_time, end_time, ticket_price, number_of_tickets):
        new_raffle = Raffle(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            ticket_price=ticket_price,
            number_of_tickets=number_of_tickets
        )
        db.session.add(new_raffle)
        db.session.commit()
        new_raffle.generate_tickets()
        return new_raffle

    @staticmethod
    def get_raffle(raffle_id):
        raffle = Raffle.query.get(raffle_id)
        if raffle:
            raffle.update_status()
        return raffle

    @staticmethod
    def list_raffles():
        raffles = Raffle.query.all()
        for raffle in raffles:
            raffle.update_status()
        return raffles

    @staticmethod
    def select_winner(raffle_id):
        raffle = Raffle.query.get(raffle_id)
        if not raffle:
            return None, "Raffle not found"

        raffle.update_status()
        if raffle.status != RaffleStatus.ACTIVE and raffle.status != RaffleStatus.SOLD_OUT:
            return None, f"Cannot draw winner. Raffle status is {raffle.status}"

        sold_tickets = raffle.tickets.filter(Ticket.user_id.isnot(None)).all()
        if not sold_tickets:
            raffle.status = RaffleStatus.ENDED
            raffle.result = "No winner. No tickets were sold."
            db.session.commit()
            return None, raffle.result

        winning_ticket = random.choice(sold_tickets)
        raffle.status = RaffleStatus.ENDED
        raffle.result = f"Winner: User {winning_ticket.user_id}, Ticket {winning_ticket.ticket_serial_number}"
        db.session.commit()
        return winning_ticket, None

    @staticmethod
    def set_raffle_inactive(raffle_id):
        raffle = Raffle.query.get(raffle_id)
        if not raffle:
            return False, "Raffle not found"
        raffle.status = RaffleStatus.INACTIVE
        db.session.commit()
        return True, "Raffle set to inactive"