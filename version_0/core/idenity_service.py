from enums import AuthResultEnum, Enum, User
from general import compare_password, get_id, publish_ticket

from ..validators.core_validator import (
    BaseRegisterPayload,
    IdentityPayload,
    OAuth,
    TicketType,
    WaltzAuth,
)
from ..validators.endpoint_validators import (
    LocalAuthPayload
)


class IdentityService:
    '''
    use it as: 
    Register(payload)
    '''

    def __init__(self):
        pass
        
    async def register(self, payload: OAuth | WaltzAuth) -> None:
        if isinstance(payload, OAuth):
            await publish_ticket(
                TicketType(
                type=User.RegisterUserOAuth,
                payload=payload
                )
            )

        else:
            await publish_ticket(
                TicketType(
                    type=User.RegisterUserLocal,
                    payload=payload
                )
            )

        
        raise TypeError("Type or OAuth enum incorrect")

    async def authenticate(self, payload: OAuth | LocalAuthPayload) -> Enum:

        # check if payload is None (It can be None in certaincases so)
        if payload is None:
            raise ValueError("Payload is empty")

        # get a uid as we always fetch by uid
        uid = await get_id(IdentityPayload(
            uname=payload.uname,
            email=payload.mail,
        ))

        # if uid is None then the user does not exist. So we return False as 'not authenticated'
        if uid is None:
            return AuthResultEnum.USER_NOT_FOUND

        # FOR OAuth the uid is always string
        if isinstance(uid, str):
            user: OAuth = await publish_ticket(
                TicketType(
                    type=User.GetUserOAuth,
                    payload=uid
                )
            )

            if isinstance(payload, OAuth):
                if user.updated_at == payload.updated_at:
                    return AuthResultEnum.SUCCESS
                else:
                    # TODO: update_user is not set yet, raise a warning flag for it
                    await self.update_user()
                    return AuthResultEnum.SUCCESS


        # if either uid and id aren't string then OAuth is not involved
        else:
            # checks if payload has password field
            if not isinstance(payload, WaltzAuth):
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
            is_authenticate = compare_password(payload.password.get_secret_value(), stored_pass)

            # return the predicate
            return AuthResultEnum.SUCCESS if is_authenticate else AuthResultEnum.NOT_AUTHENTIC

        return AuthResultEnum.MISC_NOT_AUTH

    async def update_user(self) -> None:
        pass
