from master_validator import TicketType, Payload, TicketEnum
from collections.abc import Callable
from typing import TypeAlias
from listeners import Listeners

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
        self._registered_ops: dict[TicketEnum, Listeners]
    
    def subscribe(self, listener: Listeners):
        # user gives us a listener
        for ops in listener.registry:
            if ops not in self._registered_ops:
                self._registered_ops[ops] = listener
            else:
                raise ValueError(f'''Duplicate entry: {ops}.\nCould not register the listner in bus. \nDoes the listner instance share operations with other listners?''')
    
    async def raise_ticket(self, ticket: TicketType):
        # waltz passes a ticket and we wake all listeners
        for ops, listener in self._registered_ops.items():
            if ticket.type == ops:
                result = await listener(ticket)
                return result
        raise ValueError(f"Unregistered/Unsubscribed operation.\n There is no operation setup for {ticket.type}")