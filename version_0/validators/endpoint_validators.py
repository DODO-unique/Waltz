from typing import Any, Literal

from core_validator import IdentityPayload
from pydantic import BaseModel
from validation_helper import Password


class LocalAuthPayload(BaseModel):
    identity: IdentityPayload
    password: Password

class WaltzResult(BaseModel):
    status: Literal['success', 'failure']
    details: dict[str, Any]