import hashlib
import secrets
from random import randint
from uuid import UUID, uuid4

import bcrypt
import httpx

from client_schemas import Credentials
from concrete.ticket_handler import TicketBus
from master_validator import (
    AuthorizationRequest,
    AuthorizationResponse,
    BaseRegisterPayload,
    CadencePayload,
    CadenceTicket,
    CredentialsTicket,
    IdentityPayload,
    OAuth,
    SessionRequest,
    TicketType,
    TokenRequest,
    TokenResponse,
    Uid,
    WaltzAuth,
)
from ticket_enum import OneTimePassword, Session, User
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


async def get_id(identity: IdentityPayload) -> Uid | None:
    '''
    use identity to get_id
    '''
    return await publish_ticket(
        TicketType(
        type=User.GetID,
        payload=identity)
    )
        

class IdentityService:
    '''
    use it as: 
    Register(payload, isOAuth)
    '''

    def __init__(self, payload: WaltzAuth | OAuth | BaseRegisterPayload | None = None):
        # NOTE: baseregisterpayload so if in Authentication OAuth payload does not contain any of the OAuth specifics
        self.payload = payload
        
    async def register(self) -> None:
        if self.payload is None:
            raise ValueError("Payload is empty")
        if isinstance(self.payload.id, str) and isinstance(self.payload, OAuth):
            await publish_ticket(
                TicketType(
                type=User.RegisterUserOAuth,
                payload=self.payload
                )
            )

        elif isinstance(self.payload, WaltzAuth):
            await publish_ticket(
                TicketType(
                    type=User.RegisterUserLocal,
                    payload=self.payload
                )
            )

        else:
            raise TypeError("Type or OAuth enum incorrect")

    async def authenticate(self) -> bool:
        '''
        first get_id
        '''
        if self.payload is None:
            raise ValueError("Payload is empty")

        uid = await get_id(IdentityPayload(
            uname=self.payload.uname,
            email=self.payload.mail,
        ))

        if uid is None:
            return False

        if isinstance(self.payload.id, str) and isinstance(uid, str):
            user: OAuth = await publish_ticket(
                TicketType(
                    type=User.GetUserOAuth,
                    payload=uid
                )
            )

            if isinstance(self.payload, OAuth):
                if user.updated_at == self.payload.updated_at:
                    return True
                else:
                    await self.update_user()
                    return True


        else:
            if not isinstance(self.payload, WaltzAuth):
                raise TypeError("INTERNAL: Payload is not WaltzAuth and is not OAuth (or uid is not str)")
            password_body: str = await publish_ticket(
                    TicketType(
                        type= User.GetUserLocal,
                        payload=uid
                    )
                )
            
            stored_pass = password_body.encode('utf-8')
            is_authenticate = compare_password(self.payload.password.get_secret_value(), stored_pass)

            return bool(is_authenticate)

        return False

    async def update_user(self) -> None:
        pass

class SessionManager:
    '''
    All session ops live here. They include:
    1. Session start (passes a session token to dev and returns it to user)
    2. Session destroy (sends a session token to dev so they can destory it)
    3. session validate (we would need this as a DI on the dev endpoint itself)
    4. Session destroy all (user must not be unique in the sessions table. A user can have multiple session from different addresses)
    5. Session cleanup (optional. Remove all expired sessions)
    '''

    def __init__(self):
        pass

    async def start(self, identity: IdentityPayload):

        uid = await get_id(identity)
        if uid is None:
            raise ValueError("No user found")
        await publish_ticket(
            TicketType(
                type=Session.Create,
                payload=SessionRequest(
                    Uid=uid
                )
            )
        )


    async def destroy(self, token: UUID):
        await publish_ticket(
            TicketType(
                id=uuid4(),
                type=Session.Delete,
                payload=SessionRequest(token=token)
            )
        )

    async def check_token(self, token: UUID) -> bool:
        predicate = await publish_ticket(
            TicketType(
                id=uuid4(),
                type=Session.Check,
                payload=SessionRequest(token=token)
            )
        )

        return predicate

    async def validate(self, token: UUID):
        return self.check_token(token)

    async def destroy_all(self, identiy: IdentityPayload):
        uid = await get_id(identity=identiy)

        await publish_ticket(
            TicketType(
                type= Session.Delete,
                payload=SessionRequest(Uid=uid)
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
            type=OneTimePassword.Store,
            payload= digest
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

        uid = await get_id(IdentityPayload(email=self.email))
        if uid is None:
            raise ValueError("No user found")
        result: str | None = await publish_ticket(
            TicketType(
                type=OneTimePassword.Get,
                payload=uid
            )
        )

        given_otp_digest = self.hash_it(payload.code)

        if given_otp_digest == result:
            # it is correct, send a correct flag back and delete the otp
            await publish_ticket(
                TicketType(
                    type=OneTimePassword.DeleteOTP,
                    payload=uid
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
                try:                
                    response = await client.post(
                        url=self.TOKEN_BASE_URLS[payload.provider],
                        headers={
                            "Content-Type" : "application/x-www-form-urlencoded",
                            "Accept" : "application/json" # NOTE: I am expecting response as json here
                        },
                        data=request.model_dump()
                    )

                    response.raise_for_status()

                    return TokenResponse.model_validate(response.json())

                except httpx.HTTPStatusError as exc:
                    raise ValueError(f"Error status {exc.response.status_code} returned by the OAuth provider ({exc.request.url}) during server-to-server trade")

                except httpx.RequestError as exc:
                    raise ValueError(f"A network error occured while requesting {exc.request.url}")

        else:
            return payload.error

# class RequestToken(Serenity):

#     def _create_token(self, creds, )

#     def _google(self, creds: Credentials):
