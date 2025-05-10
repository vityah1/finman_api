from typing import Optional, Dict, List, Any, Union
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
import logging
import json

from api.funcs import get_main_sql
from api.payments.funcs import get_dates
from mydb import db, get_db
from sqlalchemy.orm import Session
from utils import do_sql_sel
from dependencies import get_current_user
from models.models import User

# Створюємо router замість Blueprint
router = APIRouter(tags=["api"])


@router.get("/api/payments/period")
async def payments_for_period(
    request: Request, 
    year: str = Query("", description="Рік для фільтрації"),
    month: str = Query("", description="Місяць для фільтрації"),
    mono_user_id: Optional[str] = Query(None, description="ID користувача Monobank"),
    currency: str = Query("UAH", description="Валюта"),
    group_user_id: Optional[str] = Query(None, description="ID користувача групи"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Повертає платежі згруповані за категоріями за певний період (рік, місяць)
    """
    
    if year:
        year = year.zfill(2)
    if month:
        month = month.zfill(2)

    current_date, end_date, start_date = get_dates(month, year)

    data = {
        "start_date": start_date,
        "end_date": end_date,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Повертає платежі згруповані за роками
    """

    substring_func = 'extract(YEAR from `rdate`)'
    amount_func = 'convert(sum(`amount`), UNSIGNED)'
    data = {"user_id": current_user.id}
    if grouped:
        main_sql = ("select rdate from `payments` "
                    "where amount > 0 and is_deleted = 0 and user_id = :user_id")
        add_fields = ""
    else:
        data["user_id"] = current_user.id
        data["mono_user_id"] = mono_user_id
        data["currency"] = currency or 'UAH'
        add_fields = f", {amount_func} as amount, count(*) as cnt"

        main_sql = get_main_sql(data)

    sql = f"""
select {substring_func} as year {add_fields}
from 
(
{main_sql}
) p
where 1=1
group by {substring_func} order by 1 desc
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
    Повертає платежі згруповані за місяцями в році
    """
    
    data = {
        "user_id": current_user.id,
        "year": str(year),
        "mono_user_id": mono_user_id,
        "currency": currency or 'UAH',
    }
    main_sql = get_main_sql(data)

    dialect_name = db.engine.dialect.name
    if dialect_name == 'sqlite':
        month_func = "strftime('%m', p.`rdate`)"
        year_func = "strftime('%Y', p.`rdate`)"
        amount_func = "CAST(sum(p.`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        month_func = 'extract(MONTH from p.`rdate`)'
        year_func = 'extract(YEAR from p.`rdate`)'
        amount_func = 'convert(sum(p.`amount`), UNSIGNED)'
    else:
        raise HTTPException(status_code=400, detail=f"Substring function not implemented for dialect: {dialect_name}")

    sql = f"""select 
{month_func} month, {amount_func} as amount,
count(*) as cnt
from 
(
{main_sql}
and {year_func} = :year
) p
where 1=1
group by {month_func} order by 1 desc
"""

    return do_sql_sel(sql, data)


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
