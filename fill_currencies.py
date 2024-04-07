import json
from os import environ
import datetime

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models

dotenv.load_dotenv()

SQLALCHEMY_DATABASE_URI = environ["DATABASE_URI"]

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, pool_size=10, pool_pre_ping=True)

Session = sessionmaker(bind=engine)


def fill_from_file(file_path):
    session = Session()

    with open(file_path, 'r') as file:
        data = json.load(file)

    for item in data:
        if item['code'] == 978:  # EUR
            timestamp = item['time'] / 1000  # Конвертація мілісекунд в секунди
            date = datetime.datetime.utcfromtimestamp(timestamp)

            new_rate = models.SprExchangeRates(
                rdate=date,
                base_currency='UAH',
                currency='EUR',
                saleRate=item['sell'],
                purchaseRate=item['buy'],
                created=datetime.datetime.utcnow(),
                updated=datetime.datetime.utcnow(),
                source="UkrRates",
            )
            session.add(new_rate)

    session.commit()
    session.close()


if __name__ == "__main__":
    fill_from_file('EUR-universal.json')
