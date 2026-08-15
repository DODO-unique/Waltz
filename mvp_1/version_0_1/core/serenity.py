import secrets
from uuid import uuid4

import httpx

from ..exceptions.waltz_exceptions import (
    OAuthNetworkException,
    OAuthProviderException,
    OAuthStateValidationException,
    UnsupportedProviderException,
)
from ..logging.logger import get_logger

logger = get_logger("core.serenity")

logger.debug("core.serenity module loaded")
from enums import ProviderCategory
from general import bus

from ..constants.providers import (
    DiscordSchema,
    GitHubSchema,
    OAuthProviders,
)
from ..validators.core_validator import (
    AnyHttpUrl,
    AuthorizationRequest,
    AuthorizationResponse,
    AuthorizationSuccess,
    Credentials,
    CredentialsTicket,
    ProviderName,
    ResourceRequestPayload,
    ResourceResponsePayload,
    TokenRequest,
    TokenResponse,
    TradeResponse,
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
            raise OAuthStateValidationException("Given state not in storage")
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

        self.POVIDER_CATEGORY: dict[str, list[ProviderName]] = {
            "OAuth 2.0" : ["discord", "github"],
            "OIDC" : ["google", "microsoft", "linkedin"]
        }

    def get_provider_category(self, provider: ProviderName):
        if provider in self.POVIDER_CATEGORY["OIDC"]:
            return ProviderCategory.OIDC
        else:
            return ProviderCategory.OAUTH

    def _fetch_creds(self, provider_name: ProviderName) -> Credentials:
        logger.debug("_fetch_creds called for provider=%s", provider_name)
        creds = bus.credentials(CredentialsTicket(
            id=uuid4(),
            provider=provider_name
        ))
        logger.debug("_fetch_creds returned creds for provider=%s", provider_name)
        return creds

    def _compose_url(self, provider_name: ProviderName, requestBody: AuthorizationRequest):

        return f"{self.AUTHORIZATION_BASE_URLS[provider_name]}?response_type={requestBody.response_type}&client_id={requestBody.client_id}&redirect_uri={requestBody.redirect_uri}&scope={requestBody.scope}&state={requestBody.state}"

    def get_request_url(self, provider_name: ProviderName, category: ProviderCategory) -> AnyHttpUrl:
        '''
        Deals with authorization endpoints.

        This is triggered by the endpoint itself.
        When the endpoint requests initiation for OAuth, authorization_url creates and passes a state string.
        '''
        logger.debug("get_request_url called provider=%s category=%s", provider_name, category)
        # create a cryptographically random state:
        state = secrets.token_urlsafe(32)
        state_store.push(state)

        creds = self._fetch_creds(provider_name)

        scope = (
            ["openid", "email", "profile"] 
            if provider_name != "github" 
            else ["read:user", "user:email"]
        )

        if category.value:
            scope = ["openid", "email", "profile"] 
        else:
            if provider_name == "discord":
                scope = DiscordSchema.scope
            elif provider_name == "github":
                scope = GitHubSchema.scope
            

        url = AnyHttpUrl(self._compose_url(
            provider_name, 
            AuthorizationRequest(
                client_id=creds.client_id,
                redirect_uri=creds.redirect_uri,
                scope=" ".join(scope),
                state=state,
            )))
        logger.info("Authorization request url composed for provider=%s", provider_name)
        return url



    async def trade(self, payload: AuthorizationResponse) -> TradeResponse:
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
            logger.debug("trade: AuthorizationSuccess received for provider=%s", payload.provider)
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

                    token_response = TokenResponse.model_validate(response.json())
                    logger.info("trade successful for provider=%s", payload.provider)
                    return TradeResponse(
                        provider=payload.provider,
                        client_id=creds.client_id,
                        token_response=token_response
                    )
                                         

                except httpx.HTTPStatusError as exc:
                    logger.exception("HTTPStatusError during trade for provider=%s", payload.provider)
                    raise OAuthProviderException(f"Error status {exc.response.status_code} returned by the OAuth provider ({exc.request.url}) during server-to-server trade")

                except httpx.RequestError as exc:
                    logger.exception("RequestError during trade for provider=%s", payload.provider)
                    raise OAuthNetworkException(f"A network error occured while requesting {exc.request.url}")

        else:
            logger.error("trade called with failure payload: %s", payload)
            raise OAuthProviderException(f"Error occuered: {payload.error}")

    
    async def resource_request(self, payload: ResourceRequestPayload):
        provider = OAuthProviders.NONE
        claims = None
        async with httpx.AsyncClient() as client:
            if payload.provider == "github":
                assert GitHubSchema.request_sugar is not None
                accept = GitHubSchema.request_sugar.get("accept")
                response = await client.get(f"{GitHubSchema.claim_api_url}", headers={
                    "Authorization" : f"Bearer {payload.access_token}",
                    "Accept" : f"{accept}"
                })
                provider = OAuthProviders.GITHUB
                claims = GitHubSchema.claim.model_validate(response.json())

            elif payload.provider == "discord":
                response = await client.get(f"{DiscordSchema.claim_api_url}", headers={
                    "Authorization" : f"Bearer {payload.access_token}"
                })
                provider = OAuthProviders.DISORD
                claims = DiscordSchema.claim.model_validate(response.json())
            else:
                raise UnsupportedProviderException("Provider not supported")

            return ResourceResponsePayload(
                provider=provider,
                claim_schema=claims
            )
