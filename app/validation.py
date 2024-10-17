from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime, timedelta
from flask import current_app

class RaffleSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    prize_description = fields.Str(required=True)
    terms_and_conditions = fields.Str(required=True)
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    ticket_price = fields.Float(required=True)
    number_of_tickets = fields.Int(required=True)
    max_tickets_per_user = fields.Int(required=True)
    general_terms_link = fields.Url(required=True)
    number_of_draws = fields.Int(required=True, validate=validate.Range(min=1))
    prize_value = fields.Float(required=True, validate=validate.Range(min=0))
    prize_distribution_type = fields.Str(required=True, validate=validate.OneOf(['FULL', 'SPLIT']))

    @validates_schema
    def validate_raffle(self, data, **kwargs):
        if data['start_time'] >= data['end_time']:
            raise ValidationError('End time must be after start time')

        now = datetime.utcnow()
        if data['start_time'] < now:
            raise ValidationError('Start time must be in the future')

        duration = data['end_time'] - data['start_time']
        if duration < timedelta(seconds=current_app.config['RAFFLE_MIN_DURATION']):
            raise ValidationError(f'Raffle duration must be at least {current_app.config["RAFFLE_MIN_DURATION"]} seconds')
        if duration > timedelta(seconds=current_app.config['RAFFLE_MAX_DURATION']):
            raise ValidationError(f'Raffle duration must not exceed {current_app.config["RAFFLE_MAX_DURATION"]} seconds')

        if data['number_of_tickets'] < current_app.config['RAFFLE_MIN_TICKETS']:
            raise ValidationError(f'Number of tickets must be at least {current_app.config["RAFFLE_MIN_TICKETS"]}')
        if data['number_of_tickets'] > current_app.config['RAFFLE_MAX_TICKETS']:
            raise ValidationError(f'Number of tickets must not exceed {current_app.config["RAFFLE_MAX_TICKETS"]}')

        if data['ticket_price'] < current_app.config['RAFFLE_MIN_TICKET_PRICE']:
            raise ValidationError(f'Ticket price must be at least {current_app.config["RAFFLE_MIN_TICKET_PRICE"]}')
        if data['ticket_price'] > current_app.config['RAFFLE_MAX_TICKET_PRICE']:
            raise ValidationError(f'Ticket price must not exceed {current_app.config["RAFFLE_MAX_TICKET_PRICE"]}')

        if data['max_tickets_per_user'] > data['number_of_tickets']:
            raise ValidationError('Max tickets per user cannot exceed total number of tickets')

        if data['number_of_draws'] > data['number_of_tickets']:
            raise ValidationError('Number of draws cannot exceed total number of tickets')

class UserSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=64))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))

class CreditSchema(Schema):
    amount = fields.Float(required=True)

raffle_schema = RaffleSchema()
user_schema = UserSchema()
credit_schema = CreditSchema()