from logging.config import dictConfig

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from config import cfg, logger_config
from mydb import db
from models import *


dictConfig(logger_config)
migrate = Migrate()
app = Flask(__name__)
CORS(app, support_credentials=True, origins='*')

app.config["SQLALCHEMY_DATABASE_URI"] = cfg.get('DATABASE_URI')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = cfg["SECRET_KEY"]
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_SECRET_KEY"] = cfg["SECRET_KEY"]

jwt = JWTManager(app)
db.init_app(app)

migrate.init_app(app, db)

from api.api import api_bp
from api.payments import payments_bp
from auth.auth import auth_bp
from api.mono import mono_bp
from api.mono_users import mono_users_bp

app.register_blueprint(api_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(mono_bp)
app.register_blueprint(mono_users_bp)


def __repr__(self):
    return "<Mysession %r" % self.id


@app.after_request
def log_request_info(response):
    app.logger.info(
        "path: %s | method: %s | status: %s | size: %s",
        request.path,
        request.method,
        response.status,
        response.content_length,
    )
    return response


@app.teardown_request
def session_clear(exception=None):
    db.session.remove()
    if exception and db.session.is_active:
        db.session.rollback()


@app.errorhandler(404)
def page_not_found(error):
    app.logger.error(f'Resource not found: {request.path}')
    return jsonify({"message": f"{error}, path: {request.path}"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
