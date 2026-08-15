from uuid import UUID, uuid4

from version_0_1.exceptions.waltz_exceptions import (
    InvalidInternalStateException,
    SessionTokenNotFoundException,
    UserNotFoundException,
)
from version_0_1.log.logger import get_logger

logger = get_logger("core.session_manager")

logger.debug("core.session_manager module loaded")

from version_0_1.core.enums import Session
from version_0_1.core.general import get_id, publish_ticket
from version_0_1.validators.core_validator import (
    IdentityPayload,
    SessionRequest,
    TicketType,
    Uid,
)

# NOTE: MAJOR - I made them independent functions instead of a session class whcih was unnecessary
'''
All session ops live here. They include:
1. Session start (passes a session token to dev and returns it to user)
2. Session destroy (sends a session token to dev so they can destory it)
3. session validate (we would need this as a DI on the dev endpoint itself)
4. Session destroy all (user must not be unique in the sessions table. A user can have multiple session from different addresses)
5. Session cleanup (optional. Remove all expired sessions)
'''

async def _get_token(uid: Uid) -> UUID | None:
    logger.debug("_get_token called for uid=%s", uid)
    token = await publish_ticket(
        TicketType(
            type = Session.GetToken,
            payload = SessionRequest(
                Uid=uid
            )
        )
    )

    logger.debug("_get_token returned token=%s for uid=%s", token, uid)
    return token

async def start(identity: IdentityPayload | None = None, uid: Uid | None = None) -> UUID:
    logger.debug("start called with identity=%s uid=%s", identity, uid)
    if uid is None and identity is not None:
        uid = await get_id(identity)
        if uid is None:
            logger.error("start failed: No user found for identity=%s", identity)
            raise UserNotFoundException("No user found")
    token = await publish_ticket(
        TicketType(
            type=Session.Create,
            payload=SessionRequest(
                Uid=uid
            )
        )
    )

    logger.info("Session started uid=%s token=%s", uid, token)
    return token



async def destroy(token: UUID):
    logger.debug("destroy called for token=%s", token)
    await publish_ticket(
        TicketType(
            id=uuid4(),
            type=Session.Delete,
            payload=SessionRequest(token=token)
        )
    )
    logger.info("Destroyed session token=%s", token)

async def check_token(token: UUID) -> bool:
    logger.debug("check_token called for token=%s", token)
    # FIXME: I am not so sure about this method. Do you need this? If you do, then at least check the expiry here? Doesn't get_token already verify if token exists?
    predicate = await publish_ticket(
        TicketType(
            id=uuid4(),
            type=Session.Check,
            payload=SessionRequest(token=token)
        )
    )

    logger.debug("check_token result=%s for token=%s", predicate, token)
    return predicate

async def validate(identity: IdentityPayload | None = None, uid: Uid | None = None):
    logger.debug("validate called identity=%s uid=%s", identity, uid)
    if uid is None:
        if identity is not None:
            uid = await get_id(identity)
            if uid is None:
                logger.error("validate failed: No user found for identity=%s", identity)
                raise UserNotFoundException("No user found")
        else:
            logger.error("validate called with neither identity nor uid")
            raise InvalidInternalStateException("INTERNAL: Both identity and uid cannot be none")
    token = await _get_token(uid)
    if token is None:
        logger.error("validate failed: No session token found for uid=%s", uid)
        raise SessionTokenNotFoundException("No session token found")

    result = await check_token(token)
    logger.debug("validate result=%s for uid=%s", result, uid)
    return result
    

async def destroy_all(identiy: IdentityPayload):
    logger.debug("destroy_all called for identity=%s", identiy)
    uid = await get_id(identity=identiy)
    if uid is None:
        logger.error("destroy_all: No user found for identity=%s", identiy)
        raise UserNotFoundException("No user Found")

    await publish_ticket(
        TicketType(
            type= Session.DeleteAll,
            payload=SessionRequest(Uid=uid)
        )
    )
    logger.info("destroy_all completed for uid=%s", uid)
