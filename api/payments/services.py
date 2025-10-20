import datetime
import logging
import re

from fastapi import HTTPException, status
from sqlalchemy import select
from api.payments.schemas import PaymentBase, PaymentCreate, PaymentUpdate, PaymentResponse, OperationResult, BulkOperationResult

from api.funcs import get_last_rate, get_main_sql
from api.payments.funcs import (
    conv_refuel_data_to_desc, convert_desc_to_refuel_data, create_bank_payment_id, get_dates,
    get_user_phones_from_config
)
from api.groups.services import check_user_in_group
from models.models import Payment
from fastapi_sqlalchemy import db
from utility_helpers import do_sql_sel

logger = logging.getLogger()


def add_payment_(user_id: int, payment_data: PaymentCreate):
    """
    insert a new payment
    """
    # Конвертуємо Pydantic модель у словник ОДРАЗУ
    payment_dict = payment_data.model_dump(exclude_unset=True)

    # Встановлюємо ID користувача в словник
    payment_dict["user_id"] = user_id

    # Обробляємо дані заправки, якщо вони є
    if payment_data.refuel_data and payment_data.refuel_data.km:
        refuel_dict = payment_data.refuel_data.model_dump(exclude_unset=True)
        result = conv_refuel_data_to_desc(refuel_dict)
        if result:
            payment_dict["mydesc"] = result

    # Створюємо унікальний ID платежу
    payment_dict["bank_payment_id"] = create_bank_payment_id(payment_dict)

    # Розраховуємо суму в UAH, якщо валюта інша - працюємо зі словником
    currency = payment_dict.get("currency")
    currency_amount = payment_dict.get("currency_amount")
    rdate = payment_dict.get("rdate")

    logger.info(f"[ADD PAYMENT] Currency conversion check: currency={currency}, currency_amount={currency_amount}, rdate={rdate}")

    if currency != 'UAH' and currency_amount:
        logger.info(f"[ADD PAYMENT] Entering currency conversion for {currency}")
        rate = get_last_rate(currency, rdate)
        logger.info(f"[ADD PAYMENT] Exchange rate retrieved: {rate}")

        # Одразу записуємо в словник
        payment_dict["amount"] = float(currency_amount) * rate
        payment_dict["amount_original"] = currency_amount
        payment_dict["currency_original"] = currency
        payment_dict["exchange_rate"] = rate
        logger.info(f"[ADD PAYMENT] Calculated: {currency_amount} * {rate} = {payment_dict['amount']}, tracking fields set")
    else:
        logger.info(f"[ADD PAYMENT] No conversion needed (UAH or no currency_amount)")
        # Одразу записуємо в словник
        payment_dict["amount"] = currency_amount
        payment_dict["amount_original"] = currency_amount
        payment_dict["currency_original"] = 'UAH'
        payment_dict["exchange_rate"] = 1.0
        logger.info(f"[ADD PAYMENT] Set default values: amount={payment_dict['amount']}, exchange_rate=1.0")

    logger.info(f"[ADD PAYMENT] Payment data dict: {payment_dict}")

    # Створюємо об'єкт Payment та заповнюємо через update()
    payment = Payment()
    # Видаляємо refuel_data перед update
    payment_dict_clean = {k: v for k, v in payment_dict.items() if k != 'refuel_data'}
    payment.update(**payment_dict_clean)

    # Log final values before commit
    logger.info(f"[ADD PAYMENT] Final DB values before commit: currency={payment.currency}, currency_amount={payment.currency_amount}, amount={payment.amount}, exchange_rate={payment.exchange_rate}")

    try:
        db.session.add(payment)
        db.session.flush()  # КРИТИЧНО: flush() щоб зміни потрапили в сесію
        db.session.commit()
        logger.info(f"Платіж успішно доданий: {payment.id}")
        # Refresh to get updated values from database
        db.session.refresh(payment)
    except Exception as err:
        db.session.rollback()
        logger.error(f"Помилка при додаванні платежу: {str(err)}")
        raise err

    # Використовуємо PaymentResponse для уніфікованого формату відповіді
    return PaymentResponse.model_validate(payment).model_dump()


