#!/home/vityah1/kt.if.ua/mypy/gapi/bin/python3.6
# _*_ coding:UTF-8 _*_
# import cgitb
# gitb.enable()
import sys

sys.path.insert(0, "/home/vityah1/kt.if.ua/mypy/gapi/lib/python3.6/site-packages")

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# print("import ok")

from mydb import db

app = Flask(__name__)
CORS(app, support_credentials=True)
from func import cfg

# from func import rand

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"""mysql+pymysql://{cfg['db_user']}:{cfg['db_passwd']}@{cfg['db_host']}/{cfg['db_db']}"""
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = cfg["secret_key"]

app.config["JWT_SECRET_KEY"] = cfg[
    "secret_key"
]  # Change this "super secret" with something else!
jwt = JWTManager(app)

db.init_app(app)

from rozhody.api import api_bp
from auth.auth import auth_bp

app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)

# app = create_app()


def __repr__(self):
    return "<Mysession %r" % self.id


@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"message": "resource not found"}), 404


if __name__ == "__main__":
    #    app.run(debug=True)
    #    app.debug=True
    #    app.run(host='0.0.0.0',port=4000)
    #    app.run(host='0.0.0.0',port=80,debug=False)
    app.run(host="0.0.0.0", port=5000, debug=False)
