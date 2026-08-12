from uuid import UUID
from datetime import datetime
from typing import Any

from idenity_service import IdentityService
from serenity import Serenity
from ..security.jwt_handler import process_id_token
from ..validators.endpoint_validators import WaltzResult, LocalAuthPayload
from ..validators.core_validator import (
    IdentityPayload,
    LocalAuthRegistrationPayload,
    OAuthRegistration,
    JWKVerificationRequest,
    ProviderName,
)
from session_manager import start, destroy, check_token, validate

from uuid import uuid4


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

    async def authorization_request(self, provider: ProviderName):
        serenity = Serenity()
        return serenity.request_authorization(provider)

    async def oauth_registration(self, payload: JWKVerificationRequest):
        verified_claims = await process_id_token(payload)
        oauth_payload = self._oauth_registration_from_verified_claims(verified_claims)

        identity_service = IdentityService()
        token = await identity_service.register(oauth_payload)

        return WaltzResult(
            status="success",
            payload={"token": token}
        )

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise ValueError("Cannot parse datetime from OIDC claim")

    def _oauth_registration_from_verified_claims(self, verified_claims: dict[str, Any]) -> OAuthRegistration:
        subject = verified_claims.get("sub")
        if subject is None:
            raise ValueError("OIDC id_token missing required 'sub' claim")

        identity = IdentityPayload(
            email=verified_claims.get("email"),
            uname=verified_claims.get("preferred_username") or verified_claims.get("nickname"),
        )

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

    async def _check_session(self, identity: IdentityPayload):
        # check if session exists
        return await validate(identity=identity)

    async def _create_session(self, identity: IdentityPayload) -> UUID:
        if await validate(identity):
            raise ValueError("User Already exists") 
        return await start(identity)

