import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.raffle import Raffle, RaffleStatus, PrizeDistributionType
from app.services.raffle_service import RaffleService
from app.models.ticket import Ticket

class TestRaffleService(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_raffle(self):
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(days=7)
        raffle, error = RaffleService.create_raffle(
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
        self.assertIsNone(error)
        self.assertIsNotNone(raffle)
        self.assertEqual(raffle.status, RaffleStatus.DRAFT)
        self.assertEqual(raffle.tickets.count(), 100)

    def test_activate_raffle(self):
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(days=7)
        raffle, _ = RaffleService.create_raffle(
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
        
        success, message = RaffleService.activate_raffle(raffle.id)
        self.assertTrue(success)
        self.assertEqual(raffle.status, RaffleStatus.COMING_SOON)

        # Simulate time passing to start time
        raffle.start_time = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()
        
        success, message = RaffleService.activate_raffle(raffle.id)
        self.assertTrue(success)
        self.assertEqual(raffle.status, RaffleStatus.ACTIVE)

    def test_pause_raffle(self):
        start_time = datetime.utcnow() - timedelta(days=1)
        end_time = start_time + timedelta(days=7)
        raffle, _ = RaffleService.create_raffle(
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
        RaffleService.activate_raffle(raffle.id)
        
        success, message = RaffleService.set_raffle_paused(raffle.id)
        self.assertTrue(success)
        self.assertEqual(raffle.status, RaffleStatus.PAUSED)

    def test_cancel_raffle(self):
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(days=7)
        raffle, _ = RaffleService.create_raffle(
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
        
        success, message = RaffleService.cancel_raffle(raffle.id)
        self.assertTrue(success)
        self.assertEqual(raffle.status, RaffleStatus.CANCELLED)

    def test_select_winner(self):
        start_time = datetime.utcnow() - timedelta(days=2)
        end_time = datetime.utcnow() - timedelta(days=1)
        raffle, _ = RaffleService.create_raffle(
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
        RaffleService.activate_raffle(raffle.id)
        
        # Simulate a ticket purchase
        ticket = raffle.tickets.first()
        ticket.user_id = 1
        db.session.commit()

        winners, error = RaffleService.select_winner(raffle.id)
        self.assertIsNone(error)
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0].user_id, 1)

if __name__ == '__main__':
    unittest.main()