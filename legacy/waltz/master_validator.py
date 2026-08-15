from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import AnyHttpUrl, BaseModel, Field, model_validator

from client_schemas import Registry
from ticket_enum import (
    OneTimePassword,
    Operation,
    OperationIntentions,
    Session,
    User,
)
from validation_helper import (
    Addresses,
    AuthorizationFailure,
    AuthorizationSuccess,
    Callable,
    Mail,
    Name,
    Password,
    ProviderName,
    Uid,
    UserName,
)


class loginCredentials(BaseModel):
    identity: UserName | Mail
    pwd: Password
    isUname: bool

class FetchPayloads(BaseModel):
    identity: UserName | Mail
    isUname: bool

class RegisterPayload(BaseModel):
    password: Password
    uname: UserName | None
    mail: Mail | None
    name: Name | None
    dob: datetime | None
    addr: Addresses | None

class SessionPayload(BaseModel):
    '''
    session has:
        1. id
        2. user_id
        3. token
        4. created_at
        5. expires_at
    '''

class CadencePayload(BaseModel):
    email : Mail
    code : str


class CadenceTicket(BaseModel):
    id: UUID
    payload: CadencePayload

class AuthorizationRequest(BaseModel):
    response_type: Literal["code"] = "code" # you don't need to set it everytime, since default is code
    client_id : str  # we get this from client
    redirect_uri : AnyHttpUrl # from client, only one time though
    scope: str # a space-delimited string 
    state: str # random cryptographic stream
    code_challenge: str | None = None # if you don't set it then it is None
    code_challenge_method: Literal["S256"] | None = None

AuthorizationResponse = AuthorizationSuccess | AuthorizationFailure

class CredentialsTicket(BaseModel):
    id: UUID
    provider: ProviderName

class TokenRequest(BaseModel):
    grant_type: Literal["authorization_code"] = "authorization_code"
    code: str
    redirect_uri: AnyHttpUrl
    client_id: str
    client_secret: str | None = None
    code_verifier: str | None = None

intentions = User | Session | OneTimePassword
operations = Operation.User | Operation.Session | Operation.OneTimePassword


class DatabaseRegistry(BaseModel):
    '''
    A subset of Registry in listeners.
        operation: User | Session | OneTimePassword
        operator: Callable[[Any], Any]
    
    '''
    operation: OperationIntentions[Any, Any]
    operator: Callable[[Any], Any]

CadenceOperator = Callable[[CadencePayload], None]

class GrandRegistry(Registry):
    registered_database_operation : set[OperationIntentions[Any, Any]]
    registered_serenity_providers : set[ProviderName] 
    # cadence, database, serenity

class TokenResponse(BaseModel):
    access_token: str # They would usually always have one if they follow OAuth 2.0
    token_type: str # almost always 'bearer'
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    id_token: str | None = None


class BaseRegisterPayload(BaseModel):
    id: Uid = Field(default_factory=uuid4) # NOTE: sub comes here as string, local handles UUID
    name: str | None
    uname: str | None
    mail: Mail | None
    gender: Literal["male", "female", "non_binary", "prefer_not_to_say", "self_describe"] | None
    birthdate: datetime | None
    addr: Addresses | None
    picture: AnyHttpUrl | None

class OAuth(BaseRegisterPayload):
    profile: AnyHttpUrl | None
    website: AnyHttpUrl | None
    zoneinfo: str | None
    locale: str | None
    updated_at: datetime # compare for changes

class WaltzAuth(BaseRegisterPayload):
    password: Password

class IdentityPayload(BaseModel):
    '''
    Schema of IdentityPayload:

        uname: optional(UserName)   
        email: optional(Mail)

    Use internally to fetch Uid. 
    '''
    uname: UserName | None = None
    email: Mail | None = None

    @model_validator(mode="after")
    def check_contact(self):
        if self.email is None and self.uname is None:
            raise ValueError("Either email or uname must be provided.")
        return self

class OAuthAuthenticateResponse(BaseModel):
    id: str
    updated_at: datetime

class SessionRequest(BaseModel):
    Uid: Uid | None = None
    token: UUID = Field(default_factory=uuid4)

    
class TicketType(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: OperationIntentions[Any, Any]
    payload: OAuth | WaltzAuth | IdentityPayload | Uid | SessionRequest