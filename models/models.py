import datetime
import uuid

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, Float)
from sqlalchemy.dialects.mysql import FLOAT
from sqlalchemy.orm import relationship

from .base import BaseModel

Base = BaseModel


def generate_uuid4():
    return str(uuid.uuid4())


class SprSource(Base):
    __tablename__ = 'spr_sources'

    source = Column(String(29), unique=True)

    _default_fields = ["source", ]


class SprTypePayment(Base):
    __tablename__ = 'spr_type_payments'

    type_payment = Column(String(29), unique=True)

    _default_fields = ["type_payment", ]


class SprCurrency(Base):
    __tablename__ = 'spr_currencies'

    currencyCode = Column(Integer)
    currency = Column(String(3), unique=True)

    _default_fields = ["currency", "currencyCode"]


class Category(Base):
    __tablename__ = 'categories'

    payments = relationship('Payment', back_populates='category', lazy=True)
    name = Column(String(49))
    parent_id = Column(Integer)
    ord = Column(Integer)
    is_visible = Column(Boolean, nullable=False, default=False, )
    user_id = Column(Integer, ForeignKey('users.id'))
    is_fuel = Column(Boolean, nullable=False, default=False, )

    _default_fields = ["name", "parent_id", "ord", "is_visible", "is_fuel"]

    __table_args__ = (Index(
        None, 'user_id', 'name', 'parent_id', unique=True
    ),)


Category.comment = 'Directory of expense categories'


class User(Base):
    __tablename__ = 'users'

    payments = relationship('Payment', back_populates='user', lazy=True)
    login = Column(String(20), unique=True)
    password = Column(String(29))
    fullname = Column(String(39))
    phone = Column(String(16), unique=True)
    email = Column(String(99), unique=True)

    config = relationship("Config", back_populates="user", lazy=True)
    mono_users = relationship("MonoUser", back_populates="user", lazy=True)
    is_admin: Boolean = Column(Boolean, nullable=False, default=False)

    groups = relationship('UserGroupAssociation', back_populates='user')

    _default_fields = ["login", "fullname", "phone", "email", "created"]

    _hidden_fields = ["password", ]
    _readonly_fields = ["created", ]


User.comment = 'Users dictionary'


class MonoUser(Base):
    __tablename__ = 'mono_users'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='mono_users', lazy=True)
    name = Column(String(29), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    payments = relationship('Payment', back_populates='mono_user', lazy=True)

    _default_fields = ["user_id", "name", "token", "created"]

    __table_args__ = (Index(
        None, 'user_id', 'name', unique=True
    ),)


class SprConfigTypes(Base):
    __tablename__ = 'spr_config_types'

    type_data = Column(String(29), unique=True)
    name = Column(String(255))
    is_multiple = Column(Boolean, nullable=True, default=False)
    is_need_add_value = Column(Boolean, nullable=True, default=False)

    _default_fields = ["type_data", "name_type", "is_multiple", "is_need_add_value", "name"]


class Config(Base):
    __tablename__ = 'config'

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="config", lazy=True)
    type_data = Column(String(29), ForeignKey('spr_config_types.type_data'))
    value_data = Column(String(255, collation='utf8mb4_bin', ), )
    json_data = Column(Text)
    add_value = Column(String(255, collation='utf8mb4_bin', ))

    _default_fields = ["user_id", "type_data", "value_data", "add_value", ]

    _hidden_fields = ["password", ]
    _readonly_fields = ["created", ]

    __table_args__ = (Index(
        None, 'user_id', type_data, value_data, unique=True, ),)


class Payment(Base):
    __tablename__ = 'payments'

    rdate = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), comment="payment date")
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='payments')
    mydesc = Column(String(150))
    amount = Column(Float)
    currencyCode = Column(Integer, nullable=True, default=None)
    mcc = Column(Integer, comment="code mcc point")
    type_payment = Column(String(29), ForeignKey('spr_type_payments.type_payment'), comment="Cash|Card")
    bank_payment_id = Column(String(65), unique=True, default=generate_uuid4, comment="id payment from bank")
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='payments', lazy=True)
    mono_user_id = Column(Integer, ForeignKey('mono_users.id'))
    mono_user = relationship('MonoUser', back_populates='payments', lazy=True)
    source = Column(String(29), ForeignKey('spr_sources.source'), comment="mono|pryvat|webapp|revolut|wise")
    is_deleted = Column(Boolean, default=False, nullable=True)

    currency = Column(String(3), comment="EUR|USD|UAH")
    currency_amount = Column(Float, comment="amount of currency")
    bank_hash = Column(String(64), unique=True, default=generate_uuid4, comment="hash bank payment")

    __table_args__ = (Index(
        None, 'rdate', 'user_id', 'category_id', 'mydesc', 'amount', 'is_deleted', unique=True
    ), Index(
        None, bank_payment_id, unique=True
    ),)

    _default_fields = ["rdate", "category_id", "mydesc", "currency_amount", "currency", "category", "source",
        "mono_user", "bank_payment_id", ]

    _readonly_fields = ["category", ]


Payment.comment = 'List of expenses'


class SprExchangeRates(Base):
    __tablename__ = 'spr_exchange_rates'

    rdate = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), comment="exchange date")
    base_currency = Column(String(3), comment="UAH")
    currency = Column(String(3), comment="EUR|USD")
    saleRate = Column(FLOAT(10, 5))
    purchaseRate = Column(FLOAT(10, 5))
    source = Column(String(39), comment="pryvat_api | UkrRates")


class Group(Base):
    __tablename__ = 'groups'

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Адмін групи
    owner = relationship('User', foreign_keys=[owner_id])
    users = relationship('UserGroupAssociation', back_populates='group') # Зв'язок з користувачами

    _default_fields = ["name", "description", "owner_id"]


class UserGroupAssociation(Base):
    __tablename__ = 'user_group_association'

    # id додається автоматично через BaseModel
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)

    user = relationship('User')
    group = relationship('Group', back_populates='users')

    _default_fields = ["user_id", "group_id"]

    __table_args__ = (
        Index(
        None, 'user_id', 'group_id', unique=True, ),
    )