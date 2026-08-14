import time
from dataclasses import dataclass

import httpx
import jwt
from jwt import PyJWK

from ..logging.logger import get_logger
from ..validators.core_validator import JWKSchema, JWKVerificationRequest, ProviderName

logger = get_logger("security.jwt_handler")

logger.debug("security.jwt_handler module loaded")


@dataclass
class CachedJWKS:
    '''
    jwks: {providerName: {kid: jwkschema}}
    '''
    jwks: dict[str, JWKSchema]
    expires_at: float = 0

    def add_jwk(self, kid: str, key: JWKSchema):
        self.jwks[kid] = key

jwk_cache: dict[ProviderName, CachedJWKS] = {}

PROVIDER_URLS = {
    "google" : "https://www.googleapis.com/oauth2/v3/certs",
    "microsoft" : "https://login.microsoftonline.com/common/discovery/v2.0/keys",
    "linkedin" : "https://www.linkedin.com/oauth/openid/jwks"
}

async def _get_key(provider: ProviderName):
    logger.debug("_get_key called for provider=%s", provider)
    if jwk_cache[provider].expires_at > time.time():
        # expired
        logger.info("JWK cache expired for provider=%s, resetting cache", provider)
        jwk_cache[provider] = CachedJWKS({}) # strong anti-pattern vibes here
    async with httpx.AsyncClient() as client:
        response = await client.get(PROVIDER_URLS[provider])

        keys = response.json()


        for key in keys["keys"]:
            key = JWKSchema.model_validate(key)
            if key.kid in jwk_cache[provider].jwks:
                logger.debug("Found existing jwk for kid=%s", key.kid)
                return jwk_cache[provider].jwks[key.kid]
            else:
                if provider not in jwk_cache:
                    jwk_cache[provider].expires_at = time.time() + 3600
                jwk_cache[provider].add_jwk(kid=key.kid, key=key)
                logger.debug("Added jwk for kid=%s", key.kid)
                return key

async def process_id_token(payload: JWKVerificationRequest):
    logger.debug("process_id_token called for provider=%s", payload.provider)
    jwkschema = await _get_key(payload.provider)
    if jwkschema is None:
        logger.error("No jwk schema returned for provider=%s", payload.provider)
        raise ValueError("NO key returned")
    key = PyJWK(jwkschema.model_dump())
    try:
        verified_claims = jwt.decode(
            jwt=payload.id_token,
            key=key,
            audience=payload.client_id,
            issuer=jwkschema.iss,
            algorithms=jwkschema.alg
        )
    except Exception:
        logger.exception("Failed to decode id_token for provider=%s", payload.provider)
        raise

    logger.debug("Successfully verified id_token for provider=%s", payload.provider)
    return verified_claims
            