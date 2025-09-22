from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from datetime import datetime
from fastapi.responses import JSONResponse
import logging


from api.funcs import get_main_sql
from api.payments.funcs import get_dates
from mydb import db, get_db
from sqlalchemy.orm import Session
from utility_helpers import do_sql_sel
from dependencies import get_current_user
from models.models import User, Payment, Category

# Створюємо router замість Blueprint
router = APIRouter(tags=["api"])


@router.get("/api/payments/period")
async def payments_for_period(
    request: Request,
    year: str = Query("", description="Рік для фільтрації"),
    month: str = Query("", description="Місяць для фільтрації"),
    start_date: Optional[str] = Query(None, description="Дата початку періоду (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Дата кінця періоду (YYYY-MM-DD)"),
    mono_user_id: Optional[str] = Query(None, description="ID користувача Monobank"),
    currency: str = Query("UAH", description="Валюта"),
    group_user_id: Optional[str] = Query(None, description="ID користувача групи"),
    source: Optional[str] = Query(None, description="Джерело платежу для фільтрації (mono|pryvat|pwa|revolut|wise)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Повертає платежі згруповані за категоріями за певний період (рік, місяць або custom період)
    """
    
    # Якщо передані кастомні дати, використовуємо їх
    if start_date and end_date:
        # Валідація формату дат
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            calculated_start_date = start_date
            calculated_end_date = end_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Невірний формат дати. Використовуйте YYYY-MM-DD")
    else:
        # Використовуємо логіку рік/місяць
        if year:
            year = year.zfill(2)
        if month:
            month = month.zfill(2)
        current_date, calculated_end_date, calculated_start_date = get_dates(month, year)

    data = {
        "start_date": calculated_start_date,
        "end_date": calculated_end_date,
        "user_id": current_user.id,
        "mono_user_id": mono_user_id,
        "currency": currency or 'UAH',
        "source": source,
    }

    # Додаємо фільтрацію за користувачем з групи
    if group_user_id:
        try:
            data["group_user_id"] = int(group_user_id)
        except (ValueError, TypeError):
            data["group_user_id"] = group_user_id

    main_sql = get_main_sql(data)

    dialect_name = db.get_bind().dialect.name

    if dialect_name == 'sqlite':
        amount_func = "CAST(sum(`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        amount_func = 'convert(sum(`amount`), UNSIGNED)'
    else:
        raise HTTPException(status_code=400, detail=f"Substring function not implemented for dialect: {dialect_name}")

    sql = f"""
    select 
    IF(c.parent_id = 0, p.category_id, (select id from categories where id=c.parent_id)) as category_id
    , 
    IF(c.parent_id = 0, c.name, (select name from categories where id=c.parent_id)) as name
    , {amount_func} as amount,
    count(*) as cnt
    from (
    {main_sql}
    ) p left join `categories` c
    on p.category_id = c.id
    where 1=1 
    group by IF(c.parent_id = 0, p.category_id, (select id from categories where id=c.parent_id))
    , 
    IF(c.parent_id = 0, c.name, (select name from categories where id=c.parent_id)) order by 3 desc
    """
    return do_sql_sel(sql, data)


@router.get("/api/payments/years")
async def payments_by_years(
    grouped: Optional[bool] = Query(False, description="Чи групувати за роками"),
    mono_user_id: Optional[str] = Query(None, description="ID користувача Monobank"),
    currency: str = Query("UAH", description="Валюта"),
    current_user: User = Depends(get_current_user),
):
    """
    Повертає платежі згруповані за роками з підтримкою валют UAH, EUR, USD
    """

    substring_func = 'YEAR(rdate)'

    data = {"user_id": current_user.id}
    if grouped:
        main_sql = (f"SELECT rdate, amount, currency FROM payments "
                    f"WHERE amount > 0 AND (is_deleted = 0 OR is_deleted IS NULL) AND user_id = :user_id")
    else:
        data["user_id"] = current_user.id
        data["mono_user_id"] = mono_user_id
        data["currency"] = currency or 'UAH'

        # Use get_main_sql for proper currency conversion
        main_sql_inner = get_main_sql(data)

        sql = f"""
        SELECT {substring_func} as year,
               ROUND(SUM(amount), 2) as amount,
               COUNT(*) as cnt
        FROM ({main_sql_inner}) p
        GROUP BY {substring_func}
        ORDER BY year DESC
        """

        return do_sql_sel(sql, data)

    sql = f"""
SELECT {substring_func} as year,
       ROUND(SUM(amount), 2) as amount,
       COUNT(*) as cnt
FROM
(
{main_sql}
) p
WHERE 1=1
GROUP BY {substring_func} ORDER BY 1 DESC
"""

    return do_sql_sel(sql, data)


@router.get("/api/payments/{year}/months")
async def payment_by_months(
    year: int,
    mono_user_id: Optional[str] = Query(None, description="ID користувача Monobank"),
    currency: str = Query("UAH", description="Валюта"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Повертає платежі згруповані за місяцями в році з підтримкою валют UAH, EUR, USD
    """

    # Use get_main_sql for proper currency conversion
    data = {
        "user_id": current_user.id,
        "start_date": f"{year}-01-01",
        "end_date": f"{year + 1}-01-01",
        "currency": currency or 'UAH'
    }

    if mono_user_id:
        data["mono_user_id"] = mono_user_id

    main_sql = get_main_sql(data)

    sql = f"""
    SELECT MONTH(p.rdate) as month,
           ROUND(SUM(p.amount), 2) as amount,
           COUNT(*) as cnt
    FROM ({main_sql}) p
    WHERE YEAR(p.rdate) = {year}
    GROUP BY MONTH(p.rdate)
    ORDER BY month DESC
    """

    result = do_sql_sel(sql, data)

    # Format results
    return [
        {
            "month": int(row["month"]),
            "amount": float(row["amount"]) if row["amount"] else 0,
            "cnt": row["cnt"],
            "currency": currency
        }
        for row in result
    ]


@router.get("/api/about")
async def about():
    """
    Повертає вміст файлу /txt/about.html
    """
    logger = logging.getLogger(__name__)
    try:
        with open("txt/about.html", encoding="utf8") as f:
            data = f.read()
    except Exception as err:
        logger.error(f"{err}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "data": "error open about file"}
        )

    return {"status": "ok", "data": data}
