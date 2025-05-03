import datetime
import logging
import re

from flask import abort, jsonify, request

from api.funcs import get_last_rate, get_main_sql
from api.payments.funcs import (
    conv_refuel_data_to_desc, convert_desc_to_refuel_data, create_bank_payment_id, get_dates,
    get_user_phones_from_config,
)
from models import Payment
from mydb import db
from utils import do_sql_sel

logger = logging.getLogger()


def add_payment_(user_id: int):
    """
    insert a new payment
    """
    data = request.get_json()
    data['user_id'] = user_id
    if "refuel_data" in data and "km" in data["refuel_data"] and data["refuel_data"]["km"]:
        result = conv_refuel_data_to_desc(data["refuel_data"])
        if result:
            data['mydesc'] = result
    data['bank_payment_id'] = create_bank_payment_id(data)
    if data['currency'] != 'UAH':
        data['amount'] = float(data['currency_amount']) * get_last_rate(data['currency'], data['rdate'])
    payment = Payment()
    payment.from_dict(**data)
    try:
        db.session().add(payment)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

    return payment.to_dict()


def get_payments_detail(user_id: int) -> list[dict]:
    """
    list or search all payments.
    if not set conditions year and month then get current year and month
    if set q then do search
    """

    sort = request.args.get("sort")
    category_id = request.args.get("category_id")
    year = request.args.get("year")
    month = request.args.get("month")
    currency = request.args.get('currency', 'UAH') or 'UAH'
    group_id = request.args.get("group_id")
    group_user_id = request.args.get("group_user_id")

    if not sort:
        sort = "order by `amount` desc"
    elif sort == "1":
        sort = "order by `rdate` desc"
    elif sort == "2":
        sort = "order by `category_id`"
    elif sort == "3":
        sort = "order by `amount` desc"
    else:
        sort = "order by `amount` desc"

    current_date, end_date, start_date = get_dates(month, year)
    um = []

    data = {
        "start_date": start_date,
        "end_date": end_date,
        "user_id": user_id,
        "mono_user_id": request.args.get("mono_user_id"),
        "currency": currency,
        "q": request.args.get("q"),
    }

    # Додаємо фільтрацію за групою
    if group_id:
        data["group_id"] = group_id

    # Додаємо фільтрацію за користувачем з групи
    if group_user_id:
        data["group_user_id"] = group_user_id

    if category_id:
        if category_id == "_":
            data["start_date"] = f"{current_date - datetime.timedelta(days=14):%Y-%m-%d}"
        else:
            data["category_id"] = category_id

    main_sql = get_main_sql(data, um)

    sql = f"""
    SELECT p.id, p.rdate, p.category_id, c.name AS category_name,
           c.parent_id, p.mydesc, p.amount,
           m.name AS mono_user_name, p.currency, p.currency_amount, p.source,
           u.login AS user_login
           /*, p.saleRate*/
    from ({main_sql}) p
    LEFT JOIN categories c ON p.category_id = c.id
    LEFT OUTER JOIN mono_users m on p.mono_user_id = m.id
    LEFT JOIN users u ON p.user_id = u.id
    WHERE 1=1
    {sort}
    """

    result = do_sql_sel(sql, data)
    if not result:
        return []

    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    user_phones = get_user_phones_from_config(user_id)
    for row in result:

        if pattern.search(row["mydesc"]):
            phone_number = pattern.search(row["mydesc"]).group(0)
            phone_number = f"+38{phone_number}" if not phone_number.startswith("+38") else phone_number
            if phone_number in user_phones:
                row["mydesc"] += f" [{user_phones[phone_number]}]"

    return result


def get_payment_detail(payment_id: int):
    """
    get info about payment
    """

    payment = db.session().query(Payment).get(payment_id)

    if not payment:
        abort(404, "payment not found")

    result = payment.to_dict()
    result["category_name"] = payment.category.name

    refuel_data = {}
    if payment.category.name == "Заправка":
        refuel_data = convert_desc_to_refuel_data(payment.mydesc)
    if refuel_data:
        result["refuel_data"] = refuel_data

    return result


def del_payment_(payment_id: int):
    """
    mark delete payment
    """
    payment = db.session().query(Payment).get(payment_id)
    payment.is_deleted = True
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

    return jsonify({"status": "ok"})


