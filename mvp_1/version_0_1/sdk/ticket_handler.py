from collections.abc import Callable
from typing import Any, TypeAlias

from version_0_1.exceptions.waltz_exceptions import (
    CredentialsNotFoundException,
    DuplicateRegistrationException,
    ServiceNotRegisteredException,
)
from version_0_1.log.logger import get_logger

from .listeners import Listeners

logger = get_logger("sdk.ticket_handler")

logger.debug("sdk.ticket_handler module loaded")

from version_0_1.validators.core_validator import (
    CadenceTicket,
    Credentials,
    CredentialsTicket,
    GrandRegistry,
    TicketType,
)

Listener: TypeAlias = Callable[[TicketType], Any]

class TicketBus:
    def __init__(self):
        '''
        A listener would take the following attributes:
        1. id - UUID of the ticket
        2. type - enum type of the ticket
        3. payload - data a ticket needs to pass

        return type for listener is dict[str, str], so basically a payload
        '''
        self.grand_registry: GrandRegistry = GrandRegistry() 
        logger.debug("TicketBus initialized")
    
    def subscribe(self, *listeners: Listeners):
        '''
        # NOTE: This method is user triggered.

        This must run after all listeners and their functions are established, otherwise the Bus might miss them :(
        '''
        # user passes listener instances which we take in a tuple.
        # we iterate through it once:
        for listener in listeners:
            logger.debug("Subscribing listener=%s", listener)

            # A: DATABASE FIRST
            for database_registry in listener.registry.database:
                if database_registry.operation in self.grand_registry.registered_database_operation:
                    raise DuplicateRegistrationException(f"{database_registry.operation} is already registered")

                # we have to register this database entry at two places: one, the grand registry, two, the registered_database_operations
                self.grand_registry.database.add(database_registry)
                self.grand_registry.registered_database_operation.add(database_registry.operation)

            # A: Cadence Second
            if self.grand_registry.cadence is None:
                # add the email service here
                self.grand_registry.cadence = listener.registry.cadence
            elif self.grand_registry.cadence is not None and listener.registry.cadence is not None:
                raise DuplicateRegistrationException("A email service is already registered")

            # A: Serenity Third
            for creds in listener.registry.serenity:
                if creds.provider in self.grand_registry.registered_serenity_providers:
                    raise DuplicateRegistrationException("Provider already registered")

                self.grand_registry.registered_serenity_providers.add(creds.provider)
                self.grand_registry.serenity.add(creds)

    
    async def publish(self, ticket: TicketType):
        '''
        Publish a new database ticket.
        '''
        logger.debug("publish called with ticket=%s", ticket)
        registered_operations = {x.operation : x.operator for x in self.grand_registry.database}
        for operation, operator in registered_operations.items():
            if ticket.type == operation:
                logger.debug("Dispatching to operation=%s", operation)
                result = await operator(ticket.payload)
                logger.debug("Operation %s returned result=%s", operation, result)
                return result
        logger.error("Unregistered operation for ticket=%s", ticket)
        raise ServiceNotRegisteredException(f"Unregistered/Unsubscribed operation.\n There is no operation set for {ticket.type}")

    async def dispatch(self, ticket: CadenceTicket):
        '''
        Dispatch a mail
        '''
        logger.debug("dispatch called for ticket=%s", ticket)
        if self.grand_registry.cadence is not None:
            logger.debug("Calling cadence service for ticket=%s", ticket)
            self.grand_registry.cadence(ticket.payload)
            return
        logger.error("No cadence/email service registered")
        raise ServiceNotRegisteredException("No email service registered")

    def credentials(self, ticket: CredentialsTicket) -> Credentials:
        logger.debug("credentials lookup for provider=%s", ticket.provider)
        for cred in self.grand_registry.serenity:
            if cred.provider == ticket.provider:
                logger.debug("Found credentials for provider=%s", ticket.provider)
                return cred
        logger.error("No credentials found for provider=%s", ticket.provider)
        raise CredentialsNotFoundException(f"No provider set for {ticket.provider}")