from marshmallow import Schema, fields, validate

class RaffleSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    prize_description = fields.Str(required=True)
    terms_and_conditions = fields.Str(required=True)
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    ticket_price = fields.Float(required=True, validate=validate.Range(min=0))
    number_of_tickets = fields.Int(required=True, validate=validate.Range(min=1))
    max_tickets_per_user = fields.Int(required=True, validate=validate.Range(min=1))
    general_terms_link = fields.Url(required=True)

raffle_schema = RaffleSchema()