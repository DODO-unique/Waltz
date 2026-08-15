from collections.abc import Callable
from typing import TypeAlias

from client_schemas import Credentials
from concrete.listeners import Listeners
from master_validator import (
    CadenceTicket,
    CredentialsTicket,
    GrandRegistry,
    Payload,
    TicketType,
)

Listener: TypeAlias = Callable[[TicketType], Payload]

class TicketBus:
    def __init__(self):
        '''
        A listener would take the following attributes:
        1. id - UUID of the ticket
        2. type - enum type of the ticket
        3. payload - data a ticket needs to pass

        return type for listener is dict[str, str], so basically a payload
        '''
        self.grand_registry: GrandRegistry
    
    def subscribe(self, *listeners: Listeners):
        '''
        # NOTE: This method is user triggered.

        This must run after all listeners and their functions are established, otherwise the Bus might miss them :(
        '''
        # user passes listener instances which we take in a tuple.
        # we iterate through it once:
        for listener in listeners:

            # A: DATABASE FIRST
            for database_registry in listener.registry.database:
                if database_registry.operation in self.grand_registry.registered_database_operations:
                    raise ValueError(f"{database_registry.operation} is already registered")

                # we have to register this database entry at two places: one, the grand registry, two, the registered_database_operations
                self.grand_registry.database.add(database_registry)

            # A: Cadence Second
            if self.grand_registry.cadence is None:
                # add the email service here
                self.grand_registry.cadence = listener.registry.cadence
            elif self.grand_registry.cadence is not None and listener.registry.cadence is not None:
                raise ValueError("A email service is already registered")

            # A: Serenity Third
            for creds in listener.registry.serenity:
                if creds.provider in self.grand_registry.registered_serenity_providers:
                    raise ValueError("Provider already registered")

                self.grand_registry.serenity.add(creds)

    
    async def publish(self, ticket: TicketType):
        '''
        Publish a new database ticket.
        '''
        registered_operations = {x.operation : x.operator for x in self.grand_registry.database}
        for ops, operator in registered_operations.items():
            if ticket.type == ops:
                result = await operator(ticket.payload)
                return result
        raise ValueError(f"Unregistered/Unsubscribed operation.\n There is no operation set for {ticket.type}")

    async def dispatch(self, ticket: CadenceTicket):
        '''
        Dispatch a mail
        '''
        if self.grand_registry.cadence is not None:
            self.grand_registry.cadence(ticket.payload)
        raise ValueError("No email service registered")

    def credentials(self, ticket: CredentialsTicket) -> Credentials:

        for cred in self.grand_registry.serenity:
            if cred.provider == ticket.provider:
                return cred
        raise ValueError(f"No provider set for {ticket.provider}")