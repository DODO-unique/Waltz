from uuid import UUID
from idenity_service import IdentityService
from ..validators.endpoint_validators import WaltzResult
from session_manager import SessionManager

from uuid import uuid4
from typing import Any


class Orchestra:
    def __init__(self, payload: Any):
        # NOTE: Any is for now. To be changed later
        self.id = uuid4()
        self.payload = payload

        # NOTE: I could've initiated all sub function here itself but the ones not required would also be created and cause useless overhead

    async def local_authenticate(self):
        identity_service = IdentityService()

        result = await identity_service.authenticate(self.payload)

        if not result.value:
            raise ValueError("result")

        # the user is authenticated at this point.
        # check if session exists and create one. the check would be done by _create itself.
        self._create_session


        return WaltzResult(
            status='success',
            details={result.name : result.value}
        )

    async def _check_session(self):
        # check if session exists

    async def _create_session(self):
