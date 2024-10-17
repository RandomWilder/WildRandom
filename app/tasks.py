from celery import Celery
from app import create_app, db
from app.models.raffle import Raffle, RaffleStatus
from app.services.raffle_service import RaffleService
from datetime import datetime

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = create_app()
celery = make_celery(flask_app)

@celery.task
def end_raffles():
    with flask_app.app_context():
        now = datetime.utcnow()
        ended_raffles = Raffle.query.filter(
            Raffle.end_time <= now, 
            Raffle.status.in_([RaffleStatus.ACTIVE, RaffleStatus.COMING_SOON, RaffleStatus.PAUSED, RaffleStatus.SOLD_OUT])
        ).all()
        
        for raffle in ended_raffles:
            raffle.status = RaffleStatus.ENDED
            db.session.commit()
            RaffleService.select_winner(raffle.id)

@celery.task
def start_raffles():
    with flask_app.app_context():
        now = datetime.utcnow()
        starting_raffles = Raffle.query.filter(
            Raffle.start_time <= now,
            Raffle.status == RaffleStatus.COMING_SOON
        ).all()
        
        for raffle in starting_raffles:
            raffle.status = RaffleStatus.ACTIVE
            db.session.commit()

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, end_raffles.s(), name='Check and end raffles every minute')
    sender.add_periodic_task(60.0, start_raffles.s(), name='Check and start raffles every minute')