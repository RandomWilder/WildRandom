from app.models.user import User
from app import db
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

class UserService:
    @staticmethod
    def create_user(username, email, password):
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            return user, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def authenticate_user(username, password):
        try:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                return user, None
            return None, "Invalid username or password"
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def update_user(user_id, **kwargs):
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.session.commit()
            return user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def add_balance(user_id, amount):
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            user.add_balance(amount)
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def subtract_balance(user_id, amount):
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            if user.subtract_balance(amount):
                return True, None
            else:
                return False, "Insufficient balance"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def get_user_tickets(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            tickets = user.tickets
            return tickets, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def update_user_balance(user_id, amount):
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            success, message = user.update_balance(amount)
            if success:
                return user, message
            else:
                return None, message
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_all_users(page=1, per_page=20):
        try:
            users = User.query.paginate(page=page, per_page=per_page, error_out=False)
            return users.items, users.total, None
        except SQLAlchemyError as e:
            return None, 0, str(e)        
