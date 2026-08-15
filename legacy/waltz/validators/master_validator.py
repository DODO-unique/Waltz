from datetime import datetime, timezone
from typing import Annotated, Optional
from pydantic import BaseModel, SecretStr, field_validator, BeforeValidator, StringConstraints
from uuid import UUID
from error_handler import initiate_error_handler, ErrorCodes
from email_validator import EmailNotValidError, validate_email


# this is the start. Everything in-transit is datetime object.
def epoch_to_datetime(epoch: int | datetime) -> datetime:
    # print(f"epoch value: {repr(epoch)}, type: {type(epoch)}")
    if isinstance(epoch, datetime):
        if epoch.tzinfo is None:
            initiate_error_handler(message="Incorrect temporal type: datetime object must be timezone-aware", errCode=ErrorCodes.INCORRECT_TEMPORAL_TYPE.value, error=ValueError("datetime object must come with timezone"))
        return epoch.astimezone(tz=timezone.utc)
    if not isinstance(epoch, int): #type: ignore
        # holler when not int or datetime
        initiate_error_handler(message="Incorrect temporal type: epoch must be an integer", errCode=ErrorCodes.INCORRECT_TEMPORAL_TYPE.value, error=ValueError("epoch must be an integer"))
    elif epoch > 1e11:
        initiate_error_handler(message="Incorrect temporal type: epoch must be in seconds", errCode=ErrorCodes.INCORRECT_TEMPORAL_FORMAT.value, error=ValueError("epoch must be in seconds"))
    datetime_object = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return datetime_object

ISODateTime = Annotated[
            datetime,
            BeforeValidator(epoch_to_datetime)
            ]

# this is if we are wrapping as {value: ...}
class CanonicalTime(BaseModel):
    value: ISODateTime

class Category(BaseModel):
    value: str

    @field_validator('value')
    @classmethod
    def check_category(cls, v: str):
        all_cats = {'init', 'hydrate'}
        if v not in all_cats:
            raise ValueError(f"No such category {v}")
        return v

class Flag(BaseModel):
    value: str

    @field_validator('value')
    @classmethod
    def check_caps(cls, v: str):
        if not v.isupper():
            raise ValueError("Flag must be all capital")
        return v

# Like, why did I have two of these  
# class Versions(BaseModel):
#     value: str

#     @field_validator('value')
#     @classmethod
#     def check_version(cls, v: str):
#         all_versions = {'Tv_1.0'}
#         if v not in all_versions:
#             raise ValueError(f"No such version {v}")
#         return v
class VersionsValidator(BaseModel):
    value: str

    @field_validator('value')
    @classmethod
    def check_version(cls, v: str) -> str:
        all_versions = {'Tv_1.0', 'Tv_1.1', 'Tv_2.1', }
        if v not in all_versions:
            raise ValueError(f"No such version {v}")
        return v
    

# opdis package validator:
class OPDISPackageValidator(BaseModel):
    flag: Flag
    op_id : UUID | None

class IntimatePayload(BaseModel):
    prompt: Optional[str]
    delivery: Optional[ISODateTime]
    # OTHER FLAGS HERE

# opdis to tadis packaging:
class InterDispatchPackaging(BaseModel):
    flag: Flag
    intimate_payload: IntimatePayload

# email validation version 3.1
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


mail = Annotated[str, BeforeValidator(process_mail)]
class Mail(BaseModel):
    value: mail



uname = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=20,
        pattern=r'^[a-z0-9_.]+$' 
        # Not allowing white spaces either. But we strip them before validation so that's fine. 
        # No capitalized letters either because they are lowered before validation
    )
]

prohibited_usernames = {"admin", "root", "system", "null", "undefined"}
class UserName(BaseModel):
    '''
    constraints
    before
    after
    '''
    value: uname

    
    # BEFORE VALIDATOR
    @field_validator("value", mode="before")
    def normalize_uname(cls, v: str):
        if isinstance(v, str): #type: ignore
            return v.strip().lower()
        # if not string let it go as is, validation will catch it properly
        return v
    
    # AFTER VALIDATOR
    @field_validator("value")
    def check_username_rules(cls, v: str):
        if v.startswith("_") or v.endswith("_") or v.startswith(".") or v.endswith("."):
            initiate_error_handler("Username cannot start or end with '_' or '.'", errCode=ErrorCodes.INVALID_USERNAME_FORMAT.value, error=ValueError("Invalid username"))

        if ".." in v or "__" in v:
            initiate_error_handler("Username cannot contain consecutive periods or underscores", errCode=ErrorCodes.INVALID_USERNAME_FORMAT.value, error=ValueError("Invalid username"))
        
        if v in prohibited_usernames:
            initiate_error_handler("Username is prohibited", errCode=ErrorCodes.INVALID_USERNAME_FORMAT.value, error=ValueError("Invalid username"))
        

        return v
    

password = Annotated[
    SecretStr,
    StringConstraints(
        min_length=8,
        max_length=64,
    )
]


class Password(BaseModel):
    value: password


    # BEFORE VALIDATOR
    @field_validator("value", mode="before")
    def stip_password(cls, v: str):
        if isinstance(v, str): #type: ignore
            return v.strip()
        return v
    
    # AFTER VALIDATOR
    @field_validator("value")
    def check_password_rules(cls, v: SecretStr):
        if " " in v.get_secret_value():
            initiate_error_handler("Password cannot contain spaces", errCode=ErrorCodes.INVALID_PASSWORD_FORMAT.value, error=ValueError("Invalid password"))
        return v