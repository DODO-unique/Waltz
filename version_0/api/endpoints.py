from fastapi import APIRouter
from ..validators.endpoint_validators import LocalAuthPayload, WaltzResult
from ..validators.core_validator import LocalAuthRegistrationPayload
from ..core.idenity_service import IdentityService
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

    @waltz('/oauth')
    @waltz('/verify/email')
