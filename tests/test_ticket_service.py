import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.raffle import Raffle, RaffleStatus, PrizeDistributionType
from app.models.ticket import Ticket
from app.services.ticket_service import TicketService
from app.services.raffle_service import RaffleService

class TestTicketService(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test raffle
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(days=7)
        self.raffle, _ = RaffleService.create_raffle(
            name="Test Raffle",
            description="A test raffle",
            prize_description="A great prize",
            terms_and_conditions="Standard terms apply",
            start_time=start_time,
            end_time=end_time,
            ticket_price=10.0,
            number_of_tickets=100,
            max_tickets_per_user=5,
            general_terms_link="https://example.com/terms",
            number_of_draws=1,
            prize_value=1000.0,
            prize_distribution_type=PrizeDistributionType.FULL
        )
        RaffleService.activate_raffle(self.raffle.id)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_purchase_tickets(self):
        # Test purchasing tickets for an active raffle
        tickets, error = TicketService.purchase_tickets(self.raffle.id, 1, 3)
        self.assertIsNone(error)
        self.assertEqual(len(tickets), 3)
        self.assertEqual(tickets[0].user_id, 1)

        # Test purchasing more tickets than allowed per user
        tickets, error = TicketService.purchase_tickets(self.raffle.id, 1, 3)
        self.assertIsNotNone(error)
        self.assertIn("Cannot purchase more than 5 tickets per user", error)

        # Test purchasing tickets for a non-existent raffle
        tickets, error = TicketService.purchase_tickets(9999, 1, 1)
        self.assertIsNone(tickets)
        self.assertIn("Raffle not found", error)

    def test_get_tickets_for_raffle(self):
        TicketService.purchase_tickets(self.raffle.id, 1, 3)
        tickets = TicketService.get_tickets_for_raffle(self.raffle.id)
        self.assertEqual(len(tickets), 100)  # Total tickets in raffle
        purchased_tickets = [t for t in tickets if t.user_id is not None]
        self.assertEqual(len(purchased_tickets), 3)

    def test_get_user_tickets(self):
        TicketService.purchase_tickets(self.raffle.id, 1, 3)
        user_tickets = TicketService.get_user_tickets(1)
        self.assertEqual(len(user_tickets), 3)

    def test_refund_ticket(self):
        tickets, _ = TicketService.purchase_tickets(self.raffle.id, 1, 1)
        ticket_id = tickets[0].id

        # Test refunding a valid ticket
        success, message = TicketService.refund_ticket(ticket_id)
        self.assertTrue(success)
        self.assertIn("Ticket refunded successfully", message)

        # Verify the ticket is no longer associated with the user
        refunded_ticket = TicketService.get_ticket_by_id(ticket_id)
        self.assertIsNone(refunded_ticket.user_id)

        # Test refunding a non-existent ticket
        success, message = TicketService.refund_ticket(9999)
        self.assertFalse(success)
        self.assertIn("Ticket not found", message)

    def test_purchase_tickets_for_ended_raffle(self):
        # End the raffle
        self.raffle.end_time = datetime.utcnow() - timedelta(days=1)
        self.raffle.status = RaffleStatus.ENDED
        db.session.commit()

        # Attempt to purchase tickets
        tickets, error = TicketService.purchase_tickets(self.raffle.id, 1, 1)
        self.assertIsNone(tickets)
        self.assertIn("Cannot purchase tickets. Raffle status is ENDED", error)

if __name__ == '__main__':
    unittest.main()