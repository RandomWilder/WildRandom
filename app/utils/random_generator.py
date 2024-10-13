import secrets

def generate_winning_ticket(max_ticket_number):
    return secrets.randbelow(max_ticket_number) + 1