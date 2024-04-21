import datetime
import logging
from os import environ, path
from sys import path as syspath
from urllib.parse import urlparse

import pymysql
import requests

syspath.append(path.abspath(path.join(path.dirname(__file__), '..')))

DATABASE_URI = environ["DATABASE_URI"]


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler('get_rates.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()


def get_db_connection():
    parsed_uri = urlparse(DATABASE_URI)
    user = parsed_uri.username
    password = parsed_uri.password
    host = parsed_uri.hostname
    database = parsed_uri.path[1:]
    return pymysql.connect(host=host, user=user, password=password, db=database, cursorclass=pymysql.cursors.DictCursor)


def get_rates_from_api():
    url = 'https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11'
    response = requests.get(url)
    return response.json()


def find_existing_rate(cursor, current_date, currency, base_currency):
    cursor.execute(
        """
        SELECT * FROM spr_exchange_rates WHERE DATE(rdate) = %s AND currency = %s AND base_currency = %s
        """, (current_date, currency, base_currency)
    )
    return cursor.fetchone()


def update_rate(cursor, sale_rate, purchase_rate, existing_rate, currency):
    cursor.execute(
        """
        UPDATE spr_exchange_rates SET saleRate = %s, purchaseRate = %s, updated = %s WHERE id = %s
        """, (sale_rate, purchase_rate, datetime.datetime.now(datetime.timezone.utc), existing_rate['id'])
    )
    logger.info(
        f"Updated {currency} rate: saleRate from {existing_rate['saleRate']} to {sale_rate}, purchaseRate from {existing_rate['purchaseRate']} to {purchase_rate}"
    )


def insert_new_rate(cursor, current_date, base_currency, currency, sale_rate, purchase_rate):
    cursor.execute(
        """
        INSERT INTO spr_exchange_rates (rdate, base_currency, currency, saleRate, purchaseRate, created, updated, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pryvat_api')
        """, (current_date, base_currency, currency, sale_rate, purchase_rate,
              datetime.datetime.now(datetime.timezone.utc), datetime.datetime.now(datetime.timezone.utc))
    )
    logger.info(f"Added new {currency} rate: saleRate {sale_rate}, purchaseRate {purchase_rate}")


def update_or_create_rates():
    current_date = datetime.datetime.now(datetime.timezone.utc).date()
    rates_from_api = get_rates_from_api()
    conn = get_db_connection()
    cursor = conn.cursor()

    is_need_commit = False

    for rate in rates_from_api:
        currency = rate['ccy']
        base_currency = rate['base_ccy']
        sale_rate = float(rate['sale'])
        purchase_rate = float(rate['buy'])

        existing_rate = find_existing_rate(cursor, current_date, currency, base_currency)

        if existing_rate:
            if existing_rate['saleRate'] != sale_rate or existing_rate['purchaseRate'] != purchase_rate:
                update_rate(cursor, sale_rate, purchase_rate, existing_rate, currency)
                is_need_commit = True
        else:
            insert_new_rate(cursor, current_date, base_currency, currency, sale_rate, purchase_rate)
            is_need_commit = True

    if is_need_commit:
        conn.commit()

    cursor.close()
    conn.close()


if __name__ == '__main__':
    update_or_create_rates()
