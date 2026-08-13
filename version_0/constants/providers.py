from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, ValidationInfo

# -----------------------------------------------------------------
# 0. Claim Schemas
# -----------------------------------------------------------------

class ClaimSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

class DiscordClaimSchema(ClaimSchema):
    id: str
    username: str
    discriminator: str
    avatar_hash: AnyHttpUrl | None = None
    email: EmailStr | None = None
    verified: bool | None = False
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class GitHubClaimSchema(ClaimSchema):
    id: str
    login: str
    name: str | None = None
    email: EmailStr | None = None
    avatar_url: AnyHttpUrl | None = None
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_string(cls, v:int | str) -> str:
        return str(v)


# ------------------------------------------------------------------
# 1. Base Dataclass Definition
# ------------------------------------------------------------------


@dataclass
class BaseOAuthProvider:
    token_api_url: AnyHttpUrl
    claim_api_url: AnyHttpUrl
    scope: list[str]
    claim: type[GitHubClaimSchema | DiscordClaimSchema] # Pydantic BaseModel class for validation
    request_sugar: dict[str, str] | None = None


# ------------------------------------------------------------------
# 2. Discord Instance
# ------------------------------------------------------------------




DiscordSchema = BaseOAuthProvider(
    token_api_url=AnyHttpUrl("https://discord.com/api/v10/oauth2/token"),
    claim_api_url=AnyHttpUrl("https://discord.com/api/v10/users/@me"),
    scope=["identify", "email"],
    claim=DiscordClaimSchema,
)


# ------------------------------------------------------------------
# 3. GitHub Instance
# ------------------------------------------------------------------



GitHubSchema = BaseOAuthProvider(
    token_api_url=AnyHttpUrl("https://github.com/login/oauth/access_token"),
    claim_api_url=AnyHttpUrl("https://api.github.com/user"),
    scope=["read:user", "user:email"],
    claim=GitHubClaimSchema,
    request_sugar={
        "accept" : "application/vnd.github+json"
    }
)

class OAuthProviders(Enum):
    NONE = 0
    GITHUB = 1
    DISORD = 2