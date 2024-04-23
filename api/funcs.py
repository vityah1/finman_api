from datetime import datetime

from utils import do_sql_sel


def get_last_rate(currency, end_date):
    if currency != 'UAH':
        sql_get_rate = f"""SELECT `saleRate` 
    FROM spr_exchange_rates 
    WHERE currency = '{currency}' AND rdate <= '{end_date}' 
    ORDER BY rdate DESC 
    LIMIT 1"""
        result = do_sql_sel(sql_get_rate)
        if len(result) < 1:
            raise Exception(f"not found rates for {currency}")
        saleRate = result[0]["saleRate"]
    else:
        saleRate = 1
    return saleRate


def get_main_sql(
        data: dict | None
) -> str:
    condition = []

    if not data.get("end_date"):
        data["end_date"] = get_current_end_date()
    if data.get("start_date"):
        condition.append(" and p.`rdate` >= :start_date")

    condition.append(" and p.`rdate` <= :end_date")

    data["sale_rate"] = get_last_rate(data["currency"], data.get("end_date"))

    if data.get("mono_user_id"):
        condition.append(" and mono_user_id = :mono_user_id")

    if data.get("q"):
        condition.append(f" and (c.`name` like %:q% or `descript` like %:q%)")

    sql = f"""SELECT p.id, p.rdate, p.category_id, p.mydesc,
       CASE
           WHEN p.currency = :currency THEN p.currency_amount
           WHEN p.currency = 'UAH' AND :currency IN ('EUR', 'USD') and e.saleRate is not null 
           THEN p.currency_amount / e.saleRate
           WHEN p.currency IN ('EUR', 'USD') AND :currency = 'UAH' and e.saleRate is not null 
           THEN p.currency_amount * e.saleRate
           WHEN p.currency = 'UAH' AND :currency IN ('EUR', 'USD') and e.saleRate is null 
           THEN p.currency_amount / :sale_rate
           WHEN p.currency IN ('EUR', 'USD') AND :currency = 'UAH' and e.saleRate is null 
           THEN p.currency_amount *
:sale_rate
           ELSE p.currency_amount
       END AS amount,
       p.mono_user_id, p.currency, p.currency_amount, e.saleRate
FROM `payments` p
LEFT JOIN (
    SELECT e1.rdate, e1.currency, e1.saleRate, e1.purchaseRate
    FROM spr_exchange_rates e1
    JOIN (
        SELECT DATE(rdate) AS date, MAX(rdate) AS max_rdate
        FROM spr_exchange_rates
        WHERE currency = :currency
        GROUP BY DATE(rdate)
    ) e2 ON DATE(e1.rdate) = e2.date AND e1.rdate = e2.max_rdate
    WHERE e1.currency = :currency
) e ON DATE(e.rdate) = DATE(p.rdate)
where 1=1
and p.user_id = :user_id
and `is_deleted` = 0
and `amount` > 0
{' '.join(condition)}
"""

    return sql


def get_current_end_date():
    curr_date = datetime.now()
    year = f'{curr_date:%Y}'
    month = f'{curr_date:%m}'
    end_date = f'{year if int(month) < 12 else int(year) + 1}-{int(month) + 1 if int(month) < 12 else 1:02d}-01'
    return end_date
