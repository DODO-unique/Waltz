from mvp_1.core.enums import AuthResultEnum, Enum, User
from mvp_1.exceptions.waltz_exceptions import (
    DataIntegrityException,
    UserNotFoundException,
)
from mvp_1.log.logger import get_logger

logger = get_logger("core.idenity_service")

logger.debug("core.idenity_service module loaded")
from mvp_1.core.general import get_id, publish_ticket
from mvp_1.security.hashing import compare_password
from mvp_1.validators.core_validator import (
    IdentityPayload,
    LocalAuthRegistrationPayload,
    Mail,
    OAuthAuthPayload,
    OAuthRegistration,
    TicketType,
    Uid,
    UserName,
)
from mvp_1.validators.endpoint_validators import LocalAuthPayload


class IdentityService:
    '''
    use it as: 
    Register(payload)
    '''

    def __init__(self):
        pass
        
    async def register(self, payload: OAuthRegistration | LocalAuthRegistrationPayload) -> Uid:
        '''
        This method catches errors itself and returns a Uid, no need to setup relevant measures in implementation.
        Though I wish it didn't do that. We can just pass a 'None' and let the receiver filter between uid and None
        '''
        logger.debug("register called payload=%s", payload)
        try: 
            if isinstance(payload, OAuthRegistration):
                await publish_ticket(
                    TicketType(
                    type=User.RegisterUserOAuth,
                    payload=payload
                    )
                )

                logger.info("Registered OAuth user id=%s", payload.id)
                return payload.id

            else:
                await publish_ticket(
                    TicketType(
                        type=User.RegisterUserLocal,
                        payload=payload
                    )
                )
        
                logger.info("Registered local user id=%s", payload.id)
                return payload.id
        except Exception as e:
            logger.exception("Exception during register for payload=%s", payload)
            raise DataIntegrityException(str(e), cause=e) from e

    async def authenticate(self, payload: OAuthAuthPayload | LocalAuthPayload) -> Enum:
        logger.debug("authenticate called payload=%s", payload)
        # get a uid as we always fetch by uid

        # FOR OAuth the uid is always string
        if isinstance(payload, OAuthAuthPayload):
            user: OAuthRegistration | None = await publish_ticket(
                TicketType(
                    type=User.GetUserOAuth,
                    payload=payload.sub
                )
            )

            if user is None:
                logger.info("authenticate: OAuth user not found sub=%s", payload.sub)
                return AuthResultEnum.USER_NOT_FOUND

            if user.updated_at == payload.updated_at:
                logger.debug("authenticate: OAuth user up-to-date sub=%s", payload.sub)
                return AuthResultEnum.SUCCESS
            else:
                # TODO: update_user is not set yet, raise a warning flag for it
                logger.info("authenticate: OAuth user exists but outdated, updating sub=%s", payload.sub)
                await self.update_user()
                return AuthResultEnum.SUCCESS


        # if either uid and id aren't string then OAuth is not involved
        else:
            uid = await get_id(payload.identity)

            # NOTE: wondering if I can directly use the sub from oauth

            # if uid is None then the user does not exist. So we return False as 'not authenticated'
            if uid is None:
                logger.info("authenticate: local user not found identity=%s", payload.identity)
                return AuthResultEnum.USER_NOT_FOUND
            # get b\password in string
            password_body: str = await publish_ticket(
                    TicketType(
                        type= User.GetUserPassLocal,
                        payload=uid
                    )
                )

            # convert to bytes
            stored_pass = password_body.encode('utf-8')
            # check and get a predicate
            is_authenticate = compare_password(payload.password.get_secret_value(), stored_pass)

            logger.debug("authenticate: local authentication result=%s for uid=%s", is_authenticate, uid)
            # return the predicate
            return AuthResultEnum.SUCCESS if is_authenticate else AuthResultEnum.NOT_AUTHENTIC

    async def update_user(self) -> None:
        pass

    
    async def get_email_by_uname(self, uname: UserName):
        logger.debug("get_email_by_uname called uname=%s", uname)
        uid = await get_id(IdentityPayload(uname=uname))
        if uid is None:
            logger.error("get_email_by_uname: User does not exist uname=%s", uname)
            raise UserNotFoundException("User does not exist")
        mail: Mail = await publish_ticket(
            TicketType(
            type=User.GetMail,
            payload=uid)
        )
        logger.debug("get_email_by_uname returned mail=%s for uid=%s", mail, uid)
        return mail
