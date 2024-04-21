import datetime
import logging
import os
import sys


import dotenv
import requests
from sqlalchemy import and_, create_engine, func
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import SprExchangeRates

dotenv.load_dotenv()

SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URI"]

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, pool_size=10, pool_pre_ping=True)

Session = sessionmaker(bind=engine)

logger = logging.getLogger()


def get_rates_from_api():
    url = 'https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11'
    response = requests.get(url)
    data = response.json()
    return data


def update_or_create_rates():
    current_date = datetime.datetime.now(datetime.timezone.utc).date()
    rates_from_api = get_rates_from_api()
    session = Session()

    for rate in rates_from_api:
        currency = rate['ccy']
        base_currency = rate['base_ccy']
        sale_rate = float(rate['sale'])
        purchase_rate = float(rate['buy'])

        existing_rate = session.query(SprExchangeRates).filter(
            and_(
                func.date(SprExchangeRates.rdate) >= current_date,
                SprExchangeRates.rdate < current_date + datetime.timedelta(days=1),
                SprExchangeRates.currency == currency, SprExchangeRates.base_currency == base_currency
            )
        ).first()

        if existing_rate:
            if existing_rate.saleRate != sale_rate or existing_rate.purchaseRate != purchase_rate:
                print(f"{existing_rate.saleRate=} != {sale_rate=} or {existing_rate.purchaseRate=} != {purchase_rate=}")
                existing_rate.saleRate = sale_rate
                existing_rate.purchaseRate = purchase_rate
                existing_rate.updated = datetime.datetime.now(datetime.timezone.utc)
                session.commit()
                print(f"Updated {currency} rate.")
        else:
            # Додавання нового запису, якщо на поточну дату його не знайдено
            new_rate = SprExchangeRates(
                rdate=current_date, base_currency=base_currency, currency=currency, saleRate=sale_rate,
                purchaseRate=purchase_rate, created=datetime.datetime.now(datetime.timezone.utc),
                updated=datetime.datetime.now(datetime.timezone.utc),
                source='pryvat_api'
            )
            session.add(new_rate)
            session.commit()
            print(f"Added new {currency} rate.")


if __name__ == '__main__':
    update_or_create_rates()
