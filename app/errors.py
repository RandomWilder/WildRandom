from flask import Blueprint, jsonify

bp = Blueprint('errors', __name__)

@bp.app_errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

@bp.app_errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error'}), 500