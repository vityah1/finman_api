import datetime
import logging
import re

from fastapi import HTTPException, status
from api.payments.schemas import PaymentBase, PaymentCreate, PaymentUpdate, PaymentResponse, OperationResult, BulkOperationResult

from api.funcs import get_last_rate, get_main_sql
from api.payments.funcs import (
    conv_refuel_data_to_desc, convert_desc_to_refuel_data, create_bank_payment_id, get_dates,
    get_user_phones_from_config
)
from api.groups.services import check_user_in_group
from models.models import Payment
from mydb import db
from utility_helpers import do_sql_sel

logger = logging.getLogger()


def add_payment_(user_id: int, payment_data: PaymentCreate):
    """
    insert a new payment
    """
    # Встановлюємо ID користувача
    payment_data.user_id = user_id
    
    # Обробляємо дані заправки, якщо вони є
    if payment_data.refuel_data and payment_data.refuel_data.km:
        # Конвертуємо дані про заправку в опис
        refuel_dict = payment_data.refuel_data.model_dump(exclude_unset=True)
        result = conv_refuel_data_to_desc(refuel_dict)
        if result:
            payment_data.mydesc = result
    
    # Створюємо унікальний ID платежу
    payment_data.bank_payment_id = create_bank_payment_id(payment_data.model_dump())
    
    # Розраховуємо суму в UAH, якщо валюта інша
    logger.info(f"[ADD PAYMENT] Currency conversion check: currency={payment_data.currency}, currency_amount={payment_data.currency_amount}, rdate={payment_data.rdate}")

    if payment_data.currency != 'UAH' and payment_data.currency_amount:
        logger.info(f"[ADD PAYMENT] Entering currency conversion for {payment_data.currency}")
        rate = get_last_rate(payment_data.currency, payment_data.rdate)
        logger.info(f"[ADD PAYMENT] Exchange rate retrieved: {rate}")

        payment_data.amount = float(payment_data.currency_amount) * rate
        logger.info(f"[ADD PAYMENT] Calculated amount: {payment_data.currency_amount} * {rate} = {payment_data.amount}")

        # Set new currency tracking fields
        payment_data.amount_original = payment_data.currency_amount
        payment_data.currency_original = payment_data.currency
        payment_data.exchange_rate = rate
        logger.info(f"[ADD PAYMENT] Set tracking fields: amount_original={payment_data.amount_original}, currency_original={payment_data.currency_original}, exchange_rate={payment_data.exchange_rate}")
    else:
        logger.info(f"[ADD PAYMENT] No conversion needed (UAH or no currency_amount), using currency_amount as amount")
        payment_data.amount = payment_data.currency_amount
        # Set default values for UAH transactions
        payment_data.amount_original = payment_data.currency_amount
        payment_data.currency_original = 'UAH'
        payment_data.exchange_rate = 1.0
        logger.info(f"[ADD PAYMENT] Set default values: amount={payment_data.amount}, exchange_rate=1.0")
    
    # Створюємо об'єкт Payment з Pydantic моделі
    payment = Payment()
    payment_dict = payment_data.model_dump(exclude_unset=True)

    # КРИТИЧНО: Явно додаємо розраховані поля валюти, бо exclude_unset=True може їх виключити
    payment_dict["amount"] = payment_data.amount
    payment_dict["amount_original"] = payment_data.amount_original
    payment_dict["currency_original"] = payment_data.currency_original
    payment_dict["exchange_rate"] = payment_data.exchange_rate

    logger.info(f"[ADD PAYMENT] Payment data dict: {payment_dict}")

    for key, value in payment_dict.items():
        # Виключаємо refuel_data, оскільки це не колонка в таблиці Payment
        if key != 'refuel_data' and hasattr(payment, key):
            setattr(payment, key, value)

    # Log final values before commit
    logger.info(f"[ADD PAYMENT] Final DB values before commit: currency={payment.currency}, currency_amount={payment.currency_amount}, amount={payment.amount}, exchange_rate={payment.exchange_rate}")

    try:
        db.session().add(payment)
        db.session().flush()  # КРИТИЧНО: flush() щоб зміни потрапили в сесію
        db.session().commit()
        logger.info(f"Платіж успішно доданий: {payment.id}")
    except Exception as err:
        db.session().rollback()
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
    payment = db.session().query(Payment).get(payment_id)

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
    payment = db.session().query(Payment).get(payment_id)
    if not payment:
        logger.error(f"Платіж з ID {payment_id} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіж не знайдено")
        
    payment.is_deleted = True
    try:
        db.session().commit()
        logger.info(f"Платіж з ID {payment_id} помічений як видалений")
    except Exception as err:
        db.session().rollback()
        logger.error(f"Помилка при видаленні платежу: {str(err)}")
        raise err

    return OperationResult(status="ok").model_dump()


