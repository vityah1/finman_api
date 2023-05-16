from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_cors import cross_origin
from utils import do_sql_cmd


auth_bp = Blueprint(
    "auth_bp",
    __name__,
)


@auth_bp.route("/api/auth/signin", methods=["POST"])
@cross_origin()
def user_login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    sql = """select token,token_d_end from myBudj_users where user=:username and password=:password """
    if do_sql_cmd(sql, {'username': username, 'password': password})["rowcount"] < 1:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(
        identity=username, expires_delta=timedelta(days=30)
    )
    return jsonify({"accessToken": access_token, "username": username})


@auth_bp.route("/api/auth/signup", methods=["POST"])
def create_user():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    sql = """insert into myBudj_users (user,password) values (:username, :password) """
    if do_sql_cmd(sql, {'username': username, 'password': password})["rowcount"] < 1:
        return jsonify({"msg": "error create username"}), 401

    access_token = create_access_token(
        identity=username, expires_delta=timedelta(days=30)
    )
    return jsonify({"accessToken": access_token, "username": username})