def upd_payment_(payment_id):
    """
    update payment
    """
    data = request.get_json()
    if "refuel_data" in data and "km" in data["refuel_data"] and data["refuel_data"]["km"]:
        data["mydesc"] = conv_refuel_data_to_desc(data["refuel_data"])
    data["id"] = payment_id
    payment = db.session().query(Payment).get(payment_id)
    data["rdate"] = datetime.datetime.strptime(data["rdate"], "%Y-%m-%d")
    try:
        payment.update(**data)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

    # return payment.to_dict()
    return get_payment_detail(payment_id)


def change_payments_category_(user_id: int):
    """
    Змінює категорію для списку платежів
    Вхідні дані: payment_ids - список ID платежів, category_id - нова категорія
    
    Дозволяє адміністратору групи змінювати категорію платежів учасників групи
    """
    from models.models import Group, UserGroupAssociation
    
    data = request.get_json()
    payment_ids = data.get('payment_ids', [])
    category_id = data.get('category_id')
    
    if not payment_ids or not category_id:
        abort(400, "Потрібно вказати payment_ids та category_id")
    
    try:
        # Перевіряємо, чи є користувач адміністратором якоїсь групи
        admin_groups = db.session().query(Group).filter_by(owner_id=user_id).all()
        
        # Отримуємо список ID користувачів, які входять до груп адміністратора
        group_member_ids = set()
        for group in admin_groups:
            associations = db.session().query(UserGroupAssociation).filter_by(group_id=group.id).all()
            for assoc in associations:
                group_member_ids.add(assoc.user_id)
        
        # Додаємо ID самого адміністратора до цього списку
        group_member_ids.add(user_id)
        
        # Перевіряємо кожен платіж
        updated_count = 0
        for payment_id in payment_ids:
            payment = db.session().query(Payment).get(payment_id)
            
            if not payment:
                continue
                
            # Перевіряємо, чи має користувач доступ до цього платежу
            # Доступ має власник платежу або адмін групи, у якій власник платежу є учасником
            if payment.user_id not in group_member_ids:
                continue
                
            payment.category_id = category_id
            updated_count += 1
        
        db.session().commit()
        return jsonify({
            "status": "ok", 
            "message": f"Оновлено категорію для {updated_count} платежів",
            "updated_count": updated_count
        })
    except Exception as err:
        db.session().rollback()
        raise err


def bulk_delete_payments_(user_id: int):
    """
    Масове видалення платежів
    Вхідні дані: payment_ids - список ID платежів для видалення
    
    Дозволяє адміністратору групи видаляти платежі учасників групи
    """
    from models.models import Group, UserGroupAssociation
    
    data = request.get_json()
    payment_ids = data.get('payment_ids', [])
    
    if not payment_ids:
        abort(400, "Потрібно вказати payment_ids")
    
    try:
        # Перевіряємо, чи є користувач адміністратором якоїсь групи
        admin_groups = db.session().query(Group).filter_by(owner_id=user_id).all()
        
        # Отримуємо список ID користувачів, які входять до груп адміністратора
        group_member_ids = set()
        for group in admin_groups:
            associations = db.session().query(UserGroupAssociation).filter_by(group_id=group.id).all()
            for assoc in associations:
                group_member_ids.add(assoc.user_id)
        
        # Додаємо ID самого адміністратора до цього списку
        group_member_ids.add(user_id)
        
        # Перевіряємо кожен платіж
        deleted_count = 0
        for payment_id in payment_ids:
            payment = db.session().query(Payment).get(payment_id)
            
            if not payment:
                continue
                
            # Перевіряємо, чи має користувач доступ до цього платежу
            # Доступ має власник платежу або адмін групи, у якій власник платежу є учасником
            if payment.user_id not in group_member_ids:
                continue

            # Замість фізичного видалення помічаємо платіж як видалений
            payment.is_deleted = True
            deleted_count += 1
        
        db.session().commit()
        return jsonify({
            "status": "ok", 
            "message": f"Видалено {deleted_count} платежів",
            "deleted_count": deleted_count
        })
    except Exception as err:
        db.session().rollback()
        raise err

