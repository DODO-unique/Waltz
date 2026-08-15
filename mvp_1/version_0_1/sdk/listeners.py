from collections.abc import Awaitable, Callable
from typing import TypeVar, get_args

from version_0_1.core.enums import OperationIntentions
from version_0_1.exceptions.waltz_exceptions import (
    DuplicateRegistrationException,
    MissingConfigurationException,
    UnsupportedProviderException,
)
from version_0_1.logging.logger import get_logger

logger = get_logger("sdk.listeners")

logger.debug("sdk.listeners module loaded")
from version_0_1.validators.core_validator import (
    AnyHttpUrl,
    CadencePayload,
    DatabaseRegistry,
    OAuthCredentials,
    ProviderName,
    Registry,
)

P = TypeVar("P")
R = TypeVar("R")

class Listeners:

    def __init__(self, base_uri: str | None = None) -> None:
        # TODO: I think we can refactor this dictonary idea into organized pydantic classes
        self.registry: Registry

        # NOTE: URI only for OAuth
        self.REDIRECT_URI = None if base_uri is None else base_uri.rstrip("/") + "/auth/oauth/authResponse"
    
    def decorator(self, spec: OperationIntentions[P, R]) -> Callable[[Callable[[P], Awaitable[R]]],Callable[[P], Awaitable[R]],]:
        
        def actual_decorator(user_func: Callable[[P], Awaitable[R]]):

            async def wrapper(payload: P):
                logger.debug("Listener wrapper called for spec=%s payload=%s", spec, payload)
                return await user_func(payload)

            package = DatabaseRegistry(
                operation=spec,
                operator=wrapper,
            )
            self.registry.database.add(package)
            logger.debug("Registered database package for operation=%s", spec)
            return wrapper

        return actual_decorator

    def cadence_decorator(self, user_func: Callable[[CadencePayload] , None]):
        '''
        This decorator registers a email service. 
        '''
        # This runs at registration.
        if self.registry.cadence is not None:
            logger.error("Attempted to register a second cadence/email service")
            raise DuplicateRegistrationException("Two email services aren't allowed")
        
        # wrapper is the function user calls.
        def wrapper(payload: CadencePayload) -> None:
            logger.debug("Cadence wrapper called with payload=%s", payload)
            # I kept only one function here because the user function should do exactly what you expect it to do when wrapper() runs.
            user_func(payload)
            # we are the ones calling wrapper() so the user function runs with our payload

        # store the wrapper so we can call them later. 
        self.registry.cadence = wrapper
        logger.debug("Registered cadence/email service")
        return wrapper

    def serenity(self, provider_name: ProviderName, creds: OAuthCredentials):
        logger.debug("Registering serenity provider=%s", provider_name)
        if self.REDIRECT_URI is None:
            logger.error("Redirect URI not set when registering serenity provider=%s", provider_name)
            raise MissingConfigurationException("Provide a redirect URI")
        if provider_name not in get_args(ProviderName):
            logger.error("Invalid provider name=%s", provider_name)
            raise UnsupportedProviderException("No such provider name")
        package = creds.with_provider_defaults(provider_name, AnyHttpUrl(self.REDIRECT_URI))

        self.registry.serenity.add(package)
        logger.debug("Registered serenity provider=%s", provider_name)