def upd_payment_(payment_id: int, payment_data: PaymentUpdate):
    """
    update payment
    """
    # Отримуємо платіж з бази даних
    payment = db.session().query(Payment).get(payment_id)
    if not payment:
        logger.error(f"Платіж з ID {payment_id} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіж не знайдено")

    # Оновлюємо дані про заправку, якщо вони надані
    if payment_data.refuel_data and payment_data.refuel_data.km:
        refuel_dict = payment_data.refuel_data.model_dump(exclude_unset=True)
        payment_data.mydesc = conv_refuel_data_to_desc(refuel_dict)

    # Розраховуємо суму в UAH, якщо валюта інша
    logger.info(f"[UPD PAYMENT {payment_id}] Currency conversion check: currency={payment_data.currency}, currency_amount={payment_data.currency_amount}, rdate={payment_data.rdate}")

    if payment_data.currency != 'UAH' and payment_data.currency_amount:
        logger.info(f"[UPD PAYMENT {payment_id}] Entering currency conversion for {payment_data.currency}")
        rate = get_last_rate(payment_data.currency, payment_data.rdate)
        logger.info(f"[UPD PAYMENT {payment_id}] Exchange rate retrieved: {rate}")

        payment_data.amount = float(payment_data.currency_amount) * rate
        logger.info(f"[UPD PAYMENT {payment_id}] Calculated amount: {payment_data.currency_amount} * {rate} = {payment_data.amount}")

        # Set currency tracking fields
        payment_data.amount_original = payment_data.currency_amount
        payment_data.currency_original = payment_data.currency
        payment_data.exchange_rate = rate
        logger.info(f"[UPD PAYMENT {payment_id}] Set tracking fields: amount_original={payment_data.amount_original}, currency_original={payment_data.currency_original}, exchange_rate={payment_data.exchange_rate}")
    else:
        logger.info(f"[UPD PAYMENT {payment_id}] No conversion needed (UAH or no currency_amount), using currency_amount as amount")
        payment_data.amount = payment_data.currency_amount
        # Set default values for UAH transactions
        payment_data.amount_original = payment_data.currency_amount
        payment_data.currency_original = 'UAH'
        payment_data.exchange_rate = 1.0
        logger.info(f"[UPD PAYMENT {payment_id}] Set default values: amount={payment_data.amount}, exchange_rate=1.0")

    # Конвертуємо Pydantic модель у словник та виключаємо None значення
    update_data = payment_data.model_dump(exclude_unset=True)

    # КРИТИЧНО: Явно додаємо розраховані поля валюти, бо exclude_unset=True може їх виключити
    update_data["amount"] = payment_data.amount
    update_data["amount_original"] = payment_data.amount_original
    update_data["currency_original"] = payment_data.currency_original
    update_data["exchange_rate"] = payment_data.exchange_rate

    # Встановлюємо ID платежу
    update_data["id"] = payment_id
    
    try:
        # Оновлюємо платіж
        logger.info(f"[UPD PAYMENT {payment_id}] Updating payment with data: {update_data}")

        # Видаляємо поля які не можна оновити
        update_dict = {k: v for k, v in update_data.items() if k not in ['refuel_data', 'id']}
        logger.info(f"[UPD PAYMENT {payment_id}] Final update dict: {update_dict}")

        # КРИТИЧНО: Використовуємо прямий UPDATE замість setattr щоб уникнути проблем з SQLAlchemy
        db.session().query(Payment).filter(Payment.id == payment_id).update(update_dict)

        db.session().flush()
        db.session().commit()
        logger.info(f"Платіж з ID {payment_id} успішно оновлено")

        # ДЕБАГ: Отримуємо платіж з БД після коміту і перевіряємо що збереглось
        db.session().expire_all()  # Очистити кеш сесії
        saved_payment = db.session().query(Payment).get(payment_id)
        logger.info(f"[UPD PAYMENT {payment_id}] AFTER COMMIT - DB values: currency={saved_payment.currency}, currency_amount={saved_payment.currency_amount}, amount={saved_payment.amount}, exchange_rate={saved_payment.exchange_rate}, amount_original={saved_payment.amount_original}, currency_original={saved_payment.currency_original}")
    except Exception as err:
        db.session().rollback()
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
    payments = db.session().query(Payment).filter(Payment.id.in_(payment_ids)).all()
    
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
        db.session().commit()
        logger.info(f"Змінено категорію для {len(allowed_payments)} платежів на {category_id}")
    except Exception as err:
        db.session().rollback()
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
    payments = db.session().query(Payment).filter(Payment.id.in_(payment_ids)).all()
    
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
        db.session().commit()
        logger.info(f"Видалено {len(allowed_payments)} платежів")
    except Exception as err:
        db.session().rollback()
        logger.error(f"Помилка при видаленні платежів: {str(err)}")
        raise err
    
    return BulkOperationResult.success(len(allowed_payments), "Видалено")