def get_payments_detail(user_id: int, params: dict) -> list[dict]:
    """
    list or search all payments.
    if not set conditions year and month then get current year and month
    if set q then do search
    """

    sort = params.get("sort")
    category_id = params.get("category_id")
    year = params.get("year")
    month = params.get("month")
    currency = params.get('currency', 'UAH') or 'UAH'
    group_id = params.get("group_id")
    group_user_id = params.get("group_user_id")
    source = params.get("source")

    if not sort:
        sort = "order by `amount` desc"

    current_date, end_date, start_date = get_dates(month, year)

    um = ""
    if q := params.get("q"):
        um = f" and LOWER(`mydesc`) LIKE '%{q.lower()}%'"

    data = {
        "start_date": start_date,
        "end_date": end_date,
        "user_id": user_id,
        "mono_user_id": params.get("mono_user_id"),
        "currency": currency,
        "q": params.get("q"),
        "source": source,
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
           u.login AS user_login, p.display_currency
    from ({main_sql}) p
    LEFT JOIN categories c ON p.category_id = c.id
    LEFT OUTER JOIN mono_users m on p.mono_user_id = m.id
    LEFT JOIN users u ON p.user_id = u.id
    WHERE 1=1
    {sort}
    """

    try:
        result = do_sql_sel(sql, data)
    except Exception as e:
        logger.error(f"SQL error in get_payments_detail: {str(e)}")
        logger.error(f"SQL query: {sql}")
        logger.error(f"Data: {data}")
        raise

    if not result:
        return []

    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    user_phones = get_user_phones_from_config(user_id)
    for row in result:
        # Додаємо назву категорії до результату
        row["category_name"] = row.get("category_name", "")

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
    payment = db.session.query(Payment).get(payment_id)

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіж не знайдено")

    # Створюємо відповідь через Pydantic модель
    result = PaymentResponse.model_validate(payment).model_dump()
    
    # Додаємо назву категорії
    result["category_name"] = payment.category.name

    # Додаємо дані про заправку, якщо це заправка
    if payment.category.is_fuel:
        refuel_data = convert_desc_to_refuel_data(payment.mydesc)
        if refuel_data:
            result["refuel_data"] = refuel_data

    return result


def del_payment_(payment_id: int):
    """
    mark delete payment
    """
    payment = db.session.query(Payment).get(payment_id)
    if not payment:
        logger.error(f"Платіж з ID {payment_id} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіж не знайдено")

    payment.is_deleted = True
    try:
        db.session.commit()
        logger.info(f"Платіж з ID {payment_id} помічений як видалений")
    except Exception as err:
        db.session.rollback()
        logger.error(f"Помилка при видаленні платежу: {str(err)}")
        raise err

    return OperationResult(status="ok").model_dump()


def upd_payment_(payment_id: int, payment_data: PaymentUpdate):
    """
    update payment
    """
    # Отримуємо платіж з бази даних для перевірки існування
    payment = db.session.query(Payment).get(payment_id)
    if not payment:
        logger.error(f"Платіж з ID {payment_id} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіж не знайдено")

    # Конвертуємо Pydantic модель у словник ОДРАЗУ
    update_data = payment_data.model_dump(exclude_unset=True)

    # Оновлюємо дані про заправку, якщо вони надані
    if payment_data.refuel_data and payment_data.refuel_data.km:
        refuel_dict = payment_data.refuel_data.model_dump(exclude_unset=True)
        result = conv_refuel_data_to_desc(refuel_dict)
        if result:
            update_data["mydesc"] = result

    # Розраховуємо суму в UAH, якщо валюта інша - працюємо зі словником
    currency = update_data.get("currency")
    currency_amount = update_data.get("currency_amount")
    rdate = update_data.get("rdate")

    logger.info(f"[UPD PAYMENT {payment_id}] Currency conversion check: currency={currency}, currency_amount={currency_amount}, rdate={rdate}")

    if currency != 'UAH' and currency_amount:
        logger.info(f"[UPD PAYMENT {payment_id}] Entering currency conversion for {currency}")
        rate = get_last_rate(currency, rdate)
        logger.info(f"[UPD PAYMENT {payment_id}] Exchange rate retrieved: {rate}")

        # Одразу записуємо в словник
        update_data["amount"] = float(currency_amount) * rate
        update_data["amount_original"] = currency_amount
        update_data["currency_original"] = currency
        update_data["exchange_rate"] = rate
        logger.info(f"[UPD PAYMENT {payment_id}] Calculated: {currency_amount} * {rate} = {update_data['amount']}, tracking fields set")
    else:
        logger.info(f"[UPD PAYMENT {payment_id}] No conversion needed (UAH or no currency_amount)")
        # Одразу записуємо в словник
        update_data["amount"] = currency_amount
        update_data["amount_original"] = currency_amount
        update_data["currency_original"] = 'UAH'
        update_data["exchange_rate"] = 1.0
        logger.info(f"[UPD PAYMENT {payment_id}] Set default values: amount={update_data['amount']}, exchange_rate=1.0")

    try:
        # Оновлюємо платіж
        logger.info(f"[UPD PAYMENT {payment_id}] Updating payment with data: {update_data}")

        # Видаляємо поля які не можна оновити
        update_dict = {k: v for k, v in update_data.items() if k not in ['refuel_data', 'id']}
        logger.info(f"[UPD PAYMENT {payment_id}] Final update dict: {update_dict}")

        # КРИТИЧНО: Використовуємо прямий UPDATE замість setattr щоб уникнути проблем з SQLAlchemy
        db.session.query(Payment).filter(Payment.id == payment_id).update(update_dict)

        db.session.commit()
        logger.info(f"Платіж з ID {payment_id} успішно оновлено")
    except Exception as err:
        db.session.rollback()
        logger.error(f"Помилка при оновленні платежу: {str(err)}")
        raise err

    return get_payment_detail(payment_id)


def change_payments_category_(user_id: int, payment_ids: list[int], category_id: int):
    """
    Змінює категорію для списку платежів
    Вхідні дані: payment_ids - список ID платежів, category_id - нова категорія
    
    Дозволяє адміністратору групи змінювати категорію платежів учасників групи
    """
    
    # Отримуємо всі платежі
    payments = db.session.query(Payment).filter(Payment.id.in_(payment_ids)).all()

    # Платежі, до яких користувач має доступ
    allowed_payments = []

    # Перевіряємо доступ до кожного платежу
    for payment in payments:
        if payment.user_id == user_id:
            # Користувач є власником платежу
            allowed_payments.append(payment)
        else:
            # Перевіряємо, чи є користувач адміністратором групи, до якої належить платіж
            is_admin = check_user_in_group(payment.user_id, user_id)
            if is_admin:
                allowed_payments.append(payment)

    if not allowed_payments:
        # Якщо немає платежів, до яких користувач має доступ
        logger.warning(f"Не знайдено платежів для користувача {user_id} з ID {payment_ids} або немає прав доступу")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Немає доступу до платежів"
        )

    # Змінюємо категорію для доступних платежів
    for payment in allowed_payments:
        payment.category_id = category_id

    try:
        db.session.commit()
        logger.info(f"Змінено категорію для {len(allowed_payments)} платежів на {category_id}")
    except Exception as err:
        db.session.rollback()
        logger.error(f"Помилка при зміні категорії платежів: {str(err)}")
        raise err
    
    return BulkOperationResult.success(len(allowed_payments), "Оновлено")


def bulk_delete_payments_(user_id: int, payment_ids: list[int]):
    """
    Масове видалення платежів
    Вхідні дані: payment_ids - список ID платежів для видалення
    
    Дозволяє адміністратору групи видаляти платежі учасників групи
    """
    
    # Отримуємо всі платежі
    payments = db.session.query(Payment).filter(Payment.id.in_(payment_ids)).all()

    # Платежі, до яких користувач має доступ
    allowed_payments = []

    # Перевіряємо доступ до кожного платежу
    for payment in payments:
        if payment.user_id == user_id:
            # Користувач є власником платежу
            allowed_payments.append(payment)
        else:
            # Перевіряємо, чи є користувач адміністратором групи, до якої належить платіж
            is_admin = check_user_in_group(payment.user_id, user_id)
            if is_admin:
                allowed_payments.append(payment)

    if not allowed_payments:
        # Якщо немає платежів, до яких користувач має доступ
        logger.warning(f"Не знайдено платежів для користувача {user_id} з ID {payment_ids} або немає прав доступу")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Немає доступу до платежів"
        )

    # Позначаємо платежі як видалені
    for payment in allowed_payments:
        payment.is_deleted = True

    try:
        db.session.commit()
        logger.info(f"Видалено {len(allowed_payments)} платежів")
    except Exception as err:
        db.session.rollback()
        logger.error(f"Помилка при видаленні платежів: {str(err)}")
        raise err
    
    return BulkOperationResult.success(len(allowed_payments), "Видалено")
