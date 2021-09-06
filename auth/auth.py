from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_cors import cross_origin
from utils import do_sql_cmd

auth_bp = Blueprint(
    "auth_bp",
    __name__,
)

# Create a route to authenticate your users and return JWT Token. The
# create_access_token() function is used to actually generate the JWT.
@auth_bp.route("/api/auth/signin", methods=["POST"])
@cross_origin()
# @app.route("/token", methods=["POST"])
def check_user():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    # Query your database for username and password
    # print(f"username:{username}, password:{password}")
    sql = f"""select token,token_d_end from myBudj_users where user='{username}' and password='{password}' """
    if do_sql_cmd(sql)["rowcount"] < 1:
        return jsonify({"msg": "Bad username or password"}), 401

    # create a new token with the user id inside
    access_token = create_access_token(
        identity=username, expires_delta=timedelta(days=30)
    )
    return jsonify({"accessToken": access_token, "username": username})


@auth_bp.route("/api/auth/signup", methods=["POST"])
# @cross_origin()
# @app.route("/token", methods=["POST"])
def create_user():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    # Query your database for username and password
    # print(f"username:{username}, password:{password}")
    sql = f"""insert into myBudj_users (user,password) values ('{username}','{password}') """
    if do_sql_cmd(sql)["rowcount"] < 1:
        return jsonify({"msg": "error create username"}), 401

    # create a new token with the user id inside
    access_token = create_access_token(
        identity=username, expires_delta=timedelta(days=30)
    )
    return jsonify({"accessToken": access_token, "username": username})
