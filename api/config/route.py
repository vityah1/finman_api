# _*_ coding:UTF-8 _*_





from api.config.services import (
    get_user_config_,
    get_config_,
    add_config_,
    edit_config_,
    delete_config_,
    get_config_types_,
)


config_bp = Blueprint(
    "config_bp",
    __name__,
)


@config_bp.route("/api/config/config_types", methods=["GET"])

def get_config_types():
    """
    get configs
    """
    return get_config_types_()


@config_bp.route("/api/users/config", methods=["GET"])


def get_user_config():
    """
    get user configs
    """
    current_user = 
    user_id = current_user.get('user_id')
    return get_user_config_(user_id)


@config_bp.route("/api/users/config", methods=["POST"])


def add_config():
    """
    add user config
    """
    current_user = 
    user_id = current_user.get('user_id')
    return add_config_(user_id)


@config_bp.route("/api/config/<config_id>", methods=["DELETE"])


def delete_config(config_id):
    """
    delete config
    """
    return delete_config_(config_id)


@config_bp.route("/api/config/<config_id>", methods=["PATCH"])


def edit_config(config_id):
    """
    edit config
    """
    return edit_config_(config_id)


@config_bp.route("/api/config/<config_id>", methods=["GET"])


def get_config(config_id):
    """
    get config
    """
    return get_config_(config_id)
