import datetime

from flask import json
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql.expression import not_
from sqlalchemy.orm.attributes import QueryableAttribute

from mydb import db


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated = Column(DateTime)

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **data):
        """
        Function to update model
        """
        for key, value in data.items():
            if key not in dir(self):
                continue
            if key == "id":
                continue
            if isinstance(getattr(self, key), BaseModel):
                continue
            setattr(self, key, value)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.id}"
