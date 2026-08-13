from fastapi import APIRouter
from ..validators.endpoint_validators import LocalAuthPayload, WaltzResult, RequestByIdentity, RequestByMail
from ..validators.core_validator import LocalAuthRegistrationPayload, ProviderName, AuthorizationResponse, IdentityPayload
from ..core.orchestration import Orchestra

def routes(prefix: str):
    waltz = APIRouter(prefix=prefix)

    @waltz.get('/')
    def test():
        return {"Dev Message" : "You are connected"}

    
    @waltz.post('/local/authenticate')
    async def authenticate(payload: LocalAuthPayload) -> WaltzResult:
        return await Orchestra().local_authenticate(payload)

    @waltz.post('/local/register')
    async def register(payload: LocalAuthRegistrationPayload):
        return await Orchestra().local_registration(payload)

    @waltz.get('/oauth/init')
    def initiate_oauth(payload: ProviderName):
        '''
        Returns authorization request
        '''
        return Orchestra().oauth_authorization_request(payload)
    
    @waltz.post('/oauth/authResponse') 
    async def auth_code(payload: AuthorizationResponse):
        return await Orchestra().initiate_trade(payload)

    @waltz('/verify/email')
    async def dispatch_mail(payload: RequestByMail | RequestByIdentity):
        orc = Orchestra()
        if isinstance(payload, RequestByIdentity):
            identity = IdentityPayload(
                uname=payload.uname
            )
            orc.initiate_email_validation(identity)
            return WaltzResult(
                status="indetermined"
            )
        else:
            identity = IdentityPayload(
                email=payload.email
            )
            orc.initiate_email_validation(identity)
