from flask import Blueprint, jsonify, request
from app.services.user_service import UserService
from app.validation import user_schema, credit_schema
from marshmallow import ValidationError

bp = Blueprint('user', __name__)

@bp.route('/register', methods=['POST'])
def register_user():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()

    try:
        validated_data = user_schema.load(data)
    except ValidationError as validation_errors:
        return jsonify({'error': validation_errors.messages}), 400

    user, error = UserService.create_user(**validated_data)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(user.to_dict()), 201

@bp.route('/login', methods=['POST'])
def login_user():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    user, error = UserService.authenticate_user(data['username'], data['password'])
    if error:
        return jsonify({'error': error}), 401
    return jsonify(user.to_dict()), 200

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user, error = UserService.get_user(user_id)
    if error:
        return jsonify({'error': error}), 404
    return jsonify(user.to_dict()), 200

@bp.route('/<int:user_id>/balance', methods=['POST'])
def add_balance(user_id):
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    if 'amount' not in data:
        return jsonify({'error': 'Missing amount'}), 400

    success, error = UserService.add_balance(user_id, float(data['amount']))
    if not success:
        return jsonify({'error': error}), 400
    return jsonify({'message': 'Balance added successfully'}), 200

@bp.route('/<int:user_id>/tickets', methods=['GET'])
def get_user_tickets(user_id):
    tickets, error = UserService.get_user_tickets(user_id)
    if error:
        return jsonify({'error': error}), 404
    return jsonify([ticket.to_dict() for ticket in tickets]), 200

@bp.route('/<int:user_id>/credit', methods=['POST'])
def credit_user(user_id):
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    
    try:
        validated_data = credit_schema.load(data)
    except ValidationError as validation_errors:
        return jsonify({'error': validation_errors.messages}), 400

    user, message = UserService.update_user_balance(user_id, validated_data['amount'])
    if user:
        return jsonify({'message': message, 'user': user.to_dict()}), 200
    else:
        return jsonify({'error': message}), 400

@bp.route('/all', methods=['GET'])
def get_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    users, total, error = UserService.get_all_users(page, per_page)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200