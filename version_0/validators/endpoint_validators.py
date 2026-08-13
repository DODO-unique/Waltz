from typing import Any, Literal

from core_validator import UUID, IdentityPayload
from pydantic import BaseModel
from validation_helper import Password


class LocalAuthPayload(BaseModel):
    identity: IdentityPayload
    password: Password

class WaltzResult(BaseModel):
    status: Literal['success', 'failure']
    details: dict[str, Any] | None = None
    payload: dict[str, Any]

class LogOutPayload(BaseModel):
    token: UUID
    identity: IdentityPayload