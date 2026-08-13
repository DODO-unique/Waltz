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

    @waltz.post('/verify/email/sent')
    async def dispatch_mail(payload: RequestByMail | RequestByIdentity):
        orc = Orchestra()
        
        identity = IdentityPayload(uname=payload.uname) if isinstance(payload, RequestByIdentity) else IdentityPayload(email=payload.email)
        await orc.initiate_email_validation(identity)
        return WaltzResult(
            status="indetermined"
        )

    @waltz.post('/verify/email/validate')
    async def validate_mail(payload: ValidationPayload):
        orc = Orchestra()

        return await orc.email_validation(payload)
