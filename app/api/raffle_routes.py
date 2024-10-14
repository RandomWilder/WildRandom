from flask import Blueprint, jsonify, request, current_app
from app.services.raffle_service import RaffleService
from app.services.ticket_service import TicketService
from datetime import datetime

bp = Blueprint('raffle', __name__)

@bp.route('', methods=['POST'])
@bp.route('/', methods=['POST'])
def create_raffle():
    current_app.logger.debug(f"Received data: {request.data}")
    current_app.logger.debug(f"Content-Type: {request.headers.get('Content-Type')}")
    
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    current_app.logger.debug(f"Parsed JSON data: {data}")

    required_fields = ['name', 'description', 'prize_description', 'terms_and_conditions', 
                       'start_time', 'end_time', 'ticket_price', 'number_of_tickets', 
                       'max_tickets_per_user', 'general_terms_link']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        raffle, error = RaffleService.create_raffle(
            name=data['name'],
            description=data['description'],
            prize_description=data['prize_description'],
            terms_and_conditions=data['terms_and_conditions'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            ticket_price=float(data['ticket_price']),
            number_of_tickets=int(data['number_of_tickets']),
            max_tickets_per_user=int(data['max_tickets_per_user']),
            general_terms_link=data['general_terms_link']
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(raffle.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def list_raffles():
    raffles, error = RaffleService.list_raffles()
    if error:
        return jsonify({'error': error}), 500
    return jsonify([raffle.to_dict() for raffle in raffles])

@bp.route('/<int:raffle_id>', methods=['GET'])
def get_raffle(raffle_id):
    raffle, error = RaffleService.get_raffle(raffle_id)
    if error:
        return jsonify({'error': error}), 404
    if raffle is None:
        return jsonify({'error': 'Raffle not found'}), 404
    return jsonify(raffle.to_dict())

@bp.route('/<int:raffle_id>/purchase', methods=['POST'])
def purchase_tickets(raffle_id):
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    user_id = data.get('user_id')
    num_tickets = data.get('num_tickets', 1)

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        num_tickets = int(num_tickets)
    except ValueError:
        return jsonify({'error': 'Invalid number of tickets'}), 400

    tickets, error = TicketService.purchase_tickets(raffle_id, user_id, num_tickets)
    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'purchased_tickets': [
            {
                'ticket_id': ticket.ticket_id,
                'ticket_number': ticket.ticket_number,
                'raffle_id': ticket.raffle_id,
                'user_id': ticket.user_id
            } for ticket in tickets
        ]
    }), 201

@bp.route('/<int:raffle_id>/draw', methods=['POST'])
def draw_winner(raffle_id):
    winning_ticket, error = RaffleService.select_winner(raffle_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({
        'result': 'Winner selected',
        'winning_ticket_id': winning_ticket.ticket_id,
        'winning_ticket_number': winning_ticket.ticket_number,
        'winning_user_id': winning_ticket.user_id
    }), 200

@bp.route('/<int:raffle_id>/set_inactive', methods=['POST'])
def set_raffle_inactive(raffle_id):
    success, message = RaffleService.set_raffle_inactive(raffle_id)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 404

@bp.route('/user/<int:user_id>/history', methods=['GET'])
def get_user_raffle_history(user_id):
    history, error = RaffleService.get_user_raffle_history(user_id)
    if error:
        return jsonify({'error': error}), 500
    return jsonify(history)

@bp.route('/<int:raffle_id>/activate', methods=['POST'])
def activate_raffle(raffle_id):
    success, message = RaffleService.activate_raffle(raffle_id)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400