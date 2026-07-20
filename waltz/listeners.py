from ticket_enum import TicketEnum 
from collections.abc import Callable
from master_validator import TicketType

class Listeners:

    def __init__(self) -> None:
        self.registry: dict[TicketEnum, Callable[..., dict[str, str]]] = {}

    async def __call__(self, ticket: TicketType):
        if ticket.type in self.registry:
            result = self.registry[ticket.type](ticket.payload)
            return result
        else:
            raise ValueError("Relevant ticket not registered")
    
    def decorator(self, record_enum: TicketEnum):
        def actual_decorator(user_func: Callable[..., dict[str, str]]) -> Callable[[None], dict[str, str]]:
            def wrapper(payload: None) -> dict[str, str]:
                x: dict[str, str] = user_func(payload)
                return x
            if record_enum not in self.registry:
                self.registry[record_enum] = wrapper
            return wrapper
        return actual_decorator
    