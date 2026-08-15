'''
Note that all names here would not reflect internal naming heirarchy (like Serenity, Cadence) and would reflect the purpose.
The classnames should reflect purpose and be practical.
'''


from pydantic import AnyHttpUrl, BaseModel

from master_validator import CadenceOperator, DatabaseRegistry
from validation_helper import ProviderName


class OAuthCredentials(BaseModel):
    client_id : str
    client_secret : str | None

    def with_provider_defaults(self, provider: ProviderName, uri: AnyHttpUrl) -> "Credentials":
        return Credentials(
            redirect_uri= uri,
            provider=provider,
            **self.model_dump()
        )



'''
The following are semi-internal schemas for the Bus. 
'''

class Credentials(OAuthCredentials):
    redirect_uri : AnyHttpUrl
    provider : ProviderName

class Registry(BaseModel):
    database : set[DatabaseRegistry]
    cadence : CadenceOperator | None
    serenity : set[Credentials]