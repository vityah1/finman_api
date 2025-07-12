import logging
from datetime import datetime

from api.config.schemas import ConfigTypes
from api.mono.funcs import get_category_id
from models import Payment, User
from mydb import db
from utility_helpers import do_sql_sel

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
    if um is None:
        um = []

    user_id = data.get("user_id")
    data["type_data"] = ConfigTypes.EXCLUDE_FROM_STAT.value

    if not data.get("end_date"):
        data["end_date"] = get_current_end_date()
    if data.get("start_date"):
        condition.append(" and p.`rdate` >= :start_date")

    condition.append(" and p.`rdate` <= :end_date")

    # Додаємо фільтр за конкретним користувачем групи
    if data.get("group_user_id"):
        condition.append(" and p.user_id = :group_user_id")
    else:
        # Якщо не вказано конкретного користувача, фільтруємо за всіма користувачами групи
        condition.append(" and p.user_id IN (SELECT u.id FROM users u JOIN user_group_association uga ON u.id = uga.user_id JOIN `groups` g ON uga.group_id = g.id WHERE g.id = (SELECT g.id FROM `groups` g JOIN user_group_association uga ON g.id = uga.group_id WHERE uga.user_id = :user_id LIMIT 1))")

    # Додаємо JOIN для категорій, щоб включити як користувацькі, так і групові категорії
    joins.append("""
    LEFT JOIN categories c ON p.category_id = c.id
    LEFT JOIN categories gc ON (
        c.name = gc.name AND 
        gc.group_id = (SELECT g.id FROM `groups` g JOIN user_group_association uga ON g.id = uga.group_id WHERE uga.user_id = :user_id LIMIT 1) AND
        (c.parent_id = gc.parent_id OR (c.parent_id IS NULL AND gc.parent_id IS NULL))
    )
    """)

    # Залишаємо фільтр за mono_user_id для зворотної сумісності
    if data.get("mono_user_id"):
        condition.append(" and mono_user_id = :mono_user_id")

    if data.get("q"):
        condition.append(" and (c.`name` like %:q% or gc.`name` like %:q%)")

    if data.get("category_id"):
        # Додаємо рекурсивний CTE для категорій
        recursive_cte = """
        WITH RECURSIVE CategoryPath AS (
            SELECT id, name, parent_id, group_id, user_id
            FROM categories
            WHERE id = :category_id AND (
                group_id IN (
                    SELECT g.id 
                    FROM `groups` g
                    JOIN user_group_association uga ON g.id = uga.group_id
                    WHERE uga.user_id = :user_id
                ) OR 
                user_id = :user_id OR 
                group_id IS NULL
            )
            UNION ALL
            SELECT c.id, c.name, c.parent_id, c.group_id, c.user_id
            FROM categories c
            INNER JOIN CategoryPath cp ON cp.id = c.parent_id
            WHERE (
                c.group_id IN (
                    SELECT g.id 
                    FROM `groups` g
                    JOIN user_group_association uga ON g.id = uga.group_id
                    WHERE uga.user_id = :user_id
                ) OR 
                c.user_id = :user_id OR 
                c.group_id IS NULL
            )
        )
        """
        joins.append("JOIN CategoryPath cp ON p.category_id = cp.id")
    else:
        recursive_cte = ""

    sql = f"""
    {recursive_cte}
    SELECT p.id, p.rdate, p.category_id, p.mydesc,
           ROUND(
           CASE
               WHEN p.currency = :currency THEN p.currency_amount
               WHEN p.currency = 'UAH' AND :currency IN ('EUR', 'USD')
               THEN p.currency_amount / (
                   SELECT COALESCE(MAX(e.saleRate), 1)
                   FROM spr_exchange_rates e
                   WHERE e.currency = :currency AND e.rdate <= p.rdate
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
           p.mono_user_id, p.currency, p.currency_amount, p.source, p.user_id
    FROM `payments` p
    {' '.join(joins)}
    WHERE 1=1
    AND `is_deleted` = 0
    AND `currency_amount` > 0
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


def find_category(user: User, description: str) -> tuple[int, bool]:
    category_id = None
    is_deleted = False
    user_config = user.config
    for config_row in user_config:
        if config_row.type_data not in (
                ConfigTypes.IS_DELETED_BY_DESCRIPTION.value, ConfigTypes.CATEGORY_REPLACE.value):
            continue
        # set as deleted according to rules
        if config_row.type_data == ConfigTypes.IS_DELETED_BY_DESCRIPTION.value:
            if description == config_row.value_data:
                is_deleted = 1
        # for replace category according to rules
        if config_row.type_data == ConfigTypes.CATEGORY_REPLACE.value:
            if config_row.add_value and description.find(config_row.value_data.strip()) > -1:
                try:
                    category_id = int(config_row.add_value)
                    break
                except Exception as err:
                    logging.warning(f'can not set category id for cat: {config_row.add_value=}, {err}')

    if not category_id:
        category_id = get_category_id(user.id, description)
    return category_id, is_deleted
