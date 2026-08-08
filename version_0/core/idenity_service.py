from ..validators.core_validator import WaltzAuth, OAuth, BaseRegisterPayload, TicketType, IdentityPayload
from enums import User
from general import publish_ticket, get_id, compare_password


class IdentityService:
    '''
    use it as: 
    Register(payload, isOAuth)
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

    async def authenticate(self) -> bool:
        '''
        first get_id
        '''
        if self.payload is None:
            raise ValueError("Payload is empty")

        uid = await get_id(IdentityPayload(
            uname=self.payload.uname,
            email=self.payload.mail,
        ))

        if uid is None:
            return False

        if isinstance(self.payload.id, str) and isinstance(uid, str):
            user: OAuth = await publish_ticket(
                TicketType(
                    type=User.GetUserOAuth,
                    payload=uid
                )
            )

            if isinstance(self.payload, OAuth):
                if user.updated_at == self.payload.updated_at:
                    return True
                else:
                    await self.update_user()
                    return True


        else:
            if not isinstance(self.payload, WaltzAuth):
                raise TypeError("INTERNAL: Payload is not WaltzAuth and is not OAuth (or uid is not str)")
            password_body: str = await publish_ticket(
                    TicketType(
                        type= User.GetUserLocal,
                        payload=uid
                    )
                )
            
            stored_pass = password_body.encode('utf-8')
            is_authenticate = compare_password(self.payload.password.get_secret_value(), stored_pass)

            return bool(is_authenticate)

        return False

    async def update_user(self) -> None:
        pass
