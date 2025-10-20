import logging

from fastapi import HTTPException
from models.models import Category, SprSource, SprTypePayment
from api.schemas.common import SprCurrencyResponse, SprSourceResponse, SprTypePaymentResponse, CategoryResponse

from fastapi_sqlalchemy import db

logger = logging.getLogger()


def get_spr_dictionary(dictionary) -> list[dict]:
    """
    get dictionary
    """
    if dictionary == 'currency':
        return [
            {'currencyCode': 'UAH', 'currency': 'UAH'},
            {'currencyCode': 'EUR', 'currency': 'EUR'},
            {'currencyCode': 'USD', 'currency': 'USD'},
        ]
    elif dictionary == 'source':
        model = SprSource
    elif dictionary == 'type_payment':
        model = SprTypePayment
    elif dictionary == 'category':
        model = Category
    else:
        return []               
    query = db.session.query(model).all()
    if not query:
        raise HTTPException(404, 'Not found dictionary')

    if dictionary == 'currency':
        return [SprCurrencyResponse.model_validate(item).model_dump() for item in query]
    elif dictionary == 'source':
        return [SprSourceResponse.model_validate(item).model_dump() for item in query]
    elif dictionary == 'type_payment':
        return [SprTypePaymentResponse.model_validate(item).model_dump() for item in query]
    elif dictionary == 'category':
        return [CategoryResponse.model_validate(item).model_dump() for item in query]
    else:
        return []
