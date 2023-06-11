import logging

from flask import abort
from models.models import Category, SprCurrency, SprSource, SprTypePayment

from mydb import db

logger = logging.getLogger()


def get_spr_dictionary(dictionary) -> list[dict]:
    """
    get dictionary
    """
    if dictionary == 'currency':
        model = SprCurrency
    elif dictionary == 'source':
        model = SprSource
    elif dictionary == 'type_payment':
        model = SprTypePayment
    elif dictionary == 'category':
        model = Category
    else:
        return []               
    query = db.session().query(model).all()
    if not query:
        abort(404, 'Not found dictionary')

    return [item.to_dict() for item in query]
