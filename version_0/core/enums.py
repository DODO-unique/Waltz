from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import Generic, TypeVar
from uuid import UUID

from ..validators.core_validator import (
    IdentityPayload,
    LocalAuthRegistrationPayload,
    Mail,
    OAuthRegistration,
    SessionRequest,
    Uid,
)


class Operation:
    class User(str, Enum):
        GET_ID = 'get_id'
        GET_USER_LOCAL = 'get_user_local'
        GET_USER_OAUTH = 'get_user_oauth'
        GET_MAIL = 'get_mail'
        REGISTER_USER_OAUTH = 'register_user'
        REGISTER_USER_LOCAL = 'register_user_local'

    class Session(str, Enum):
        CREATE = 'create'
        CHECK = 'check'
        DELETE = 'delete'
        DELETE_ALL = 'delete_all'
        GET_TOKEN = 'get_token' 

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

    GetUserPassLocal: OperationIntentions[Uid, str] = OperationIntentions(
        operation = Operation.User.GET_USER_LOCAL,
        payload = Uid
    )

    GetUserOAuth: OperationIntentions[Uid, OAuthRegistration | None] = OperationIntentions(
        operation = Operation.User.GET_USER_OAUTH,
        payload = Uid
    )

    GetMail: OperationIntentions[Uid, Mail | None] = OperationIntentions(
        operation = Operation.User.GET_MAIL,
        payload = Uid
    )

    RegisterUserOAuth: OperationIntentions[OAuthRegistration, None] = OperationIntentions(
        operation = Operation.User.REGISTER_USER_OAUTH,
        payload = OAuthRegistration
    )

    RegisterUserLocal: OperationIntentions[LocalAuthRegistrationPayload, None] = OperationIntentions(
        operation = Operation.User.REGISTER_USER_LOCAL,
        payload = LocalAuthRegistrationPayload
    )


class Session:
    Create: OperationIntentions[SessionRequest, UUID] = OperationIntentions(
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

    GetToken: OperationIntentions[SessionRequest, UUID] = OperationIntentions(
        operation = Operation.Session.GET_TOKEN,
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

class AuthResultEnum(Enum):
    SUCCESS = 0
    NOT_AUTHENTIC = 1
    USER_NOT_FOUND = 2
    MISC_NOT_AUTH = 3

class ProviderCategory(Enum):
    OIDC = 0
    OAUTH = 1