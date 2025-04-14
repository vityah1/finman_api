from fastapi import APIRouter, Depends, Query, HTTPException, Request
from app.jwt import get_current_user
from typing import Optional

from api.funcs import get_main_sql
from api.payments.funcs import get_dates
from mydb import db
from utils import do_sql_sel


router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.get("/period")
def payments_for_period(
    year: Optional[str] = Query("", description="Year"),
    month: Optional[str] = Query("", description="Month"),
    mono_user_id: Optional[str] = Query(None),
    currency: str = Query("UAH"),
    group_user_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user)
):
    """
    return payments grouped by categories in some period (year, month)
    """
    year = year.zfill(2) if year else ""
    month = month.zfill(2) if month else ""

    current_date, end_date, start_date = get_dates(month, year)

    data = {
        "start_date": start_date,
        "end_date": end_date,
        "user_id": user_id,
        "mono_user_id": mono_user_id,
        "currency": currency or "UAH",
    }

    if group_user_id:
        try:
            data["group_user_id"] = int(group_user_id)
        except (ValueError, TypeError):
            data["group_user_id"] = group_user_id

    main_sql = get_main_sql(data)
    dialect_name = db.engine.dialect.name

    if dialect_name == "sqlite":
        amount_func = "CAST(sum(`amount`) AS INTEGER)"
    elif dialect_name == "mysql":
        amount_func = "convert(sum(`amount`), UNSIGNED)"
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

