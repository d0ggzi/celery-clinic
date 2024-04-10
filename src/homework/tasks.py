import datetime
import random

from src.homework.celery import celery
import time
from celery.exceptions import Ignore
from src.homework.db import db


@celery.task(bind=True)
def create_record(self, doctor: str):
    self.update_state(state="Обработка...", meta=doctor)
    time.sleep(10)
    self.update_state(state="Запись...", meta=doctor)

    # создание рандомной даты
    random_days = random.randint(1, 10)
    appointment_date = datetime.datetime.now() + datetime.timedelta(days=random_days)
    appointment_date = str(appointment_date).split('.')[0]

    time.sleep(10)
    self.update_state(state="Успешно", meta=doctor)

    info = {
        "doctor": doctor,
        "date": appointment_date
    }

    db.save(self.request.id, info)
    raise Ignore()  # для корректного использования кастомных состояний
