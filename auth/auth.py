from datetime import timedelta
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import create_access_token
from flask_cors import cross_origin
from utils import do_sql_cmd
from mydb import db
from models import User


auth_bp = Blueprint(
    "auth_bp",
    __name__,
)


@auth_bp.route("/api/auth/signin", methods=["POST"])
@cross_origin()
def user_login():
    data = request.get_json()

    sql = """select id, token,token_d_end, fullname, phone, email 
from myBudj_users 
where user=:username and password=:password """

    res = do_sql_cmd(sql, data)
    if res.get("rowcount") < 1:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(
        identity=data.get('username'), expires_delta=timedelta(days=30)
    )
    user = res.get('data')[0]
    return {
        "user_id": res.get('data')[0][0],
        "accessToken": access_token,
        "username": data.get('username'),
        "fullname": user[3],
        "phone": user[4],
        "email": user[5],
    }


@auth_bp.route("/api/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    result = {}

    user = db.session().query(User).get(user_id)
    try:
        db.session().delete(user)
        db.session().commit()
    except Exception as err:
        abort(500, f"user delete failed {err}")

    result["result"] = "ok"
    return result


@auth_bp.route("/api/auth/signup", methods=["POST"])
def create_user():
    result = {}
    data = request.get_json()

    user = User(**data)
    try:
        db.session().add(user)
        db.session().commit()
    except Exception as err:
        abort(500, f"user create failed {err}")

    access_token = create_access_token(
        identity=data.get('username'), expires_delta=timedelta(days=30)
    )
    result = user.to_dict()
    result["accessToken"] = access_token
    return result


@auth_bp.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id):
    """
    get user
    """
    user = db.session().query(User).get(user_id)
    if not user:
        abort(404, 'Not found users')

    return user.to_dict()


@auth_bp.route("/api/users", methods=["GET"])
def get_users():
    """
    get users
    """
    users = db.session().query(User).all()
    if not users:
        abort(404, 'Not found users')

    return [item.to_dict() for item in users]


@auth_bp.route("/api/users/<user_id>", methods=["PATCH"])
def edit_user(user_id):
    data = request.get_json()
    data['user_id'] = user_id

    sql = """update myBudj_users 
set user = :username, password = :password, fullname = :fullname, phone = :phone, email = :email 
where id = :user_id """

    res = do_sql_cmd(sql, data)
    if res["rowcount"] < 1:
        return jsonify({"message": "error edit user"}), 401

    access_token = create_access_token(
        identity=data.get('username'), expires_delta=timedelta(days=30)
    )

    return {
        "user_id": data.get('user_id'),
        "accessToken": access_token,
        "username": data.get('username'),
        "fullname": data.get('fullname'),
        "phone": data.get('phone'),
        "email": data.get('email'),
    }


@auth_bp.route("/api/auth/signup_", methods=["POST"])
def create_user_deprecate():
    data = request.get_json()

    sql = """insert into myBudj_users 
(user, password, fullname, phone, email) 
values (:username, :password, :fullname, :phone, :email) """

    res = do_sql_cmd(sql, data)
    if res["rowcount"] < 1:
        return jsonify({"msg": "error create username"}), 401

    access_token = create_access_token(
        identity=data.get('username'), expires_delta=timedelta(days=30)
    )

    return {
        "user_id": res.get('data'),
        "accessToken": access_token,
        "username": data.get('username'),
        "fullname": data.get('fullname'),
        "phone": data.get('phone'),
        "email": data.get('email'),
    }

