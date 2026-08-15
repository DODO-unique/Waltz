import hashlib
import secrets
from random import randint
from typing import Any
from uuid import UUID, uuid4
import httpx

import bcrypt

from client_schemas import Credentials
from concrete.ticket_handler import TicketBus
from master_validator import (
    AuthorizationRequest,
    AuthorizationResponse,
    CadencePayload,
    CadenceTicket,
    CredentialsTicket,
    FetchPayloads,
    Payload,
    RegisterPayload,
    TokenRequest,
    TicketType,
    loginCredentials,
    TokenResponse
)
from ticket_enum import TicketEnum
from validation_helper import AuthorizationSuccess, Mail, ProviderName

# from demo_parent_ticket_resolver import 

bus = TicketBus()
async def publish_ticket(ticket: TicketType):
    return await bus.publish(ticket)

async def dispatch_ticket(ticket: CadenceTicket):
    return await bus.dispatch(ticket)

def hash_password(plain_text_password: str) -> bytes:
    # first we convert string to bytes
    password_bytes = plain_text_password.encode('utf-8')

    # generate salt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password

def compare_password(pt_pass: str, hpass: bytes) -> bool:
    password_bytes = pt_pass.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hpass)

async def check_token(token: UUID) -> bool:
    predicate = await publish_ticket(
        TicketType(
            id=uuid4(),
            type=TicketEnum.CHECK_TOKEN,
            payload=Payload(
                value={
                    "token" : token
                }
            )
        )
    )

    return predicate['predicate']

class InMemoryStateStore:
    '''
    A set. 
    Push: Adds a new string to the set.
    Pop: Removes state from storage and confirms it existed.
    '''

    def __init__(self):
        self.storage: set[str] = set()

    def push(self, state: str):
        self.storage.add(state)

    def pop(self, state: str):
        if state not in self.storage:
            raise ValueError("Given state not in storage")
        self.storage.remove(state)
        return True        

state_store = InMemoryStateStore()

class Authenticate:
    '''
    Verify performs the following tasks:
    1. Take identity + password, request password from dev, compare, boolean authentication
    2. . . .
    '''
    def __init__(self, creds: loginCredentials): 
        self.identity = creds.identity
        self.pwd =creds.pwd
        self.isUname = creds.isUname
        self.payload = {
                    'identity': self.identity 
                }

    async def is_authenticate(self) -> bool:
        '''
        Expected:
        {password : "hash"}: dict[str, str]
        The hash should be in strings and not bytes. We will handle it's encoding.
        '''

        password_body = await publish_ticket(
                TicketType(
                    id=uuid4(),
                    type= TicketEnum.FETCH_USER_CREDS_UNAME if self.isUname else TicketEnum.FETCH_USER_CREDS_EMAIL,
                    payload=Payload(
                        value=self.payload
                    )
                )
            )
        
        stored_pass = password_body['predicate'].encode('utf-8')

        is_authenticate = compare_password(self.pwd.get_secret_value(), stored_pass)

        return bool(is_authenticate)

class Register:
    '''
    We take a Register Payload and pack it in a ticket.
    This performs:
    Take data, send a insert ticket. 
    '''

    def __init__(self, payload: RegisterPayload):
        self.uname = payload.uname
        self.password = hash_password(payload.password.get_secret_value())
        self.mail = payload.mail
        self.name = payload.name
        self.dob = payload.dob
        self.addr = payload.addr
        self.payload: dict[str, Any] = payload.model_dump(exclude_none=True)
        
    async def register(self) -> None:
        await publish_ticket(
            TicketType(
                id=uuid4(),
                type= TicketEnum.REGISTER_USER,
                payload = Payload(
                    value=self.payload
                )
            )
        )

