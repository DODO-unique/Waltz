from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from idenity_service import IdentityService
from serenity import Serenity
from session_manager import destroy, destroy_all, start, validate

from ..constants.providers import DiscordClaimSchema, GitHubClaimSchema
from ..security.jwt_handler import process_id_token
from ..validators.core_validator import (
    AuthorizationResponse,
    IdentityPayload,
    JWKVerificationRequest,
    LocalAuthRegistrationPayload,
    OAuthAuthPayload,
    OAuthRegistration,
    ProviderName,
    ResourceRequestPayload,
    ResourceResponsePayload,
    Uid,
)
from ..validators.endpoint_validators import (
    LocalAuthPayload,
    LogOutPayload,
    WaltzResult,
)


class Orchestra:
    def __init__(self):
        # NOTE: Any is for now. To be changed later
        self.id = uuid4()

        # NOTE: I could've initiated all sub function here itself but the ones not required would also be created and cause useless overhead

    async def local_registration(self, payload: LocalAuthRegistrationPayload):
        identity_service = IdentityService()

        token = await identity_service.register(payload)

        # .register() catches all errors itself
        return WaltzResult(
            status="success",
            payload={
                "token" : token
            }
        )

    async def local_authenticate(self, payload: LocalAuthPayload):
        identity_service = IdentityService()

        result = await identity_service.authenticate(payload)

        if not result.value:
            raise ValueError(result)

        # the user is authenticated at this point.
        # check if session exists and create one. the check would be done by _create itself.
        token = await self._create_session(identity=payload.identity)


        return WaltzResult(
            status='success',
            details={result.name : result.value}, # A: This feels unnecessary
            payload = {
                "token": token
            }
        )

    def oauth_authorization_request(self, provider: ProviderName):
        serenity = Serenity()
        category = serenity.get_provider_category(provider)
        return serenity.get_request_url(provider, category)

    async def initiate_trade(self, payload: AuthorizationResponse) -> WaltzResult:
        serenity = Serenity()
        trade_response = await serenity.trade(payload)
        if trade_response.token_response.id_token is None:
            # this is the oauth 2.0 access token category
            result = await serenity.resource_request(ResourceRequestPayload(
                provider=trade_response.provider,
                access_token=trade_response.token_response.access_token
            ))  
            token = await self._oauth_registration(result)

            return WaltzResult(
                status="success",
                payload={
                    "token": token
                }
            )
            
        else:
            jwk_request = JWKVerificationRequest(
                provider=payload.provider,
                id_token=trade_response.token_response.id_token,
                client_id=trade_response.client_id
            )
            token = await self._oidc_oauth_registration(jwk_request)

            return WaltzResult(
                status="success",
                payload={
                    "token": token
                }
            )


    async def _oauth_registration(self, payload: ResourceResponsePayload) -> UUID:
        identity = IdentityService()
        if payload.provider.value == 1 and isinstance(payload.claim_schema, GitHubClaimSchema): #github
            claims = payload.claim_schema
            subject = claims.id
            updated_at = claims.updated_at
            registeration_data = OAuthRegistration(
                id=claims.id,
                name=claims.name,
                identity=IdentityPayload(
                    uname=claims.login,
                    email= claims.email
                ),
                picture=claims.avatar_url,
                updated_at=claims.updated_at
            )

        elif payload.provider.value == 2 and isinstance(payload.claim_schema, DiscordClaimSchema):
            claims = payload.claim_schema
            subject = claims.id
            updated_at = claims.updated_at

            registeration_data = OAuthRegistration(
                id=subject,
                identity=IdentityPayload(
                    uname=claims.username,
                    email=claims.email,
                ),
                picture=claims.avatar_hash,
                updated_at=updated_at
            )
        else:
            raise ValueError("Provider not supported")

        result = await identity.authenticate(OAuthAuthPayload(
            sub=subject,
            updated_at=updated_at
        ))

        if result.value:
            token = await self._create_session(uid=subject)
            return token
        
        uid = await identity.register(registeration_data)
        token = await self._create_session(uid=uid)
        return token


    def _oauth_registration_from_verified_claims(self, verified_claims: dict[str, Any]) -> OAuthRegistration:
        # get here is dramatically better because it returns None if the key is not found.
        subject = verified_claims.get("sub")
        if subject is None:
            raise ValueError("OIDC id_token missing required 'sub' claim")

        identity = IdentityPayload(
            email=verified_claims.get("email"),
            uname=verified_claims.get("preferred_username") or verified_claims.get("nickname"),
        )

        # iat is issued time. Unix timestamp
        updated_at_claim = verified_claims.get("updated_at") or verified_claims.get("iat")
        updated_at = self._parse_datetime(updated_at_claim)
        if updated_at is None:
            raise ValueError("OIDC id_token must contain 'updated_at' or 'iat' claim")

        return OAuthRegistration(
            id=subject,
            name=verified_claims.get("name"),
            identity=identity,
            gender=verified_claims.get("gender"),
            birthdate=verified_claims.get("birthdate"),
            addr=None,
            picture=verified_claims.get("picture"),
            profile=verified_claims.get("profile"),
            website=verified_claims.get("website"),
            zoneinfo=verified_claims.get("zoneinfo"),
            locale=verified_claims.get("locale"),
            updated_at=updated_at,
        )



    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            # OIDC claims don't pass iso format strings but still.
            return datetime.fromisoformat(value)
        raise ValueError("Cannot parse datetime from OIDC claim")


    async def _oidc_oauth_registration(self, payload: JWKVerificationRequest) -> UUID:
        '''
        Returns a session token
        '''
        verified_claims = await process_id_token(payload)
        oauth_payload = self._oauth_registration_from_verified_claims(verified_claims)

        identity_service = IdentityService()
        # check if user exists
        if not isinstance(oauth_payload.id, str):
            raise TypeError("OAuth payload is not sting.")
        result = await identity_service.authenticate(OAuthAuthPayload(sub=oauth_payload.id, updated_at=oauth_payload.updated_at))
        if result.value:
            # it is there already. Create a session here.
            token = await self._create_session(uid=oauth_payload.id)
            return token
        # register if not there
        uid = await identity_service.register(oauth_payload)
        token = await self._create_session(uid=uid)
        return token

    # async def _check_session(self, identity: IdentityPayload):
    #     # check if session exists
    #     return await validate(identity=identity)

    async def _create_session(self, identity: IdentityPayload | None = None, uid: Uid | None = None) -> UUID:
        if await validate(identity, uid):
            raise ValueError("User exists")
        return await start(identity, uid)

