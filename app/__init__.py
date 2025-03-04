from logging.config import dictConfig

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from app.config import logger_config
from models.models import SprCurrency
from mydb import db
from models import *


dictConfig(logger_config)
migrate = Migrate()
app = Flask(__name__)
CORS(app, support_credentials=True, origins='*')

app.config.from_pyfile('config.py')
# app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'ssl': {'fake_flag_to_enable_tls': True}}}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SECRET_KEY"] = SECRET_KEY
app.config["PROPAGATE_EXCEPTIONS"] = True
# app.config["JWT_SECRET_KEY"] = SECRET_KEY

jwt = JWTManager(app)

db.init_app(app)
migrate.init_app(app, db, render_as_batch=True)

from api.config import config_bp
from auth.auth import auth_bp
from api.api import api_bp
from api.mono import mono_bp
from api.mono_users import mono_users_bp
from api.sprs import sprs_bp
from api.revolut import revolut_bp
from api.wise import wise_bp
from api.p24 import p24_bp
from api.categories import categories_bp
from api.payments import payments_bp
from api.groups import groups_bp
from api.invitations.route import invitations_bp

app.register_blueprint(config_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(mono_bp)
app.register_blueprint(mono_users_bp)
app.register_blueprint(sprs_bp)
app.register_blueprint(revolut_bp)
app.register_blueprint(wise_bp)
app.register_blueprint(p24_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(invitations_bp)

from api.config.funcs import check_and_fill_spr_config_table, check_exsists_table
with app.app_context():
    if not check_exsists_table(SprConfigTypes):
        db.create_all()
    check_result = check_and_fill_spr_config_table()
    if not check_result:
        raise Exception('Config table not valid')
    if not check_exsists_table(SprCurrency):
        SprCurrency.__table__.create(db.engine)


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
def teardown_request(exception=None):
    if exception and hasattr(g, "db_session") and g.db_session:
        print(f"{exception=}")
        g.db_session.rollback()
    if hasattr(g, "db_session") and g.db_session:
        g.db_session.commit()
    db.session.remove()


@app.before_request
def before_request():
    db.session.remove()
    g.db_session = db.session


@app.errorhandler(404)
def page_not_found(error):
    app.logger.error(f'Resource not found: {request.path}')
    return jsonify({"message": f"{error}, path: {request.path}"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=False)
