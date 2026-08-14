from random import randint

from version_0.logging.logger import get_logger
logger = get_logger("core.cadence")

logger.debug("core.cadence module loaded")
from uuid import uuid4

from enums import OneTimePassword
from security.hashing import sha_hash

from ..core.general import dispatch_ticket, get_id, publish_ticket
from ..validators.core_validator import (
    CadencePayload,
    CadenceTicket,
    IdentityPayload,
    Mail,
    TicketType,
)


class Cadence:
    '''
    Verifier said it needed a name 
    Cadence: A OTP service

    Anyway, so what does a Verifier need:

    1. Get a email
    2. Generate the OTP.
    3. Hash it
    4. Store the OTP in persistence
    5. Send OTP to the given mail/phone-number/etc
    6. wait for user-entered OTP
    7. Compare hashes.
    '''

    def __init__(self, email: Mail):
        self.email = email


    async def issue(self):
        '''
        Provider is the service provider

        1. Receive email.
        2. Generate OTP.
        3. Hash OTP.
        4. Store hash + expiry + metadata.
        5. Send plaintext OTP to the email.
        6. Return "OTP issued."

        Just like tokens, otp also has an expiry and if now is greater than expiry you kill the token.
        THis is a persistence decision.
        ''' 
        logger.debug("Cadence.issue called for email=%s", self.email)
        code = randint(1000, 9999)
        digest = sha_hash(str(code))

        # pass the digest to be stored in the DB
        await publish_ticket(
            TicketType(id=uuid4(),
            type=OneTimePassword.Store,
            payload= digest
            )
        )

        await dispatch_ticket(
            CadenceTicket(
                payload=CadencePayload(
                    email=self.email,
                    code=str(code)
                )
                )
            ) 
        logger.info("Cadence.issue dispatched OTP to email=%s", self.email)


    async def validate(self, code: str) -> bool:
        '''
        1. Fetch stored OTP record.
        2. Check expiry.
        3. Hash submitted OTP.
        4. Compare hashes.
        5. If valid:
            - mark OTP as used
            - continue workflow
        6. Return success/failure.
        '''

        logger.debug("Cadence.validate called email=%s code=%s", self.email, code)
        uid = await get_id(IdentityPayload(email=self.email))
        if uid is None:
            logger.error("Cadence.validate: No user found for email=%s", self.email)
            raise ValueError("No user found")
        result: str | None = await publish_ticket(
            TicketType(
                type=OneTimePassword.Get,
                payload=uid
            )
        )

        given_otp_digest = sha_hash(code)

        if given_otp_digest == result:
            # it is correct, send a correct flag back and delete the otp
            await publish_ticket(
                TicketType(
                    type=OneTimePassword.DeleteOTP,
                    payload=uid
                )
            )

            logger.info("Cadence.validate succeeded for email=%s uid=%s", self.email, uid)
            return True

        else:
            logger.info("Cadence.validate failed for email=%s uid=%s", self.email, uid)
            return False            
