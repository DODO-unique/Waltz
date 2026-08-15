from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel

from client_schemas import Registry
from ticket_enum import TicketEnum
from validation_helper import (
    Addresses,
    AuthorizationFailure,
    AuthorizationSuccess,
    Callable,
    DatabaseOperator,
    Mail,
    Name,
    Password,
    Payload,
    ProviderName,
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

class TicketType(BaseModel):
    id: UUID
    type: TicketEnum
    payload: Payload

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

class DatabaseRegistry(BaseModel):
    operation: TicketEnum
    operator: DatabaseOperator

CadenceOperator = Callable[[CadencePayload], None]

class GrandRegistry(Registry):
    registered_database_operations : set[TicketEnum]
    registered_serenity_providers : set[ProviderName] 
    # cadence, database, serenity

class TokenResponse(BaseModel):
    access_token: str # They would usually always have one if they follow OAuth 2.0
    token_type: str # almost always 'bearer'
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    id_token: str | None = None