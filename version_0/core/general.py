import bcrypt
from enums import User

from ..sdk.ticket_handler import TicketBus
from ..validators.core_validator import CadenceTicket, IdentityPayload, TicketType, Uid

bus = TicketBus()
async def publish_ticket(ticket: TicketType):
    return await bus.publish(ticket)

async def dispatch_ticket(ticket: CadenceTicket):
    return await bus.dispatch(ticket)

def hash_password(plain_text_password: str) -> bytes:
    # first we convert string to bytes
    password_bytes = plain_text_password.encode('utf-8')

    # generate salt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password

def compare_password(pt_pass: str, hpass: bytes) -> bool:
    password_bytes = pt_pass.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hpass)

async def get_id(identity: IdentityPayload) -> Uid | None:
    '''
    use identity to get_id
    '''
    return await publish_ticket(
        TicketType(
        type=User.GetID,
        payload=identity)
    )
