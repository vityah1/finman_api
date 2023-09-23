from api.config.schemas import ConfigTypes
from api.config.funcs import add_new_config_row
# from api.mono.services import get_mono_user_info_

# def add_mono_accounts_to_config(user_id: int) -> list[dict]:
    result = []
    mono_user_info = get_mono_user_info_(user_id)
    if not mono_user_info:
        return result

    for account in mono_user_info.get('accounts'):
        data = {
            "user_id": user_id,
            "type_data": ConfigTypes.MONO_ACCOUNT.value,
            "value_data": account.get("id"),
            "json_data": account,
            }
        result.append(add_new_config_row(data))
    return result