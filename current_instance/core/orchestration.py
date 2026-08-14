from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from cadence import Cadence

from version_0.logging.logger import get_logger
logger = get_logger("core.orchestration")

logger.debug("core.orchestration module loaded")
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
    UserName,
)
from ..validators.endpoint_validators import (
    LocalAuthPayload,
    LogOutPayload,
    ValidationPayload,
    WaltzResult,
)


class Orchestra:
    def __init__(self):
        # NOTE: Any is for now. To be changed later
        self.id = uuid4()

        # NOTE: I could've initiated all sub function here itself but the ones not required would also be created and cause useless overhead

    async def local_registration(self, payload: LocalAuthRegistrationPayload):
        logger.debug("local_registration called payload=%s", payload)
        identity_service = IdentityService()

        token = await identity_service.register(payload)

        # .register() catches all errors itself
        logger.info("local_registration succeeded, token=%s", token)
        return WaltzResult(
            status="success",
            payload={
                "token" : token
            }
        )

    async def local_authenticate(self, payload: LocalAuthPayload):
        logger.debug("local_authenticate called for identity=%s", payload.identity)
        identity_service = IdentityService()

        result = await identity_service.authenticate(payload)

        if not result.value:
            logger.warning("local_authenticate failed for identity=%s result=%s", payload.identity, result)
            raise ValueError(result)

        # the user is authenticated at this point.
        # check if session exists and create one. the check would be done by _create itself.
        token = await self._create_session(identity=payload.identity)


        logger.info("local_authenticate succeeded for identity=%s token=%s", payload.identity, token)
        return WaltzResult(
            status='success',
            details={result.name : result.value}, # A: This feels unnecessary
            payload = {
                "token": token
            }
        )

    def oauth_authorization_request(self, provider: ProviderName):
        logger.debug("oauth_authorization_request called for provider=%s", provider)
        serenity = Serenity()
        category = serenity.get_provider_category(provider)
        url = serenity.get_request_url(provider, category)
        logger.info("oauth_authorization_request generated url for provider=%s", provider)
        return url

    async def initiate_trade(self, payload: AuthorizationResponse) -> WaltzResult:
        logger.debug("initiate_trade called payload=%s", payload)
        serenity = Serenity()
        trade_response = await serenity.trade(payload)
        if trade_response.token_response.id_token is None:
            # this is the oauth 2.0 access token category
            logger.debug("initiate_trade: oauth2 flow for provider=%s", trade_response.provider)
            result = await serenity.resource_request(ResourceRequestPayload(
                provider=trade_response.provider,
                access_token=trade_response.token_response.access_token
            ))  
            token = await self._oauth_registration(result)

            logger.info("initiate_trade completed via oauth2 for provider=%s token=%s", trade_response.provider, token)
            return WaltzResult(
                status="success",
                payload={
                    "token": token
                }
            )
            
        else:
            logger.debug("initiate_trade: oidc flow for provider=%s", trade_response.provider)
            jwk_request = JWKVerificationRequest(
                provider=payload.provider,
                id_token=trade_response.token_response.id_token,
                client_id=trade_response.client_id
            )
            token = await self._oidc_oauth_registration(jwk_request)

            logger.info("initiate_trade completed via oidc for provider=%s token=%s", trade_response.provider, token)
            return WaltzResult(
                status="success",
                payload={
                    "token": token
                }
            )


    async def _oauth_registration(self, payload: ResourceResponsePayload) -> UUID:
        logger.debug("_oauth_registration called for provider=%s", payload.provider)
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
            logger.error("_oauth_registration: Provider not supported: %s", payload.provider)
            raise ValueError("Provider not supported")

        result = await identity.authenticate(OAuthAuthPayload(
            sub=subject,
            updated_at=updated_at
        ))

        if result.value:
            token = await self._create_session(uid=subject)
            logger.info("_oauth_registration authenticated existing user subject=%s token=%s", subject, token)
            return token
        
        uid = await identity.register(registeration_data)
        token = await self._create_session(uid=uid)
        logger.info("_oauth_registration registered new user uid=%s token=%s", uid, token)
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
        logger.debug("_create_session called identity=%s uid=%s", identity, uid)
        if await validate(identity, uid):
            logger.error("_create_session: user exists identity=%s uid=%s", identity, uid)
            raise ValueError("User exists")
        token = await start(identity, uid)
        logger.info("_create_session created token=%s for uid=%s", token, uid)
        return token

    async def log_out(self, payload: LogOutPayload, all_accounts: bool = False):
        if all_accounts:
            await destroy_all(payload.identity)
            return WaltzResult(
                status="success"
            )
        await destroy(payload.token)

    async def initiate_email_validation(self, identity: IdentityPayload):
        mail = identity.email
        if mail is None:
            assert identity.uname is not None # IdentityPayload enforces either one to be not None locally
            mail = await self._get_mail(identity.uname)
        caddy = Cadence(email=mail)

        await caddy.issue()

    async def email_validation(self, payload: ValidationPayload):
        mail = payload.identity.email
        if mail is None:
            assert payload.identity.uname is not None # IdentityPayload enforces either one to be not None locally            
            mail = await self._get_mail(payload.identity.uname)
        caddy = Cadence(email=mail)

        predicate = await caddy.validate(payload.code)

        return WaltzResult(
            status="success",
            payload={
                "predicate" : predicate
            }
        )

    async def _get_mail(self, uname: UserName):
        identity = IdentityService()
        return await identity.get_email_by_uname(uname)
