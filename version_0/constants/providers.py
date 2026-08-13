from dataclasses import dataclass
from enum import Enum
from pydantic import AnyHttpUrl, BaseModel, EmailStr, HttpUrl

# ------------------------------------------------------------------
# 1. Base Dataclass Definition
# ------------------------------------------------------------------


@dataclass
class BaseOAuthProvider:
    token_api_url: AnyHttpUrl
    claim_api_url: AnyHttpUrl
    scope: list[str]
    claim: type[BaseModel]  # Pydantic BaseModel class for validation
    request_sugar: dict[str, str] | None = None


# ------------------------------------------------------------------
# 2. Discord Schemas and Instance
# ------------------------------------------------------------------


class DiscordClaimSchema(BaseModel):
    id: str
    username: str
    discriminator: str
    avatar: str | None = None
    email: EmailStr | None = None
    verified: bool | None = False


DiscordSchema = BaseOAuthProvider(
    token_api_url=AnyHttpUrl("https://discord.com/api/v10/oauth2/token"),
    claim_api_url=AnyHttpUrl("https://discord.com/api/v10/users/@me"),
    scope=["identify", "email"],
    claim=DiscordClaimSchema,
)


# ------------------------------------------------------------------
# 3. GitHub Schemas and Instance
# ------------------------------------------------------------------


class GitHubClaimSchema(BaseModel):
    id: int
    login: str
    name: str | None = None
    email: EmailStr | None = None
    avatar_url: HttpUrl | None = None


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