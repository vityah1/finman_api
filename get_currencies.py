from os import environ
import datetime
from datetime import date, timedelta

import requests
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models

dotenv.load_dotenv()

SQLALCHEMY_DATABASE_URI = environ["DATABASE_URI"]

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, pool_size=10, pool_pre_ping=True)

Session = sessionmaker(bind=engine)


def fetch_and_fill(start_year = 2020):
    session = Session()
    end_date = date.today()
    current_date = date(start_year, 4, 7)

    while current_date <= end_date:
        # Форматування дати для запиту
        formatted_date = current_date.strftime('%d.%m.%Y')
        url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={formatted_date}'
        response = requests.get(url)
        data = response.json()

        # Перевірка наявності даних
        if 'exchangeRate' not in data:
            current_date += timedelta(days=1)
            continue

        for rate in data['exchangeRate']:
            if rate.get('currency') in ['USD', 'EUR']:
                new_rate = models.SprExchangeRates(
                    rdate=current_date,
                    base_currency='UAH',
                    currency=rate['currency'],
                    saleRate=rate.get('saleRate', 0),
                    purchaseRate=rate.get('purchaseRate', 0),
                    created=datetime.datetime.now(),
                    updated=datetime.datetime.now(),
                    source="pryvat_api",
                )
                session.add(new_rate)

        session.commit()
        current_date += timedelta(days=1)

    session.close()


if __name__ == "__main__":
    fetch_and_fill()