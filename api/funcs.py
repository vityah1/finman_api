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
