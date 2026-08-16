import time
from dataclasses import dataclass

import httpx
import jwt
from jwt import PyJWK
from version_0_1.exceptions.waltz_exceptions import JWTKeyMissingException
from version_0_1.log.logger import get_logger
from version_0_1.validators.core_validator import (
    JWKSchema,
    JWKSetSchema,
    JWKVerificationRequest,
    ProviderName,
)

logger = get_logger("security.jwt_handler")

logger.debug("security.jwt_handler module loaded")


@dataclass
class CachedJWK:
    jwk: JWKSchema
    expiry: float

jwk_cache: dict[str, CachedJWK] = {}

OIDC_CONFIG = {
    "google": {
        "iss": "https://accounts.google.com",
        "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
    },
    "microsoft": {
        "iss": "https://login.microsoftonline.com/common/v2.0",
        "jwks_uri": "https://login.microsoftonline.com/common/discovery/v2.0/keys",
    },
    "linkedin": {
        "iss": "https://www.linkedin.com/oauth",
        "jwks_uri": "https://www.linkedin.com/oauth/openid/jwks",
    },
}

async def _get_key(provider: ProviderName, token_header_kid: str) -> JWKSchema | None:
    logger.debug("_get_key called for provider=%s", provider)

    if token_header_kid in jwk_cache:
        return jwk_cache[token_header_kid].jwk


    async with httpx.AsyncClient() as client:
        response = await client.get(OIDC_CONFIG[provider]["jwks_uri"])
        formal_key: JWKSchema | None = None

        keys = response.json()
        # keys is a package of keys.
        keys = JWKSetSchema.model_validate(keys)
        kid_key_dict = keys.lookup_dict()

        if token_header_kid in kid_key_dict:
            formal_key = kid_key_dict[token_header_kid]
            
        # updating the cache
        for kid, key in kid_key_dict.items():
            """If control comes here, then token_header_kid is definitely not in jwk_cache"""

            if kid not in jwk_cache:
                # if kid is not in jwk_cache, add it
                # add kid-key pair to cache. Five minute time default
                jwk_cache[kid] = CachedJWK(jwk=key, expiry=time.time() + (5*60))
                continue
            # check if expired
            if jwk_cache[kid].expiry < time.time():
                # if expired, delete entry
                logger.debug("Expired kid in cache. Destorying entry")
                del jwk_cache[kid]
        
        return formal_key

async def process_id_token(payload: JWKVerificationRequest):
    logger.debug("process_id_token called for provider=%s", payload.provider)

    header = jwt.get_unverified_header(payload.id_token)
    kid = header["kid"]

    jwkschema = await _get_key(payload.provider, token_header_kid=kid)

    if jwkschema is None:
        logger.error("No jwk schema returned for provider=%s", payload.provider)
        raise JWTKeyMissingException("NO key returned")
    
    key = PyJWK(jwkschema.model_dump())

    try:
        verified_claims = jwt.decode(
            jwt=payload.id_token,
            key=key,
            audience=payload.client_id,
            issuer=OIDC_CONFIG[payload.provider]["iss"],
            algorithms=jwkschema.alg
        )
    except Exception:
        logger.exception("Failed to decode id_token for provider=%s", payload.provider)
        raise

    logger.debug("Successfully verified id_token for provider=%s", payload.provider)
    return verified_claims
            
