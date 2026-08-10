from fastapi import APIRouter
from ..validators.endpoint_validators import LocalAuthPayload, WaltzResult
from ..core.idenity_service import IdentityService

def routes(prefix: str):
    waltz = APIRouter(prefix=prefix)

    @waltz.get('/')
    def test():
        return {"Success" : "Hello World!"}

    
    @waltz.post('/local/authenticate')
    async def authenticate(payload: LocalAuthPayload):
        identity_service = IdentityService()

        result = await identity_service.authenticate(payload)

        if not result.value:
            raise ValueError("result")

        return WaltzResult(
            status='success',
            details={result.name : result.value}
        )

    @waltz('/oauth')
    @waltz('/verify/email')
