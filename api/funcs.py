import logging
from datetime import datetime

from api.config.schemas import ConfigTypes
from models import Payment
from mydb import db
from utils import do_sql_sel

logger = logging.getLogger()


def get_last_rate(currency, end_date):
    if currency == 'UAH':
        return 1

    sql_get_rate = f"""SELECT `saleRate` 
    FROM spr_exchange_rates 
    WHERE currency = '{currency}' AND rdate <= '{end_date}' 
    ORDER BY rdate DESC 
    LIMIT 1"""

    result = do_sql_sel(sql_get_rate)

    if len(result) < 1:
        raise Exception(f"not found rates for {currency}")

    sale_rate = result[0]["saleRate"]

    return sale_rate


def get_main_sql(
        data: dict | None,
        um: list = None,
) -> str:
    condition = []
    joins = []
    withs = []
    if um is None:
        um = []

    data["type_data"] = ConfigTypes.EXCLUDE_FROM_STAT.value

    if not data.get("end_date"):
        data["end_date"] = get_current_end_date()
    if data.get("start_date"):
        condition.append(" and p.`rdate` >= :start_date")

    condition.append(" and p.`rdate` <= :end_date")

    # data["sale_rate"] = get_last_rate(data["currency"], data.get("end_date"))

    if data.get("mono_user_id"):
        condition.append(" and mono_user_id = :mono_user_id")

    if data.get("q"):
        condition.append(f" and (c.`name` like %:q% or `descript` like %:q%)")

    if data.get("category_id"):
        withs.append(f"""
WITH RECURSIVE CategoryPath AS (
    SELECT id
    FROM categories
    WHERE id = :category_id
    UNION ALL
    SELECT c.id
    FROM categories c
    INNER JOIN CategoryPath cp ON cp.id = c.parent_id
)
""")
        joins.append("JOIN CategoryPath cp ON p.category_id = cp.id")

    sql = f"""
    {' '.join(withs)}
    SELECT p.id, p.rdate, p.category_id, p.mydesc,
           ROUND(
           CASE
               WHEN p.currency = :currency THEN p.currency_amount
               WHEN p.currency = 'UAH' AND :currency IN ('EUR', 'USD')
               THEN p.currency_amount / (
                   SELECT COALESCE(MAX(e.saleRate), 1)
                   FROM spr_exchange_rates e
                   WHERE e.currency = p.currency AND e.rdate <= p.rdate
                   ORDER BY e.rdate DESC
                   LIMIT 1
               )
               WHEN p.currency IN ('EUR', 'USD') AND :currency = 'UAH'
               THEN p.currency_amount * (
                   SELECT COALESCE(MAX(e.saleRate), 1)
                   FROM spr_exchange_rates e
                   WHERE e.currency = p.currency AND e.rdate <= p.rdate
                   ORDER BY e.rdate DESC
                   LIMIT 1
               )
               ELSE p.currency_amount
           END, 2) AS amount,
           p.mono_user_id, p.currency, p.currency_amount
           /*, e.saleRate*/
    FROM `payments` p
    {' '.join(joins)}
    WHERE 1=1
    AND p.user_id = :user_id
    AND `is_deleted` = 0
    AND `amount` > 0
    AND p.mydesc NOT IN (SELECT value_data FROM config WHERE type_data = :type_data AND user_id = :user_id)
    {' '.join(condition)}
    {' '.join(um)}
    """

    return sql


def get_current_end_date():
    curr_date = datetime.now()
    year = f'{curr_date:%Y}'
    month = f'{curr_date:%m}'
    end_date = f'{year if int(month) < 12 else int(year) + 1}-{int(month) + 1 if int(month) < 12 else 1:02d}-01'
    return end_date


def add_bulk_payments(data: list[dict]):
    result = False
    try:
        db.session.bulk_insert_mappings(Payment, data)
        db.session.commit()
        result = True
    except Exception as err:
        logger.error(f'{err}')
        db.session.rollback()
        db.session.flush()
    return result
