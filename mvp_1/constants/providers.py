from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)
from mvp_1.log.logger import get_logger

logger = get_logger("constants.providers")

logger.debug("constants.providers module loaded")

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

    @field_validator("avatar_hash", mode="before")
    @classmethod
    def transform_avatar_hash_to_url(cls, v: Any, info: ValidationInfo) -> str | None:
        logger.debug("transform_avatar_hash_to_url called for v=%s", v)
        if isinstance(v, str) and v.startswith("http"):
            return v
        if v is None:
            return v
        data = info.data if hasattr(info, "data") else {}
        user_id = data.get("id")
        ext = "gif" if v.startswith("a_") else "png"
        url = f"https://cdn.discordapp.com/avatars/{user_id}/{v}.{ext}"
        logger.debug("Transformed avatar hash to url=%s", url)
        return url


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
        logger.debug("convert_id_to_string called with v=%s", v)
        s = str(v)
        logger.debug("Converted id to string=%s", s)
        return s


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