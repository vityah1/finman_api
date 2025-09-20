from typing import Optional, Dict, List, Any, Union
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from datetime import datetime
from fastapi.responses import JSONResponse
import logging
import json
from sqlalchemy import select, func, extract, and_, or_, case

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
    show_original: Optional[bool] = Query(False, description="Показувати в оригінальній валюті"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Повертає платежі згруповані за роками з підтримкою валют
    """

    substring_func = 'YEAR(rdate)'

    # Choose amount field based on show_original flag
    if show_original:
        amount_field = 'amount_original'
        currency_filter = "AND currency_original = :currency" if currency != "ALL" else ""
    else:
        amount_field = 'amount'
        currency_filter = ""

    amount_func = f'ROUND(SUM({amount_field}), 2)'

    data = {"user_id": current_user.id}
    if grouped:
        main_sql = (f"SELECT rdate, {amount_field}, currency_original FROM payments "
                    f"WHERE amount > 0 AND (is_deleted = 0 OR is_deleted IS NULL) AND user_id = :user_id")
        add_fields = ""
    else:
        data["user_id"] = current_user.id
        data["mono_user_id"] = mono_user_id
        data["currency"] = currency or 'UAH'
        add_fields = f", {amount_func} as amount, COUNT(*) as cnt"

        if show_original and currency != "ALL":
            add_fields += ", currency_original"

        # Optimized SQL without subquery for better performance
        conditions = ["amount > 0", "(is_deleted = 0 OR is_deleted IS NULL)", "user_id = :user_id"]

        if mono_user_id:
            conditions.append("mono_user_id = :mono_user_id")

        if show_original and currency != "ALL":
            conditions.append("currency_original = :currency")

        main_sql = f"SELECT {substring_func} as year {add_fields} FROM payments WHERE {' AND '.join(conditions)} GROUP BY {substring_func} ORDER BY year DESC"

        return do_sql_sel(main_sql, data)

    sql = f"""
SELECT {substring_func} as year {add_fields}
FROM
(
{main_sql} {currency_filter}
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
    show_original: Optional[bool] = Query(False, description="Показувати в оригінальній валюті"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Повертає платежі згруповані за місяцями в році з підтримкою валют
    """

    # Build query conditions
    conditions = [
        Payment.user_id == current_user.id,
        extract('year', Payment.rdate) == year,
        or_(Payment.is_deleted == False, Payment.is_deleted == None)
    ]

    # Add mono_user filter if provided
    if mono_user_id:
        conditions.append(Payment.mono_user_id == mono_user_id)

    # Choose amount field based on show_original flag
    if show_original:
        amount_field = Payment.amount_original
        # Filter by original currency if specified
        if currency and currency != 'ALL':
            conditions.append(Payment.currency_original == currency)
    else:
        amount_field = Payment.amount
        # For UAH view, no need to filter by currency

    # Build aggregation query using SQLAlchemy
    stmt = select(
        extract('month', Payment.rdate).label('month'),
        func.sum(amount_field).label('amount'),
        func.count().label('cnt')
    ).where(
        and_(*conditions)
    ).group_by(
        extract('month', Payment.rdate)
    ).order_by(
        extract('month', Payment.rdate).desc()
    )

    # Execute query
    result = db.execute(stmt).all()

    # Format results
    return [
        {
            "month": int(row.month),
            "amount": float(row.amount) if row.amount else 0,
            "cnt": row.cnt,
            "currency": currency if show_original else "UAH"
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
