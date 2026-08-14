from enums import User

from ..sdk.ticket_handler import TicketBus
from ..validators.core_validator import CadenceTicket, IdentityPayload, TicketType, Uid
from version_0.logging.logger import get_logger
logger = get_logger("core.general")

logger.debug("core.general module loaded")

bus = TicketBus()
async def publish_ticket(ticket: TicketType):
    logger.debug("publish_ticket called ticket=%s", ticket)
    return await bus.publish(ticket)

async def dispatch_ticket(ticket: CadenceTicket):
    logger.debug("dispatch_ticket called ticket=%s", ticket)
    return await bus.dispatch(ticket)

async def get_id(identity: IdentityPayload) -> Uid | None:
    '''
    use identity to get_id
    '''
    logger.debug("get_id called identity=%s", identity)
    return await publish_ticket(
        TicketType(
        type=User.GetID,
        payload=identity)
    )
