import hashlib
import re
from os import environ

import dotenv
from sqlalchemy import create_engine, or_, select
from sqlalchemy.orm import sessionmaker

import models

dotenv.load_dotenv()

SQLALCHEMY_DATABASE_URI = environ["DATABASE_URI"]

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, pool_size=10, pool_pre_ping=True)

Session = sessionmaker(bind=engine)


def conv_data():
    session = Session()
    stmt = select(models.Payment).where(
        or_(
            models.Payment.mydesc.like('%eur%'), models.Payment.source == 'revolut'
        ),
        models.Payment.rdate >= '2021-01-01', models.Payment.rdate <= '2024-04-06',
        models.Payment.is_deleted == 0,
        models.Payment.source != 'mono',
    # models.Payment.id == 9694
    )
    result = session.execute(stmt).scalars().all()

    for item in result:
        mydesc = item.mydesc
        print(f'{mydesc=}')
        matches = re.findall(r'(\d+\.\d+|\d+)\s?eur', mydesc, re.IGNORECASE)
        if len(matches) > 0:
            original_amount = float(matches[0])
        else:
            original_amount = round(item.amount / 40.60, 2)

        if original_amount > 0:
            item.currency_amount = int(original_amount * 100)
            item.currency = 'EUR'

            if item.source == 'revolut':
                bank_desc = item.bank_payment_id[14:]
                bank_desc = bank_desc[len(f'{item.user_id}{item.category_id}'):]
                bank_desc = bank_desc[:-len(f'{item.amount}0')]

                bank_payment_id = f"{item.rdate:%Y%m%d%H%M%S}{item.user_id}{item.category_id}{bank_desc}{original_amount}"

            else:
                bank_payment_id = item.bank_payment_id

            hash_object = hashlib.sha256(bank_payment_id.encode())
            bank_hash = hash_object.hexdigest()

            item.bank_hash = bank_hash
    session.commit()


if __name__ == '__main__':
    conv_data()