class Session:
    '''
    All session ops live here. They include:
    1. Session start (passes a session token to dev and returns it to user)
    2. Session destroy (sends a session token to dev so they can destory it)
    3. session validate (we would need this as a DI on the dev endpoint itself)
    4. Session destroy all (user must not be unique in the sessions table. A user can have multiple session from different addresses)
    5. Session cleanup (optional. Remove all expired sessions)
    '''

    def __init__(self):
        # self.allow_created_at = False
        # self.allow_expires_at = False
        # self.allow_session_id = False
        pass

    async def get_userId(self, payload: FetchPayloads) -> UUID:
        result = await publish_ticket(
            TicketType(
                id=uuid4(),
                type=TicketEnum.GET_USERID if payload.isUname else TicketEnum.GET_USERID_EMAIL,
                payload=Payload(
                    value={
                        "identity": payload.identity
                    }
                )
            )
        )
        return result['uid']

    # on hold.
    # TODO: read new_plans.md for the plan of universal configurer 
    # def configure(self, session_id: bool = False, created_at: bool = False, expires_at: bool = False):
    #     self.allow_created_at = created_at
    #     self.allow_expires_at = expires_at
    #     self.allow_session_id = session_id

    async def start(self, fetch_payload: FetchPayloads):
        '''
        Takes FetchPayload. The name got so sticky I am using it as a argument name.
        A fetch payload is a payload that consists of a identity and a isUname tag, helping understand if identity is a mail or uname.
        That felt like explaining a pop-culture reference, either way, moving on.

        From legacy versions:
        
            create session. 
            session has:
            1. id
            2. user_id
            3. token
            4. created_at
            5. expires_at
            # we have to decide the above here and send to ORM, there add an entry.
            out of those 5, some are created automatically. like id, created at, expires_at
            we need to set token.
            We also need to fetch user id which will refer to the user table.
            information relevant to this would be used relationally.
        
        The change in that plan is to simply, request for user_id ourselves from what is given. We will only take uname... or email. God I am so tired of there being email and uname.

        Note:
        Many can be defaults at source.
        We would only provide user_id and token by default
        Others can be requested via #TODO: configurer 
        '''

        uid = await self.get_userId(fetch_payload)

        await publish_ticket(
            TicketType(
                id = uuid4(),
                type=TicketEnum.CREATE_SESSION,
                payload=Payload(
                    value={
                        "uid": uid,
                        "token": uuid4()
                    }
                )
            )
        )


    async def destroy(self, token: UUID):
        await publish_ticket(
            TicketType(
                id=uuid4(),
                type=TicketEnum.DESTROY_TOKEN,
                payload=Payload(
                    value={
                        "token" : token
                    }
                )
            )
        )

    async def validate(self, token: UUID):
        return check_token(token)

    async def destroy_all(self, fetch_payload: FetchPayloads):
        uid = await self.get_userId(fetch_payload)

        await publish_ticket(
            TicketType(
                id= uuid4(),
                type= TicketEnum.DESTROY_ALL_USER_TOKEN,
                payload=Payload(
                    value={
                        "uid" : uid
                    }
                )
            )
        )

class Cadence:
    '''
    Verifier said it needed a name 
    Cadence: A OTP service

    Anyway, so what does a Verifier need:

    1. Get a email
    2. Generate the OTP.
    3. Hash it
    4. Store the OTP in persistence
    5. Send OTP to the given mail/phone-number/etc
    6. wait for user-entered OTP
    7. Compare hashes.
    '''

    def __init__(self, email: Mail):
        self.email = email

    def hash_it(self, code: str) -> str:
        digest = hashlib.sha256(
            code.encode()
        ).hexdigest()
        return digest

    async def issue(self):
        '''
        Provider is the service provider

        1. Receive email.
        2. Generate OTP.
        3. Hash OTP.
        4. Store hash + expiry + metadata.
        5. Send plaintext OTP to the email.
        6. Return "OTP issued."

        Just like tokens, otp also has an expiry and if now is greater than expiry you kill the token.
        THis is a persistence decision.
        '''
        code = randint(1000, 9999)
        digest = self.hash_it(str(code))

        # pass the digest to be stored in the DB
        await publish_ticket(
            TicketType(id=uuid4(),
            type=TicketEnum.STORE_OTP_DIGEST,
            payload=Payload(
                value={
                    "digest" : digest
                })
            )
        )

        await dispatch_ticket(
            CadenceTicket(
                id=uuid4(),
                payload=CadencePayload(
                    email=self.email,
                    code=str(code)
                )
                )
            )


    async def verify(self, payload: CadencePayload):
        '''
        1. Fetch stored OTP record.
        2. Check expiry.
        3. Hash submitted OTP.
        4. Compare hashes.
        5. If valid:
            - mark OTP as used
            - continue workflow
        6. Return success/failure.
        '''

        # scanning by email, can do it by id if felt required during testing
        result = await publish_ticket(
            TicketType(
                id=uuid4(),
                type=TicketEnum.FETCH_OTP_DIGEST,
                payload=Payload(
                    value={
                        "email" : payload.email
                    }
                )
            )
        )

        given_otp_digest = self.hash_it(payload.code)

        if given_otp_digest == result['otp']:
            # it is correct, send a correct flag back and delete the otp
            await publish_ticket(
                TicketType(
                    id=uuid4(),
                    type=TicketEnum.DESTROY_OTP_ENTRY,
                    payload=Payload(
                        value={
                            "email" : payload.email
                        }
                    )
                )
            )

            return True

        else:
            return False            

