from flask import Blueprint, jsonify, request
from app.services.raffle_service import RaffleService
from app.services.ticket_service import TicketService
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('raffle', __name__, url_prefix='/api/raffle')

@bp.route('/', methods=['POST'])
def create_raffle():
    data = request.json
    try:
        raffle = RaffleService.create_raffle(
            name=data['name'],
            description=data['description'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            ticket_price=data['ticket_price'],
            number_of_tickets=data['number_of_tickets']
        )
        return jsonify({
            'id': raffle.id, 
            'name': raffle.name, 
            'status': raffle.status,
            'created_at': raffle.created_at.isoformat(),
            'start_time': raffle.start_time.isoformat()
        }), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error occurred: {str(e)}'}), 500

@bp.route('/<int:raffle_id>', methods=['GET'])
def get_raffle(raffle_id):
    try:
        raffle = RaffleService.get_raffle(raffle_id)
        if raffle:
            return jsonify({
                'id': raffle.id,
                'name': raffle.name,
                'description': raffle.description,
                'created_at': raffle.created_at.isoformat(),
                'start_time': raffle.start_time.isoformat(),
                'end_time': raffle.end_time.isoformat(),
                'ticket_price': raffle.ticket_price,
                'number_of_tickets': raffle.number_of_tickets,
                'available_tickets': len(raffle.get_available_tickets()),
                'status': raffle.status,
                'result': raffle.result
            })
        return jsonify({'error': 'Raffle not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error occurred: {str(e)}'}), 500

@bp.route('/', methods=['GET'])
def list_raffles():
    try:
        raffles = RaffleService.list_raffles()
        return jsonify([{
            'id': raffle.id,
            'name': raffle.name,
            'created_at': raffle.created_at.isoformat(),
            'start_time': raffle.start_time.isoformat(),
            'end_time': raffle.end_time.isoformat(),
            'available_tickets': len(raffle.get_available_tickets()),
            'status': raffle.status
        } for raffle in raffles])
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error occurred: {str(e)}'}), 500

@bp.route('/<int:raffle_id>/purchase', methods=['POST'])
def purchase_tickets(raffle_id):
    data = request.json
    user_id = data.get('user_id')
    num_tickets = data.get('num_tickets', 1)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    tickets, error = TicketService.purchase_tickets(raffle_id, user_id, num_tickets)
    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'purchased_tickets': [
            {
                'ticket_id': ticket.ticket_id_number,
                'ticket_serial_number': ticket.ticket_serial_number,
                'raffle_id': ticket.raffle_id,
                'user_id': ticket.user_id
            } for ticket in tickets
        ]
    }), 201

@bp.route('/<int:raffle_id>/draw', methods=['POST'])
def draw_winner(raffle_id):
    winning_ticket, message = RaffleService.select_winner(raffle_id)
    if winning_ticket:
        return jsonify({
            'result': 'We have a winner!',
            'winning_ticket_serial_number': winning_ticket.ticket_serial_number,
            'winning_user_id': winning_ticket.user_id,
            'raffle_status': 'ended'
        }), 200
    else:
        return jsonify({
            'result': 'No winner',
            'message': message,
            'raffle_status': 'ended'
        }), 200

@bp.route('/<int:raffle_id>/set_inactive', methods=['POST'])
def set_raffle_inactive(raffle_id):
    success, message = RaffleService.set_raffle_inactive(raffle_id)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 404