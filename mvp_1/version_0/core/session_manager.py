from uuid import UUID, uuid4

from enums import Session
from general import get_id, publish_ticket

from ..validators.core_validator import IdentityPayload, SessionRequest, TicketType, Uid

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
    token = await publish_ticket(
        TicketType(
            type = Session.GetToken,
            payload = SessionRequest(
                Uid=uid
            )
        )
    )

    return token

async def start(identity: IdentityPayload | None = None, uid: Uid | None = None) -> UUID:
    if uid is None and identity is not None:
        uid = await get_id(identity)
        if uid is None:
            raise ValueError("No user found")
    token = await publish_ticket(
        TicketType(
            type=Session.Create,
            payload=SessionRequest(
                Uid=uid
            )
        )
    )

    return token



async def destroy(token: UUID):
    await publish_ticket(
        TicketType(
            id=uuid4(),
            type=Session.Delete,
            payload=SessionRequest(token=token)
        )
    )

async def check_token(token: UUID) -> bool:
    # FIXME: I am not so sure about this method. Do you need this? If you do, then at least check the expiry here? Doesn't get_token already verify if token exists?
    predicate = await publish_ticket(
        TicketType(
            id=uuid4(),
            type=Session.Check,
            payload=SessionRequest(token=token)
        )
    )

    return predicate

async def validate(identity: IdentityPayload | None = None, uid: Uid | None = None):
    if uid is None:
        if identity is not None:
            uid = await get_id(identity)
            if uid is None:
                raise ValueError("No user found")
        else:
            raise ValueError("INTERNAL: Both identity and uid cannot be none")
    token = await _get_token(uid)
    if token is None:
        raise ValueError("No session token found")

    return await check_token(token)
    

async def destroy_all(identiy: IdentityPayload):
    uid = await get_id(identity=identiy)

    await publish_ticket(
        TicketType(
            type= Session.Delete,
            payload=SessionRequest(Uid=uid)
        )
    )
