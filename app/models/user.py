from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Float, default=0.0)

    tickets = db.relationship('Ticket', back_populates='user')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_balance(self, amount):
        self.balance += amount
        db.session.commit()

    def subtract_balance(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            db.session.commit()
            return True
        return False

    def update_balance(self, amount):
        new_balance = self.balance + amount
        if new_balance < 0:
            return False, "Insufficient funds"
        self.balance = new_balance
        db.session.commit()
        return True, f"Balance updated. New balance: {self.balance}"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'balance': self.balance
        }