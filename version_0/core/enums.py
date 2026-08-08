from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import Generic, TypeVar

from ..validators.core_validator import IdentityPayload, OAuth, SessionRequest, Uid, WaltzAuth  


class Operation:
    class User(str, Enum):
        GET_ID = 'get_id'
        GET_USER_LOCAL = 'get_user_local'
        GET_USER_OAUTH = 'get_user_oauth'
        REGISTER_USER_OAUTH = 'register_user'
        REGISTER_USER_LOCAL = 'register_user_local'

    class Session(str, Enum):
        CREATE = 'create'
        CHECK = 'check'
        DELETE = 'delete'
        DELETE_ALL = 'delete_all'

    class OneTimePassword(str, Enum):
        STORE = 'store'
        GET = 'get'
        DELETE = 'delete'

P = TypeVar("P")
R = TypeVar("R")

@dataclass(frozen=True)
class OperationIntentions(Generic[P, R]):
    operation: Enum
    payload: type[P] | UnionType


class User:
    GetID: OperationIntentions[IdentityPayload, Uid | None] = OperationIntentions(
        operation = Operation.User.GET_ID,
        payload = IdentityPayload
    )

    GetUserLocal: OperationIntentions[Uid, str] = OperationIntentions(
        operation = Operation.User.GET_USER_LOCAL,
        payload = Uid
    )

    GetUserOAuth: OperationIntentions[Uid, OAuth] = OperationIntentions(
        operation = Operation.User.GET_USER_OAUTH,
        payload = Uid
    )

    RegisterUserOAuth: OperationIntentions[OAuth, None] = OperationIntentions(
        operation = Operation.User.REGISTER_USER_OAUTH,
        payload = OAuth
    )

    RegisterUserLocal: OperationIntentions[WaltzAuth, None] = OperationIntentions(
        operation = Operation.User.REGISTER_USER_LOCAL,
        payload = WaltzAuth
    )


class Session:
    Create: OperationIntentions[SessionRequest, None] = OperationIntentions(
        operation = Operation.Session.CREATE,
        payload = SessionRequest
    )

    Check: OperationIntentions[SessionRequest, bool] = OperationIntentions(
        operation = Operation.Session.CHECK,
        payload = SessionRequest
    )

    Delete: OperationIntentions[SessionRequest, None] = OperationIntentions(
        operation = Operation.Session.DELETE,
        payload = SessionRequest
    )

    DeleteAll: OperationIntentions[SessionRequest, None] = OperationIntentions(
        operation = Operation.Session.DELETE_ALL,
        payload = SessionRequest
    )


class OneTimePassword:
    Store: OperationIntentions[str, None] = OperationIntentions(
        operation = Operation.OneTimePassword.STORE,
        payload = str
    )

    Get: OperationIntentions[Uid, str | None] = OperationIntentions(
        operation = Operation.OneTimePassword.GET,
        payload = Uid
    )

    DeleteOTP: OperationIntentions[Uid, None] = OperationIntentions(
        operation = Operation.OneTimePassword.DELETE,
        payload = Uid
    )


class FeatEnum(str, Enum):
    DATABASE = 'database'
    CADENCE = 'cadence'
    SERENITY = 'serenity'