class Serenity:
    '''
    The OAuth handler. 
    Serenity would have a different decorator and a different bus, since Waltz is supporting limited context in OAuth.

    We will split it into three things:
    1. Authorization URL
    2. Exchange
    3. Verify
    4. _JWT helper
    '''
    def __init__(self):
        self.AUTHORIZATION_BASE_URLS = {
            "google": "https://accounts.google.com/o/oauth2/v2/auth",
            "microsoft": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize", # common for org and person microsoft accounts.
            "discord": "https://discord.com/oauth2/authorize",
            "github": "https://github.com/login/oauth/authorize",
            "linkedin": "https://www.linkedin.com/oauth/v2/authorization",
            "custom": "USER_VARIABLE" # dev enters their preferred URL here.
        }

        self.TOKEN_BASE_URLS = {
            "google": "https://oauth2.googleapis.com/token",
            "microsoft": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "discord": "https://discord.com/api/oauth2/token",
            "github": "https://github.com/login/oauth/access_token",
            "linkedin": "https://www.linkedin.com/oauth/v2/accessToken",
            "custom": "USER_VARIABLE"
        }

    def _fetch_creds(self, provider_name: ProviderName) -> Credentials:
        return bus.credentials(CredentialsTicket(
            id=uuid4(),
            provider=provider_name
        ))

    def _compose_url(self, provider_name: ProviderName, requestBody: AuthorizationRequest):

        return f"{self.AUTHORIZATION_BASE_URLS[provider_name]}?response_type={requestBody.response_type}&client_id={requestBody.client_id}&redirect_uri={requestBody.redirect_uri}&scope={requestBody.scope}&state={requestBody.state}"

    def request_authorization(self, provider_name: ProviderName):
        '''
        Deals with authorization endpoints.

        This is triggered by the endpoint itself.
        When the endpoint requests initiation for OAuth, authorization_url creates and passes a state string.
        '''
        # create a cryptographically random state:
        state = secrets.token_urlsafe(32)
        state_store.push(state)

        creds = self._fetch_creds(provider_name)

        scope = (
            ["openid", "email", "profile"] 
            if provider_name != "github" 
            else ["read:user", "user:email"]
        )

        return self._compose_url(
            provider_name, 
            AuthorizationRequest(
                client_id=creds.client_id,
                redirect_uri=creds.redirect_uri,
                scope=" ".join(scope),
                state=state,
            ))



    async def trade(self, payload: AuthorizationResponse):
        '''
        This AuthorizationResponse comes resolved into a Pydantic object from the endpoint itself: FastAPI's pydantic DI takes the type hint and resolves it with TypeAdapter internally.

        Tasks:
        1. Seperate ops for success and failure
        2. Success:
            1. take code and state. 
            2. Compare state and pop it.
            3. If response is False, raise Error
            4. If response is True, send code to API in the package and expect it to 
        '''
        if isinstance(payload, AuthorizationSuccess):
            state_store.pop(AuthorizationSuccess.state)
            creds = self._fetch_creds(payload.provider)
            authorization_code = AuthorizationSuccess.code
            
            request = TokenRequest(
                code=authorization_code,
                redirect_uri=creds.redirect_uri,
                client_id=creds.client_id
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=self.TOKEN_BASE_URLS[payload.provider],
                    headers={
                        "Content-Type" : "application/x-www-form-urlencoded",
                        "Accept" : "application/json" # NOTE: I am expecting response as json here
                    },
                    data=request.model_dump()
                )

                TokenResponse.model_validate(response.json())
                

        else:
            return payload.error

# class RequestToken(Serenity):

#     def _create_token(self, creds, )

#     def _google(self, creds: Credentials):
