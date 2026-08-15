from collections.abc import Awaitable, Callable
from typing import TypeVar, get_args

from client_schemas import OAuthCredentials, Registry
from master_validator import CadencePayload, DatabaseRegistry
from ticket_enum import OperationIntentions
from validation_helper import ProviderName

P = TypeVar("P")
R = TypeVar("R")

class Listeners:

    def __init__(self, base_uri: str | None = None) -> None:
        # TODO: I think we can refactor this dictonary idea into organized pydantic classes
        self.registry: Registry

        # NOTE: URI only for OAuth
        self.REDIRECT_URI = None if base_uri is None else base_uri.rstrip("/") + "/auth/oauth/initiate"
    
    def decorator(self, spec: OperationIntentions[P, R]) -> Callable[[Callable[[P], Awaitable[R]]],Callable[[P], Awaitable[R]],]:
        
        def actual_decorator(user_func: Callable[[P], Awaitable[R]]):

            async def wrapper(payload: P):
                return await user_func(payload)

            package = DatabaseRegistry(
                operation=spec,
                operator=wrapper,
            )
            self.registry.database.add(package)
            return wrapper

        return actual_decorator

    def cadence_decorator(self, user_func: Callable[[CadencePayload] , None]):
        '''
        This decorator registers a email service. 
        '''
        # This runs at registration.
        if self.registry.cadence is not None:
            raise ValueError("Two email services aren't allowed")
        
        # wrapper is the function user calls.
        def wrapper(payload: CadencePayload) -> None:
            # I kept only one function here because the user function should do exactly what you expect it to do when wrapper() runs.
            user_func(payload)
            # we are the ones calling wrapper() so the user function runs with our payload

        # store the wrapper so we can call them later. 
        self.registry.cadence = wrapper
        
        return wrapper

    def serenity(self, provider_name: ProviderName, creds: OAuthCredentials):
        if self.REDIRECT_URI is None:
            raise ValueError("Provide a redirect URI")
        if provider_name not in get_args(ProviderName):
            raise ValueError("No such provider name")
        package = creds.with_provider_defaults(provider_name, self.REDIRECT_URI)

        self.registry.serenity.add(package)