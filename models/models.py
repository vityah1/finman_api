import uuid
import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean
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


class NewCategory(Base):
    __tablename__ = 'spr_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
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
        "is_visible"
    ]    

    __table_args__ = (
        Index(
            'i_u_spr_categories',
            user_id, name,
            unique=True
        ),
    )


class Category(Base):
    __tablename__ = 'spr_cat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat = Column(String(49))
    is_sub_cat = Column(Boolean, default=False, nullable=True)
    ord = Column(Integer)
    is_visible = Column(Boolean, nullable=False, default=False, comment="if show")
    user_id = Column(Integer, ForeignKey('users.id'))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "cat",
        "is_sub_cat",
        "ord",
        "is_visible"
    ]

    __table_args__ = (
        Index(
            'i_u_spr_cat',
            user_id, cat,
            unique=True
        ),
    )

Category.comment = 'Довідник категорій витрат'


class SubCategory(Base):
    __tablename__ = 'spr_sub_cat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat_id = Column(Integer, ForeignKey('spr_cat.id'))
    sub_cat = Column(String(49))
    ord = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "cat_id",
        "sub_cat",
        "ord",
    ]


    __table_args__ = (
        Index(
            'i_u_spr_sub_cat',
            user_id,
            cat_id,
            sub_cat,
            unique=True,
        ),
    )

SubCategory.comment = 'Довідник під категорій витрат'


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(20), unique=True)
    password = Column(String(29))
    fullname = Column(String(39))
    phone = Column(String(16))
    email = Column(String(99))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

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
    name = Column(String(29), nullable=False)
    mono_token = Column(String(255), nullable=False)
    mono_account = Column(String(99))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = ["user_id", "name", "mono_token", "created"]

    __table_args__ = (
        Index(
            'i_u_mono_users',
            user_id, mono_account,
            unique=True
        ),
        Index(
            'i_u_mono_users_token',
            mono_token,
            unique=True,
        ),
    )


class SprTypeSetting(Base):
    __tablename__ = 'spr_type_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_data = Column(String(29), unique=True)
    name_type = Column(String(255))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "type_data",
        "name_type",
    ]


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(20), ForeignKey('users.id'))
    type_data = Column(String(29), ForeignKey('spr_type_settings.type_data'))
    value_data = Column(String(255))
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    _default_fields = [
        "type_data",
        "value_data",
    ]

    _hidden_fields = [
        "password",
    ]
    _readonly_fields = [
        "created",
    ]

    __table_args__ = (
        Index(
            'i_u_config',
            user_id,
            type_data,
            unique=True
        ),
    )


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rdate = Column(DateTime, default=datetime.datetime.utcnow, comment="payment date")    
    cat = Column(String(99), ForeignKey('spr_cat.cat'))
    sub_cat = Column(String(99), ForeignKey('spr_sub_cat.sub_cat'))
    desc = Column(String(150))
    suma = Column(Integer)
    currencyCode = Column(Integer)
    mcc = Column(Integer, comment="code mcc point")
    type_payment = Column(String(29), ForeignKey('spr_type_payments.type_payment'), comment="Cash|Card")
    id_bank_payment = Column(String(20), unique=True, default=generate_uuid4, comment="id payment from bank")
    owner = Column(String(19), ForeignKey('users.login'))
    user_id = Column(String(19), ForeignKey('users.id'))
    user = relationship('User', foreign_keys=[user_id], primaryjoin='User.id == Payment.user_id', lazy=True)
    source = Column(String(29), ForeignKey('spr_sources.source'), comment="mono|pryvat|webapp")
    is_deleted = Column(Boolean, default=False, nullable=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime)

    __table_args__ = (
        Index(
            'i_u_payments', user_id, cat, sub_cat, suma, is_deleted,
            unique=True
        ),
    )

    _default_fields = [
        "rdate",
        "cat",
        "sub_cat",
        "desc",
        "suma",
        "currencyCode",
    ]

    _hidden_fields = [
        "password",
    ]
    _readonly_fields = [
        "created",
    ]      

Payment.comment = 'Список витрат'
