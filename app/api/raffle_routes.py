from flask import Blueprint, jsonify, request, current_app
from app.services.raffle_service import RaffleService
from app.services.ticket_service import TicketService
from datetime import datetime
import traceback
from app.validation import raffle_schema
from marshmallow import ValidationError

bp = Blueprint('raffle', __name__)

@bp.route('', methods=['POST'])
@bp.route('/', methods=['POST'])
def create_raffle():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()

    try:
        validated_data = raffle_schema.load(data)
    except ValidationError as validation_errors:
        return jsonify({'error': validation_errors.messages}), 400

    try:
        raffle, error = RaffleService.create_raffle(**validated_data)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(raffle.to_dict()), 201
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@bp.route('/<int:raffle_id>', methods=['PUT'])
def update_raffle(raffle_id):
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()

    try:
        validated_data = raffle_schema.load(data, partial=True)
    except ValidationError as validation_errors:
        return jsonify({'error': validation_errors.messages}), 400

    try:
        raffle, error = RaffleService.update_raffle(raffle_id, **validated_data)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(raffle.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def list_raffles():
    raffles, error = RaffleService.list_raffles()
    if error:
        return jsonify({'error': error}), 400
    return jsonify([raffle.to_dict() for raffle in raffles]), 200

@bp.route('/<int:raffle_id>', methods=['GET'])
def get_raffle(raffle_id):
    raffle, error = RaffleService.get_raffle(raffle_id)
    if error:
        return jsonify({'error': error}), 400
    if not raffle:
        return jsonify({'error': 'Raffle not found'}), 404
    return jsonify(raffle.to_dict()), 200

@bp.route('/<int:raffle_id>/purchase', methods=['POST'])
def purchase_tickets(raffle_id):
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    if 'user_id' not in data or 'num_tickets' not in data:
        return jsonify({'error': 'Missing user_id or num_tickets'}), 400

    try:
        tickets, error = TicketService.purchase_tickets(
            raffle_id=raffle_id,
            user_id=int(data['user_id']),
            num_tickets=int(data['num_tickets'])
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify([ticket.to_dict() for ticket in tickets]), 201
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400

@bp.route('/<int:raffle_id>/draw', methods=['POST'])
def draw_winner(raffle_id):
    winners, error = RaffleService.select_winner(raffle_id)
    if error:
        return jsonify({'error': error}), 400
    
    result = []
    for winner in winners:
        if winner == "No Winner":
            result.append({"outcome": "No Winner"})
        else:
            result.append({
                "outcome": "Winner",
                "user_id": winner.user_id,
                "ticket_id": winner.ticket_id
            })
    
    return jsonify({'draw_results': result}), 200

@bp.route('/<int:raffle_id>/activate', methods=['POST'])
def activate_raffle(raffle_id):
    success, message = RaffleService.activate_raffle(raffle_id)
    if not success:
        return jsonify({'error': message}), 400
    return jsonify({'message': message}), 200

@bp.route('/<int:raffle_id>/status', methods=['PUT'])
def update_raffle_status(raffle_id):
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    if 'status' not in data:
        return jsonify({'error': 'Missing status'}), 400

    success, message = RaffleService.set_raffle_status(raffle_id, data['status'])
    if not success:
        return jsonify({'error': message}), 400
    return jsonify({'message': message}), 200

@bp.route('/<int:raffle_id>/pause', methods=['POST'])
def pause_raffle(raffle_id):
    success, message = RaffleService.set_raffle_paused(raffle_id)
    if not success:
        return jsonify({'error': message}), 400
    return jsonify({'message': message}), 200

@bp.route('/<int:raffle_id>/cancel', methods=['POST'])
def cancel_raffle(raffle_id):
    success, message = RaffleService.cancel_raffle(raffle_id)
    if not success:
        return jsonify({'error': message}), 400
    return jsonify({'message': message}), 200

@bp.route('/user/<int:user_id>/history', methods=['GET'])
def get_user_history(user_id):
    history, error = RaffleService.get_user_raffle_history(user_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(history), 200

@bp.route('/<int:raffle_id>/remaining_tickets', methods=['GET'])
def get_remaining_tickets(raffle_id):
    tickets, error = RaffleService.get_remaining_tickets(raffle_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'remaining_tickets': len(tickets)}), 200

@bp.route('/<int:raffle_id>/comprehensive_info', methods=['GET'])
def get_comprehensive_raffle_info(raffle_id):
    info, error = RaffleService.get_comprehensive_raffle_info(raffle_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(info), 200

@bp.route('/ticket/<int:ticket_id>/refund', methods=['POST'])
def refund_ticket(ticket_id):
    success, message = TicketService.refund_ticket(ticket_id)
    if not success:
        return jsonify({'error': message}), 400
    return jsonify({'message': message}), 200

@bp.route('/<int:raffle_id>/purchased_tickets', methods=['GET'])
def get_purchased_tickets(raffle_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    tickets, total, error = TicketService.get_purchased_tickets_for_raffle(raffle_id, page, per_page)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({
        'tickets': [ticket.to_dict() for ticket in tickets],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200