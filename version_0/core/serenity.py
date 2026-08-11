import secrets
from uuid import uuid4

import httpx
from general import bus

from ..validators.core_validator import (
    AuthorizationRequest,
    AuthorizationResponse,
    AuthorizationSuccess,
    Credentials,
    CredentialsTicket,
    ProviderName,
    TokenRequest,
    TokenResponse,
)


class InMemoryStateStore:
    '''
    A set for storing OAuth state temporarily to prevent state.
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
            raise TypeError(f"Error occuered: {payload.error}")
