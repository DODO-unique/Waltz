from enum import Enum


class Operation:
    class User(str, Enum):
        GET_ID = 'get_id'
        GET_USER = 'get_user'
        CHECK_ID = 'check_id'
        REGISTER_USER = 'register_user'

    class Session(str, Enum):
        CREATE = 'create'
        CHECK = 'check'
        DELETE = 'delete'

    class OneTimePassword(str, Enum):
        STORE = 'store'
        GET = 'get'
        DELETE = 'delete'

class FeatEnum(str, Enum):
    DATABASE = 'database'
    CADENCE = 'cadence'
    SERENITY = 'serenity'