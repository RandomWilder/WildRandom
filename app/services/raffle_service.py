from app.models.raffle import Raffle, RaffleStatus, PrizeDistributionType
from app.models.ticket import Ticket
from app import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.utils.random_generator import generate_winning_ticket
from sqlalchemy import func

class RaffleService:
    @staticmethod
    def create_raffle(name, description, prize_description, terms_and_conditions, start_time, end_time, 
                      ticket_price, number_of_tickets, max_tickets_per_user, general_terms_link, 
                      number_of_draws, prize_value, prize_distribution_type):
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
                status=RaffleStatus.DRAFT,
                number_of_draws=number_of_draws,
                prize_value=prize_value,
                prize_distribution_type=prize_distribution_type
            )
            db.session.add(new_raffle)
            db.session.flush()  # This ensures the raffle gets an ID before we generate tickets

            # Generate tickets for the new raffle
            Ticket.generate_tickets(new_raffle.id, number_of_tickets)

            db.session.commit()
            return new_raffle, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_raffle(raffle_id, **kwargs):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            
            if raffle.status not in [RaffleStatus.DRAFT, RaffleStatus.COMING_SOON]:
                return None, "Cannot update raffle that is not in DRAFT or COMING_SOON status"

            for key, value in kwargs.items():
                if hasattr(raffle, key):
                    setattr(raffle, key, value)

            db.session.commit()
            return raffle, None
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
                return None, "Winners already selected"

            all_tickets = raffle.tickets.all()
            if not all_tickets:
                return None, "No tickets were generated for this raffle"

            winners = []
            for _ in range(raffle.number_of_draws):
                if not all_tickets:
                    break
                winning_ticket_number = generate_winning_ticket(len(all_tickets))
                winning_ticket = all_tickets.pop(winning_ticket_number - 1)
                
                if winning_ticket.user_id is None:
                    winners.append("No Winner")
                else:
                    winners.append(winning_ticket)

            result = []
            for winner in winners:
                if winner == "No Winner":
                    result.append("No Winner")
                else:
                    if raffle.prize_distribution_type == PrizeDistributionType.SPLIT:
                        prize_per_winner = raffle.prize_value / len([w for w in winners if w != "No Winner"])
                    else:
                        prize_per_winner = raffle.prize_value
                    result.append(f"Winner: User {winner.user_id}, Ticket {winner.ticket_id}, Prize: {prize_per_winner}")

            raffle.result = "; ".join(result)
            db.session.commit()
            return winners, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def set_raffle_status(raffle_id, new_status):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return False, "Raffle not found"
            
            if new_status not in RaffleStatus:
                return False, "Invalid status"

            if raffle.status in [RaffleStatus.ENDED, RaffleStatus.CANCELLED] and new_status != RaffleStatus.DRAFT:
                return False, f"Cannot change status of {raffle.status} raffle"

            raffle.status = new_status
            db.session.commit()
            return True, f"Raffle status set to {new_status.value}"
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
                    'raffle_status': raffle.status.value,
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
            if raffle.status not in [RaffleStatus.DRAFT, RaffleStatus.PAUSED]:
                return False, f"Cannot activate raffle. Current status: {raffle.status}"
            
            now = datetime.utcnow()
            if now < raffle.start_time:
                raffle.status = RaffleStatus.COMING_SOON
            else:
                raffle.status = RaffleStatus.ACTIVE
            
            db.session.commit()
            return True, f"Raffle set to {raffle.status.value}"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def set_raffle_paused(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return False, "Raffle not found"
            if raffle.status in [RaffleStatus.ENDED, RaffleStatus.CANCELLED]:
                return False, f"Cannot pause raffle. Current status: {raffle.status}"
            raffle.status = RaffleStatus.PAUSED
            db.session.commit()
            return True, "Raffle paused"
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

    @staticmethod
    def get_remaining_tickets(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            return raffle.tickets.filter_by(user_id=None).all(), None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_raffle_draw_history(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            if not raffle.result:
                return None, "No draw has been performed yet"
            return raffle.result.split("; "), None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_comprehensive_raffle_info(raffle_id=None):
        try:
            if raffle_id:
                raffles = [Raffle.query.get(raffle_id)]
                if not raffles[0]:
                    return None, "Raffle not found"
            else:
                raffles = Raffle.query.all()

            comprehensive_info = []

            for raffle in raffles:
                raffle.update_status()
                tickets = Ticket.query.filter_by(raffle_id=raffle.id).all()
                sold_tickets = len([t for t in tickets if t.user_id is not None])
                total_income = raffle.ticket_price * sold_tickets
                unique_participants = db.session.query(func.count(func.distinct(Ticket.user_id))).filter(Ticket.raffle_id == raffle.id, Ticket.user_id.isnot(None)).scalar()

                raffle_info = raffle.to_dict()
                raffle_info.update({
                    "unique_participants": unique_participants,
                    "total_sold_tickets": sold_tickets,
                    "total_income": round(total_income, 2),
                    "draw_results": raffle.get_formatted_result() or "No draw has been performed yet."
                })

                comprehensive_info.append(raffle_info)

            return comprehensive_info[0] if raffle_id else comprehensive_info, None
        except SQLAlchemyError as e:
            return None, str(e)