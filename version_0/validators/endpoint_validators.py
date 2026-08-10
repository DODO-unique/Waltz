from pydantic import BaseModel
from typing import Literal, Any
from validation_helper import UserName, Mail, Password
from datetime import datetime

class LocalAuthenticationPayload(BaseModel):
    uname: UserName
    email: Mail
    password: Password
    time: datetime

class WaltzResult(BaseModel):
    status: Literal['success', 'failure']
    details: dict[str, Any]