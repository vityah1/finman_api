import uuid
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship

from . base import BaseModel


Base = BaseModel


def generate_uuid4():
    return str(uuid.uuid4())


class SprSource(Base):
    __tablename__ = 'spr_sources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(29), unique=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "source",
    ]  

class SprTypePayment(Base):
    __tablename__ = 'spr_type_payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_payment = Column(String(29), unique=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "type_payment",
    ]

class SprCurrency(Base):
    __tablename__ = 'spr_currencies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    currencyCode = Column(Integer)
    currency = Column(String(29), unique=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "currency",
        "currencyCode"
    ]

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    payments = relationship('Payment', back_populates='category', lazy=True)
    name = Column(String(49))
    parent_id = Column(Integer)
    ord = Column(Integer)
    is_visible = Column(Boolean, nullable=False, default=False,)
    user_id = Column(Integer, ForeignKey('users.id'))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "name",
        "parent_id",
        "ord",
        "is_visible",
    ]

    __table_args__ = (
        Index(
            None,
            user_id, name, parent_id,
            unique=True
        ),
    )
Category.comment = 'Довідник категорій витрат'


class Category_(Base):
    __tablename__ = 'spr_cat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat = Column(String(49), unique=True)
    is_sub_cat = Column(Boolean, default=False, nullable=True)
    ord = Column(Integer)
    is_visible = Column(Boolean, nullable=False, default=False, comment="if show")
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "cat",
        "is_sub_cat",
        "ord",
        "is_visible"
    ]


class SubCategory(Base):
    __tablename__ = 'spr_sub_cat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat_id = Column(Integer, ForeignKey('spr_cat.id'))
    sub_cat = Column(String(49))
    ord = Column(Integer)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "cat_id",
        "sub_cat",
        "ord",
    ]

    __table_args__ = (
        Index(
            None,
            cat_id,
            sub_cat,
            unique=True,
        ),
    )

SubCategory.comment = 'Довідник під категорій витрат'


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    payments = relationship('Payment', back_populates='user', lazy=True)
    login = Column(String(20), unique=True)
    password = Column(String(29))
    fullname = Column(String(39))
    phone = Column(String(16), unique=True)
    email = Column(String(99), unique=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)
    config = relationship("Config", back_populates="user", lazy=True)
    mono_users = relationship("MonoUser", back_populates="user", lazy=True)

    _default_fields = [
        "login",
        "fullname",
        "phone",
        "email",
        "created"
    ]

    _hidden_fields = [
        "password",
    ]
    _readonly_fields = [
        "created",
    ]    

User.comment = 'Довідник користувачів'


class MonoUser(Base):
    __tablename__ = 'mono_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='mono_users', lazy=True)
    name = Column(String(29), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    payments = relationship('Payment', back_populates='mono_user', lazy=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = ["user_id", "name", "token", "created"]

    __table_args__ = (
        Index(
            None,
            user_id, name,
            unique=True
        ),
    )


class SprConfigTypes(Base):
    __tablename__ = 'spr_config_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_data = Column(String(29), unique=True)
    name = Column(String(255))
    is_multiple = Column(Boolean, nullable=True, default=False)
    is_need_add_value = Column(Boolean, nullable=True, default=False)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "type_data",
        "name_type",
        "is_multiple",
        "is_need_add_value"
    ]


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="config", lazy=True)
    type_data = Column(String(29), ForeignKey('spr_config_types.type_data'))
    value_data = Column(String(255, collation='utf8mb4_bin',),)
    json_data = Column(Text)
    add_value = Column(String(255, collation='utf8mb4_bin',))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "user_id",
        "type_data",
        "value_data",
        "add_value",
    ]

    _hidden_fields = [
        "password",
    ]
    _readonly_fields = [
        "created",
    ]

    __table_args__ = (
        Index(
            None,
            user_id,
            type_data,
            value_data,
            unique=True,
        ),
    )


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rdate = Column(DateTime, default=datetime.datetime.utcnow, comment="payment date")
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='payments')
    mydesc = Column(String(150))
    amount = Column(Integer)
    currencyCode = Column(Integer)
    mcc = Column(Integer, comment="code mcc point")
    type_payment = Column(String(29), ForeignKey('spr_type_payments.type_payment'), comment="Cash|Card")
    bank_payment_id = Column(String(36), unique=True, default=generate_uuid4, comment="id payment from bank")
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='payments', lazy=True)
    mono_user_id = Column(Integer, ForeignKey('mono_users.id'))
    mono_user = relationship('MonoUser', back_populates='payments', lazy=True)
    source = Column(String(29), ForeignKey('spr_sources.source'), comment="mono|pryvat|webapp")
    is_deleted = Column(Boolean, default=False, nullable=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    __table_args__ = (
        Index(
            None, rdate, user_id, category_id, mydesc, amount, is_deleted,
            unique=True
        ),
        Index(
            None, bank_payment_id,
            unique=True
        ),
    )

    _default_fields = [
        "rdate",
        "category_id",
        "mydesc",
        "amount",
        "currencyCode",
        "category",
        "source",
        "mono_user",
        "bank_payment_id",
    ]

    _readonly_fields = [
        "category",
    ]      

Payment.comment = 'Список витрат'
