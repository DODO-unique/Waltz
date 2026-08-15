from enums import User

from ..sdk.ticket_handler import TicketBus
from ..validators.core_validator import CadenceTicket, IdentityPayload, TicketType, Uid

bus = TicketBus()
async def publish_ticket(ticket: TicketType):
    return await bus.publish(ticket)

async def dispatch_ticket(ticket: CadenceTicket):
    return await bus.dispatch(ticket)

async def get_id(identity: IdentityPayload) -> Uid | None:
    '''
    use identity to get_id
    '''
    return await publish_ticket(
        TicketType(
        type=User.GetID,
        payload=identity)
    )
