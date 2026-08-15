'''
Docstring for payload_model.py
For Payload validation.
Used in Dock layer only. 
'''

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from .master_validator import ISODateTime, CanonicalTime, Category, Flag, VersionsValidator, Mail, UserName, Password



class RegisterPayloadValidator(BaseModel):
    user: UserName
    mail: Mail
    pt_password: Password # plaintext password - secret string extracted by get_secret_value()

class LoginPayloadValidator(BaseModel):
    user: UserName
    pt_password: Password # plaintext password - secret string extracted by get_secret_value()

class LogoutPayloadValidator(BaseModel):
    user: UserName
