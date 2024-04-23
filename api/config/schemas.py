from aenum import Enum


class ConfigTypes(Enum):
    MONO_ACCOUNT = 'mono_account'
    TELEGRAM_TOKEN = 'telegram_token'
    TELEGRAM_CHAT_ID = 'telegram_chat_id'
    PHONE_TO_NAME = 'phone_to_name'
    CATEGORY_REPLACE = 'category_replace'
    EXCLUDE_FROM_STAT = 'exclude_from_stat'
    IS_DELETED_BY_DESCRIPTION = 'is_deleted_by_description'

    @property
    def name(self):
        if self is ConfigTypes.TELEGRAM_TOKEN:
            return 'Токен телеграму'
        elif self is ConfigTypes.TELEGRAM_CHAT_ID:
            return 'chat_id телеграму'
        elif self is ConfigTypes.MONO_ACCOUNT:
            return 'ID рахунку в моно банку'
        elif self is ConfigTypes.PHONE_TO_NAME:
            return 'Номер телефону для показу по імені'
        elif self is ConfigTypes.CATEGORY_REPLACE:
            return 'Категорія на заміну по опису з моно'
        elif self is ConfigTypes.EXCLUDE_FROM_STAT:
            return 'Виключити із статистики'
        elif self is ConfigTypes.IS_DELETED_BY_DESCRIPTION:
            return 'Позначити як видалене по опису з моно'
        else:
            return False

    @property
    def is_multiple(self):
        if self is ConfigTypes.MONO_ACCOUNT:
            return True
        elif self is ConfigTypes.PHONE_TO_NAME:
            return True
        elif self is ConfigTypes.CATEGORY_REPLACE:
            return True
        elif self is ConfigTypes.EXCLUDE_FROM_STAT:
            return True
        elif self is ConfigTypes.IS_DELETED_BY_DESCRIPTION:
            return True
        else:
            return False

    @property
    def is_need_add_value(self):
        if self is ConfigTypes.PHONE_TO_NAME:
            return True
        elif self is ConfigTypes.CATEGORY_REPLACE:
            return True
        else:
            return False
