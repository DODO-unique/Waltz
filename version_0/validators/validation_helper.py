from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal, TypeAlias
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    SecretStr,
    StringConstraints,
)

from error_handler import ErrorCodes, initiate_error_handler

# ----------------------------------------------------------------------------------------------------------------------------------------------------

def normalize_uname(v: str):
    if isinstance(v, str): #type: ignore
        return v.strip().lower()
    # if not string let it go as is, validation will catch it properly
    return v

def check_username_rules(v: str):
    if v.startswith(("_", ".")) or v.endswith((".", "_")):
        initiate_error_handler("Username cannot start or end with '_' or '.'", errCode=ErrorCodes.INVALID_USERNAME_FORMAT.value, error=ValueError("Invalid username"))

    if ".." in v or "__" in v:
        initiate_error_handler("Username cannot contain consecutive periods or underscores", errCode=ErrorCodes.INVALID_USERNAME_FORMAT.value, error=ValueError("Invalid username"))
    
    if v in prohibited_usernames:
        initiate_error_handler("Username is prohibited", errCode=ErrorCodes.INVALID_USERNAME_FORMAT.value, error=ValueError("Invalid username"))
    return v


UserName = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=20,
        pattern=r'^[a-z0-9_.]+$' 
        # Not allowing white spaces either. But we strip them before validation so that's fine. 
        # No capitalized letters either because they are lowered before validation
    ),
    BeforeValidator(normalize_uname),
    AfterValidator(check_username_rules)
]

prohibited_usernames = {"admin", "root", "system", "null", "undefined"}
    
# ---------------------------------------------------------------------------------------------------------------------------------------------------------

def strip_password(v: str):
    if isinstance(v, str): #type: ignore
        return v.strip()
    return v

def check_password_rules(v: SecretStr):
    if " " in v.get_secret_value():
        initiate_error_handler("Password cannot contain spaces", errCode=ErrorCodes.INVALID_PASSWORD_FORMAT.value, error=ValueError("Invalid password"))
    return v

Password = Annotated[
    SecretStr,
    StringConstraints(
        min_length=8,
        max_length=64,
    ),
    BeforeValidator(strip_password),
    AfterValidator(check_password_rules)
]

# ----------------------------------------------------------------------------------------------------------------------------------------------------


def process_mail(value: str):
    '''
    we will technically only get verified email here (email and login module TBD as of 22nd Feb)
    For now, I am adding from external library (I know we hate it mutually when we have to add external dependencies, but this is for MVP only)
    #Todo: make sure your custom email validator name is not same.
    '''
    try:
        validated_email = validate_email(value, check_deliverability=False)
        email = validated_email.normalized
        return email
    except EmailNotValidError as e: #type: ignore
        initiate_error_handler(message="Invalid email format", errCode=ErrorCodes.INVALID_EMAIL_FORMAT.value, error=e)


Mail = Annotated[str, BeforeValidator(process_mail)]

# ----------------------------------------------------------------------------------------------------------------------------------------------------

class Name(BaseModel):
    first_name: str
    middle_name: str | None
    last_name: str | None

# ----------------------------------------------------------------------------------------------------------------------------------------------------

class Address(BaseModel):
    one: str
    two: str
    three: str

class Addresses(BaseModel):
    address : list[Address]

ProviderName = Literal["google", "microsoft", "github", "discord", "linkedin", "custom"]

Uid: TypeAlias = str | UUID