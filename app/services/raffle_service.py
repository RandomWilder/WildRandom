import json
from flask import current_app
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

            if raffle.status != RaffleStatus.ENDED:
                return None, f"Cannot select winner. Raffle status is {raffle.status}"

            if raffle.result:
                return None, "Winners already selected"

            all_tickets = raffle.tickets.all()
            if not all_tickets:
                return None, "No tickets were generated for this raffle"

            winners = []
            draw_time = datetime.utcnow()
            for _ in range(raffle.number_of_draws):
                if not all_tickets:
                    break
                winning_ticket_number = generate_winning_ticket(len(all_tickets))
                winning_ticket = all_tickets.pop(winning_ticket_number - 1)
                
                if raffle.prize_distribution_type == PrizeDistributionType.SPLIT:
                    prize_value = raffle.prize_value / raffle.number_of_draws
                else:
                    prize_value = raffle.prize_value

                winner_info = {
                    "raffle_id": raffle.id,
                    "ticket_number": winning_ticket.ticket_number,
                    "prize_description": raffle.prize_description,
                    "prize_value": prize_value,
                    "outcome": "Winner" if winning_ticket.user_id else "No Winner",
                    "user_id": winning_ticket.user_id if winning_ticket.user_id else "No Winner",
                    "draw_time": draw_time.isoformat()
                }
                winners.append(winner_info)

            raffle.result = json.dumps(winners)
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
                win_status = "The draw hasn't taken place yet"
                prize_value = "Pending number of winners" if raffle.prize_distribution_type == PrizeDistributionType.SPLIT else raffle.prize_value

                if raffle.status == RaffleStatus.ENDED:
                    if raffle.result:
                        try:
                            results = json.loads(raffle.result)
                            winning_ticket = next((r for r in results if r['user_id'] == user_id), None)
                            if winning_ticket:
                                win_status = "You Win!"
                                prize_value = winning_ticket['prize_value']
                            else:
                                win_status = "No win"
                        except json.JSONDecodeError:
                            # If raffle.result is not a valid JSON, treat it as if no draw has taken place
                            win_status = "Error in draw results"
                    else:
                        win_status = "Draw completed, but no results available"

                raffle_history.append({
                    'purchase_time': ticket.purchase_time.isoformat() if ticket.purchase_time else None,
                    'raffle_name': raffle.name,
                    'prize_description': raffle.prize_description,
                    'prize_value': prize_value,
                    'ticket_number': ticket.ticket_number,
                    'win': win_status
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
            return json.loads(raffle.result), None
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
                    "draw_results": json.loads(raffle.result) if raffle.result else "No draw has been performed yet."
                })

                comprehensive_info.append(raffle_info)

            return comprehensive_info[0] if raffle_id else comprehensive_info, None
        except SQLAlchemyError as e:
            return None, str(e)
        
    @staticmethod
    def end_raffle(raffle_id):
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return False, "Raffle not found"
            
            if raffle.status not in [RaffleStatus.ACTIVE, RaffleStatus.SOLD_OUT, RaffleStatus.COMING_SOON]:
                return False, f"Cannot end raffle. Current status: {raffle.status}"
            
            raffle.status = RaffleStatus.ENDED
            raffle.end_time = datetime.utcnow()  # Update end time to now
            db.session.commit()
            return True, "Raffle ended successfully"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)