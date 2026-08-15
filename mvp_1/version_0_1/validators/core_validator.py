# --------------------- Imports

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator
from version_0_1.exceptions.waltz_exceptions import RequiredFieldMissingException
from version_0_1.log.logger import get_logger

logger = get_logger("validators.core_validator")

logger.debug("validators.core_validator module loaded")
from validation_helper import Addresses, Mail, Password, ProviderName, Uid, UserName
from version_0_1.constants.providers import (
    DiscordClaimSchema,
    GitHubClaimSchema,
    OAuthProviders,
)
from version_0_1.core.enums import OperationIntentions

# ---------------- Cadence Schemas

class CadencePayload(BaseModel):
    """
    Internal payload schema for sending email requests to relevant service set by developer.

    ```python
    email: Mail
    code: str
    ```

    Notes:
    - `code` is **not hashed**.
    - It is the decimal string representation of an integer.
    """
    email : Mail
    code : str


class CadenceTicket(BaseModel):
    '''
    A wrapper around CadencePayload.   
    Important for requesting tickets to cadence decorator

        ```python
        id: UUID = uuid4()
        payload: CadencePayload
        ```
    '''
    id: UUID = Field(default_factory=uuid4)
    payload: CadencePayload

# ------------------ Identity Service

class IdentityServiceSchema(BaseModel):
    pass

class IdentityPayload(IdentityServiceSchema):
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
        logger.debug("IdentityPayload.check_contact called: email=%s, uname=%s", self.email, self.uname)
        if self.email is None and self.uname is None:
            logger.error("IdentityPayload validation failed: neither email nor uname provided")
            raise RequiredFieldMissingException("Either email or uname must be provided.")
        return self

class BaseRegisterPayload(IdentityServiceSchema):
    id: Uid = Field(default_factory=uuid4) # NOTE: sub comes here as string, local handles UUID
    name: str | None = None
    identity: IdentityPayload
    gender: Literal["male", "female", "non_binary", "prefer_not_to_say", "self_describe"] | None = None
    birthdate: datetime | None = None
    addr: Addresses | None = None
    picture: AnyHttpUrl | None = None

class OAuthRegistration(BaseRegisterPayload):
    profile: AnyHttpUrl | None = None
    website: AnyHttpUrl | None = None
    zoneinfo: str | None = None
    locale: str | None = None
    updated_at: datetime # compare for changes

class LocalAuthRegistrationPayload(BaseRegisterPayload):
    '''
    Used only and only for Local Auth registration.
        ```python
        Required
        id: str | UUID = uuid4() 
        identity: IdentityPayload
        password: Password

        Optional
        name: str | None = None
        gender: Literal["male", "female", "non_binary", "prefer_not_to_say", "self_describe"] | None = None
        birthdate: datetime | None = None
        addr: Addresses | None = None
        picture: AnyHttpUrl | None = None
        ```
    
    '''
    password: Password

class OAuthAuthPayload(BaseModel):
    sub: str #the sub is the only thing we need to compare
    updated_at: datetime


# ------------------ Serenity 

class OAuthSchema(BaseModel):
    pass

class TokenResponse(OAuthSchema):
    access_token: str # They would usually always have one if they follow OAuth 2.0
    token_type: str # almost always 'bearer'
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    id_token: str | None = None

class TradeResponse(OAuthSchema):
    provider: ProviderName
    client_id: str
    token_response: TokenResponse

class TokenRequest(OAuthSchema):
    grant_type: Literal["authorization_code"] = "authorization_code"
    code: str
    redirect_uri: AnyHttpUrl
    client_id: str
    client_secret: str | None = None
    code_verifier: str | None = None


class AuthorizationRequest(OAuthSchema):
    response_type: Literal["code"] = "code" # you don't need to set it everytime, since default is code
    client_id : str  # we get this from client
    redirect_uri : AnyHttpUrl # from client, only one time though
    scope: str # a space-delimited string 
    state: str # random cryptographic stream
    code_challenge: str | None = None # if you don't set it then it is None
    code_challenge_method: Literal["S256"] | None = None

class BaseAuthorizationResponse(OAuthSchema):
    provider: "ProviderName"
    state: str

class AuthorizationSuccess(BaseAuthorizationResponse):
    status: Literal["success"]
    code: str

class AuthorizationFailure(BaseAuthorizationResponse):
    status: Literal["failure"]
    error: str
    error_description: str
    error_url: str

AuthorizationResponse = AuthorizationSuccess | AuthorizationFailure 

class CredentialsTicket(BaseModel):
    '''
    A credentials ticket simply requests by provider name. 
    All details registered by the providername are requested.

        ```python
        id: UUID = uuid4()
        provider = Literal["google", "microsoft", "github", "discord", "linkedin", "custom"]
        ```
    '''
    id: UUID = Field(default_factory=uuid4)
    provider: ProviderName

class ResourceRequestPayload(BaseModel):
    provider: ProviderName
    access_token: str

class ResourceResponsePayload(BaseModel):
    provider: OAuthProviders
    claim_schema: GitHubClaimSchema | DiscordClaimSchema | None

# ------------------- Session

class SessionRequest(BaseModel):
    Uid: Uid | None = None
    token: UUID = Field(default_factory=uuid4)
    expiry: float = time.time()

class SessionResponse(BaseModel):
    token: UUID | None = None
    expiry: float


# ------------------- SDK Schemas

class SDKSchemas(BaseModel):
    pass

class OAuthCredentials(SDKSchemas):
    client_id : str
    client_secret : str | None

    def with_provider_defaults(self, provider: ProviderName, uri: AnyHttpUrl) -> "Credentials":
        return Credentials(
            redirect_uri= uri,
            provider=provider,
            **self.model_dump()
        )


class DatabaseRegistry(BaseModel):
    '''
    A subset of Registry in listeners.
        operation: User | Session | OneTimePassword
        operator: Callable[[Any], Any]
    
    '''
    operation: OperationIntentions[Any, Any]
    operator: Callable[[Any], Any]

class Credentials(OAuthCredentials):
    redirect_uri : AnyHttpUrl
    provider : ProviderName

class Registry(SDKSchemas):
    database : set[DatabaseRegistry] = set()
    cadence : Callable[[CadencePayload], None] | None = None
    serenity : set[Credentials] = set()

class GrandRegistry(Registry):
    registered_database_operation : set[OperationIntentions[Any, Any]] = set()
    registered_serenity_providers : set[ProviderName]  = set()
    # cadence, database, serenity

class TicketType(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: OperationIntentions[Any, Any]
    payload: OAuthRegistration | OAuthAuthPayload | LocalAuthRegistrationPayload | IdentityPayload | Uid | SessionRequest

# ------------------- JWT

class JWKSchema(BaseModel):
    kid: str
    kty: str
    alg: str
    iss: str
    n: str
    e: str  
    model_config = ConfigDict(extra="allow")

class JWKVerificationRequest(BaseModel):
    provider: ProviderName
    id_token: str
    client_id: str