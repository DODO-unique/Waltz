import time
from dataclasses import dataclass

import httpx
import jwt
from jwt import PyJWK

from ..validators.core_validator import JWKSchema, JWKVerificationRequest, ProviderName


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
    if jwk_cache[provider].expires_at > time.time():
        # expired
        jwk_cache[provider] = CachedJWKS({}) # strong anti-pattern vibes here
    async with httpx.AsyncClient() as client:
        response = await client.get(PROVIDER_URLS[provider])

        keys = response.json()


        for key in keys["keys"]:
            key = JWKSchema.model_validate(key)
            if key.kid in jwk_cache[provider].jwks:
                return jwk_cache[provider].jwks[key.kid]
            else:
                if provider not in jwk_cache:
                    jwk_cache[provider].expires_at = time.time() + 3600
                jwk_cache[provider].add_jwk(kid=key.kid, key=key)
                return key

async def process_id_token(payload: JWKVerificationRequest):
    jwkschema = await _get_key(payload.provider)
    if jwkschema is None:
        raise ValueError("NO key returned")
    key = PyJWK(jwkschema.model_dump())
    verified_claims = jwt.decode(
        jwt=payload.id_token,
        key=key,
        audience=payload.client_id,
        issuer=jwkschema.iss,
        algorithms=jwkschema.alg
    )

    return verified_claims
            