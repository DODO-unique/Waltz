from enums import AuthResultEnum, Enum, User
from general import get_id, publish_ticket
from ..security.hashing import compare_password

from ..validators.core_validator import (
    LocalAuthRegistrationPayload,
    OAuthAuthPayload,
    OAuthRegistration,
    TicketType,
    Uid,
)
from ..validators.endpoint_validators import LocalAuthPayload


class IdentityService:
    '''
    use it as: 
    Register(payload)
    '''

    def __init__(self):
        pass
        
    async def register(self, payload: OAuthRegistration | LocalAuthRegistrationPayload) -> Uid:
        '''
        This method catches errors itself and returns a Uid, no need to setup relevant measures in implementation
        '''
        try: 
            if isinstance(payload, OAuthRegistration):
                await publish_ticket(
                    TicketType(
                    type=User.RegisterUserOAuth,
                    payload=payload
                    )
                )

                return payload.id

            else:
                await publish_ticket(
                    TicketType(
                        type=User.RegisterUserLocal,
                        payload=payload
                    )
                )
        
                return payload.id
        except Exception as e:
            raise ValueError(e)

    async def authenticate(self, payload: OAuthAuthPayload | LocalAuthPayload) -> Enum:

        # get a uid as we always fetch by uid

        # FOR OAuth the uid is always string
        if isinstance(payload, OAuthAuthPayload):
            user: OAuthAuthPayload = await publish_ticket(
                TicketType(
                    type=User.GetUserOAuth,
                    payload=payload.sub
                )
            )

            if user.updated_at == payload.updated_at:
                return AuthResultEnum.SUCCESS
            else:
                # TODO: update_user is not set yet, raise a warning flag for it
                await self.update_user()
                return AuthResultEnum.SUCCESS


        # if either uid and id aren't string then OAuth is not involved
        else:
            uid = await get_id(payload.identity)

            # NOTE: wondering if I can directly use the sub from oauth

            # if uid is None then the user does not exist. So we return False as 'not authenticated'
            if uid is None:
                return AuthResultEnum.USER_NOT_FOUND
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

    async def update_user(self) -> None:
        pass
