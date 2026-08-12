from dataclasses import dataclass
from pydantic import AnyHttpUrl, BaseModel

@dataclass
class BaseOAuthProvider:
    token_api_url: AnyHttpUrl
    claim_api_url: AnyHttpUrl

@dataclass
class Discord(BaseOAuthProvider):
    request_scope: list[str] = 
    claim_package: DiscordClaimSchema
    