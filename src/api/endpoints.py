from fastapi import APIRouter

from mvp_1.core.orchestration import Orchestra
from mvp_1.log.logger import get_logger
from mvp_1.validators.core_validator import (
    AuthorizationResponse,
    IdentityPayload,
    LocalAuthRegistrationPayload,
    ProviderName,
)
from mvp_1.validators.endpoint_validators import (
    LocalAuthPayload,
    RequestByIdentity,
    RequestByMail,
    ValidationPayload,
    WaltzResult,
)

logger = get_logger("api.endpoints")

logger.debug("api.endpoints module loaded")



def routes(prefix: str):
    waltz = APIRouter(prefix=prefix)

    @waltz.get('/')
    def test():
        logger.debug("health check called")
        return {"Dev Message" : "You are connected"}

    
    @waltz.post('/local/authenticate')
    async def authenticate(payload: LocalAuthPayload) -> WaltzResult:
        logger.debug("endpoint /local/authenticate called payload=%s", payload)
        return await Orchestra().local_authenticate(payload)

    @waltz.post('/local/register')
    async def register(payload: LocalAuthRegistrationPayload):
        logger.debug("endpoint /local/register called payload=%s", payload)
        return await Orchestra().local_registration(payload)

    @waltz.get('/oauth/init')
    def initiate_oauth(payload: ProviderName):
        '''
        Returns authorization request
        '''
        logger.debug("endpoint /oauth/init called provider=%s", payload)
        return Orchestra().oauth_authorization_request(payload)
    
    @waltz.get('/oauth/authResponse') 
    async def auth_code(payload: AuthorizationResponse):
        logger.debug("endpoint /oauth/authResponse called payload=%s", payload)
        return await Orchestra().initiate_trade(payload)

    @waltz.post('/verify/email/sent')
    async def dispatch_mail(payload: RequestByMail | RequestByIdentity):
        logger.debug("endpoint /verify/email/sent called payload=%s", payload)
        orc = Orchestra()
        
        identity = IdentityPayload(uname=payload.uname) if isinstance(payload, RequestByIdentity) else IdentityPayload(email=payload.email)
        await orc.initiate_email_validation(identity)
        return WaltzResult(
            status="indetermined"
        )

    @waltz.post('/verify/email/validate')
    async def validate_mail(payload: ValidationPayload):
        logger.debug("endpoint /verify/email/validate called payload=%s", payload)
        orc = Orchestra()

        return await orc.email_validation(payload)
