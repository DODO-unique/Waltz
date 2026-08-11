from uuid import UUID
from idenity_service import IdentityService
from serenity import Serenity
from ..validators.endpoint_validators import WaltzResult, LocalAuthPayload
from ..validators.core_validator import IdentityPayload, LocalAuthRegistrationPayload, ProviderName
from session_manager import start, destroy, check_token, validate

from uuid import uuid4


class Orchestra:
    def __init__(self):
        # NOTE: Any is for now. To be changed later
        self.id = uuid4()

        # NOTE: I could've initiated all sub function here itself but the ones not required would also be created and cause useless overhead

    async def local_registration(self, payload: LocalAuthRegistrationPayload):
        identity_service = IdentityService()

        token = await identity_service.register(payload)

        # .register() catches all errors itself
        return WaltzResult(
            status="success",
            payload={
                "token" : token
            }
        )

    async def local_authenticate(self, payload: LocalAuthPayload):
        identity_service = IdentityService()

        result = await identity_service.authenticate(payload)

        if not result.value:
            raise ValueError(result)

        # the user is authenticated at this point.
        # check if session exists and create one. the check would be done by _create itself.
        token = await self._create_session(identity=payload.identity)


        return WaltzResult(
            status='success',
            details={result.name : result.value}, # A: This feels unnecessary
            payload = {
                "token": token
            }
        )

    async def authorization_request(self, provider: ProviderName):
        serenity = Serenity()
        return serenity.request_authorization(provider)

    async def _check_session(self, identity: IdentityPayload):
        # check if session exists
        return await validate(identity=identity)

    async def _create_session(self, identity: IdentityPayload) -> UUID:
        if await validate(identity):
            raise ValueError("User Already exists") 
        return await start(identity)

