import datetime
import logging
from os import environ, path
from sys import path as syspath
from urllib.parse import urlparse

import pymysql
import requests

syspath.append(path.abspath(path.join(path.dirname(__file__), '..')))

DATABASE_URI = environ["DATABASE_URI"]

logger = logging.getLogger()


def setup_logging(logger: logging.Logger):
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging(logger)


def send_telegram_message(telegram_token, telegram_chat_id, message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        'chat_id': telegram_chat_id, 'text': message, 'parse_mode': 'Markdown'
    }
    response = requests.post(url, json=payload)
    return response.text


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


def get_telegram_data(cursor):
    cursor.execute(
        """
        SELECT `type_data`, `value_data` FROM `config` cfg
        join `users` u on cfg.`user_id` = u.`id` 
        WHERE u.`is_admin` = %s AND type_data in ('telegram_token', 'telegram_chat_id')
        """, True
    )
    result = cursor.fetchall()
    telegram_token = None
    telegram_chat_id = None
    for row in result:
        if row.get('type_data') == 'telegram_token':
            telegram_token = row.get('value_data')
        if row.get('type_data') == 'telegram_chat_id':
            telegram_chat_id = row.get('value_data')

    return telegram_token, telegram_chat_id


def find_existing_rate(cursor, current_date, currency, base_currency):
    cursor.execute(
        """
        SELECT * FROM spr_exchange_rates WHERE DATE(rdate) = %s AND currency = %s AND base_currency = %s
        """, (current_date, currency, base_currency)
    )
    return cursor.fetchone()


def find_last_rate(cursor, currency, base_currency):
    cursor.execute(
        """
        SELECT * FROM spr_exchange_rates WHERE currency = %s AND base_currency = %s ORDER BY rdate DESC, updated DESC LIMIT 1
        """, (currency, base_currency)
    )
    return cursor.fetchone()


def update_rate(cursor, sale_rate, purchase_rate, existing_rate):
    cursor.execute(
        """
        UPDATE spr_exchange_rates SET saleRate = %s, purchaseRate = %s, updated = %s, source = %s WHERE id = %s
        """, (sale_rate, purchase_rate, datetime.datetime.now(datetime.timezone.utc), 'pryvat_api', existing_rate['id'])
    )


def insert_new_rate(cursor, current_date, base_currency, currency, sale_rate, purchase_rate):
    cursor.execute(
        """
        INSERT INTO spr_exchange_rates (rdate, base_currency, currency, saleRate, purchaseRate, created, updated, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pryvat_api')
        """, (
            current_date, base_currency, currency, sale_rate, purchase_rate,
            datetime.datetime.now(datetime.timezone.utc),
            datetime.datetime.now(datetime.timezone.utc))
    )


def update_or_create_rates():
    current_date = datetime.datetime.now(datetime.timezone.utc).date()
    rates_from_api = get_rates_from_api()
    conn = get_db_connection()
    cursor = conn.cursor()

    is_need_commit = False
    messages = []

    for rate in rates_from_api:
        currency = rate['ccy']
        base_currency = rate['base_ccy']
        sale_rate = float(rate['sale'])
        purchase_rate = float(rate['buy'])

        existing_rate = find_existing_rate(cursor, current_date, currency, base_currency)
        last_rate = find_last_rate(cursor, currency, base_currency)

        if existing_rate:
            # If there is already a rate for today, update it if changed
            if existing_rate['saleRate'] != sale_rate or existing_rate['purchaseRate'] != purchase_rate:
                update_rate(cursor, sale_rate, purchase_rate, existing_rate)
                is_need_commit = True
        else:
            # If no rate for today, insert new rate
            insert_new_rate(cursor, current_date, base_currency, currency, sale_rate, purchase_rate)
            is_need_commit = True

        if last_rate:
            # Compare with the last rate to determine if there's a change for notification
            if last_rate['saleRate'] != sale_rate:
                sale_rate_change = sale_rate - last_rate['saleRate']
                txt = (
                    f"Sale rate change for {currency}:\n"
                    f" - from {last_rate['saleRate']} to {sale_rate} "
                    f"({'+' if sale_rate_change > 0 else ''}{sale_rate_change:.4f})"
                )
                logger.info(txt)
                messages.append(txt)

            if last_rate['purchaseRate'] != purchase_rate:
                purchase_rate_change = purchase_rate - last_rate['purchaseRate']
                txt = (
                    f"Purchase rate change for {currency}:\n"
                    f" - from {last_rate['purchaseRate']} to {purchase_rate} "
                    f"({'+' if purchase_rate_change > 0 else ''}{purchase_rate_change:.4f})"
                )
                logger.info(txt)
                messages.append(txt)

    if is_need_commit:
        conn.commit()

    if messages:
        telegram_token, telegram_chat_id = get_telegram_data(cursor)
        if telegram_token and telegram_chat_id:
            send_telegram_message(telegram_token, telegram_chat_id, '\n'.join(messages))

    cursor.close()
    conn.close()


if __name__ == '__main__':
    update_or_create_rates()
