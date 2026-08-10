from enums import User
from general import compare_password, get_id, publish_ticket

from ..validators.core_validator import (
    BaseRegisterPayload,
    IdentityPayload,
    OAuth,
    TicketType,
    WaltzAuth,
)
from enums import AuthResultEnum, Enum


class IdentityService:
    '''
    use it as: 
    Register(payload)
    '''

    def __init__(self, payload: WaltzAuth | OAuth | BaseRegisterPayload | None = None):
        # NOTE: baseregisterpayload so if in Authentication OAuth payload does not contain any of the OAuth specifics
        self.payload = payload
        
    async def register(self) -> None:
        if self.payload is None:
            raise ValueError("Payload is empty")
        if isinstance(self.payload.id, str) and isinstance(self.payload, OAuth):
            await publish_ticket(
                TicketType(
                type=User.RegisterUserOAuth,
                payload=self.payload
                )
            )

        elif isinstance(self.payload, WaltzAuth):
            await publish_ticket(
                TicketType(
                    type=User.RegisterUserLocal,
                    payload=self.payload
                )
            )

        else:
            raise TypeError("Type or OAuth enum incorrect")

    async def authenticate(self) -> Enum:

        # check if payload is None (It can be None in certaincases so)
        if self.payload is None:
            raise ValueError("Payload is empty")

        # get a uid as we always fetch by uid
        uid = await get_id(IdentityPayload(
            uname=self.payload.uname,
            email=self.payload.mail,
        ))

        # if uid is None then the user does not exist. So we return False as 'not authenticated'
        if uid is None:
            return AuthResultEnum.USER_NOT_FOUND

        # FOR OAuth the uid is always string
        if isinstance(self.payload.id, str) and isinstance(uid, str):
            user: OAuth = await publish_ticket(
                TicketType(
                    type=User.GetUserOAuth,
                    payload=uid
                )
            )

            if isinstance(self.payload, OAuth):
                if user.updated_at == self.payload.updated_at:
                    return AuthResultEnum.SUCCESS
                else:
                    # TODO: update_user is not set yet, raise a warning flag for it
                    await self.update_user()
                    return AuthResultEnum.SUCCESS


        # if either uid and id aren't string then OAuth is not involved
        else:
            # checks if payload has password field
            if not isinstance(self.payload, WaltzAuth):
                raise TypeError("INTERNAL: Payload is not WaltzAuth and is not OAuth (or uid is not str)")
            # get bassword in string
            password_body: str = await publish_ticket(
                    TicketType(
                        type= User.GetUserLocal,
                        payload=uid
                    )
                )

            # convert to bytes
            stored_pass = password_body.encode('utf-8')
            # check and get a predicate
            is_authenticate = compare_password(self.payload.password.get_secret_value(), stored_pass)

            # return the predicate
            return AuthResultEnum.SUCCESS if is_authenticate else AuthResultEnum.NOT_AUTHENTIC

        return AuthResultEnum.MISC_NOT_AUTH

    async def update_user(self) -> None:
        pass
