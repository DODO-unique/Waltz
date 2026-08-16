from typing import Any, Literal

from version_0_1.log.logger import get_logger

logger = get_logger("validators.endpoint_validators")

logger.debug("validators.endpoint_validators module loaded")

from pydantic import BaseModel
from version_0_1.validators.core_validator import UUID, IdentityPayload
from version_0_1.validators.validation_helper import Mail, Password, UserName


class LocalAuthPayload(BaseModel):
    identity: IdentityPayload
    password: Password

class WaltzResult(BaseModel):
    status: Literal['success', 'failure', 'indetermined']
    details: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None

class LogOutPayload(BaseModel):
    token: UUID
    identity: IdentityPayload

class BaseMail(BaseModel):
    pass

class RequestByMail(BaseMail):
    email: Mail

class RequestByIdentity(BaseMail):
    uname: UserName

class ValidationPayload(BaseModel):
    identity: IdentityPayload
    code: str